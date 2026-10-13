"""Fail-closed Systems Foundry bridge prototype.

Planning only: this module never invokes registered capabilities.
A mission may contain multiple prompt-specific jobs. Independent jobs are
placed in the same parallel batch; dependency-linked jobs are ordered.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Protocol


RISK_ORDER = {"low": 0, "moderate": 1, "high": 2, "critical": 3}


class BridgeHalt(RuntimeError):
    """Raised when safe planning cannot be established."""


@dataclass(frozen=True)
class Capability:
    capability_id: str
    system_id: str
    description: str
    tags: tuple[str, ...]
    risk: str
    adapter: str
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.capability_id or not self.system_id or not self.adapter:
            raise ValueError("capability_id, system_id, and adapter are required")
        if self.risk not in RISK_ORDER:
            raise ValueError(f"unknown risk level: {self.risk}")
        if not self.tags:
            raise ValueError("at least one capability tag is required")


@dataclass(frozen=True)
class Mission:
    mission_id: str
    objective: str
    required_tags: tuple[str, ...]
    max_risk: str
    human_authorization_ref: str

    def __post_init__(self) -> None:
        if not self.mission_id or not self.objective.strip():
            raise ValueError("mission_id and objective are required")
        if not self.required_tags:
            raise ValueError("at least one required tag is needed for bounded selection")
        if self.max_risk not in RISK_ORDER:
            raise ValueError(f"unknown maximum risk: {self.max_risk}")


@dataclass(frozen=True)
class JobSpec:
    """One explicitly prompt-scoped unit of work within a larger mission."""

    job_id: str
    prompt: str
    required_tags: tuple[str, ...]
    max_risk: str
    acceptance_criteria: tuple[str, ...]
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.job_id or not self.prompt.strip():
            raise ValueError("job_id and prompt-specific instructions are required")
        if not self.required_tags:
            raise ValueError(f"job {self.job_id} requires explicit capability tags")
        if self.max_risk not in RISK_ORDER:
            raise ValueError(f"unknown maximum risk for job {self.job_id}: {self.max_risk}")
        if not self.acceptance_criteria or any(not x.strip() for x in self.acceptance_criteria):
            raise ValueError(f"job {self.job_id} requires explicit acceptance criteria")
        if self.job_id in self.depends_on:
            raise ValueError(f"job {self.job_id} cannot depend on itself")


@dataclass(frozen=True)
class Plan:
    mission_id: str
    capability_ids: tuple[str, ...]
    system_ids: tuple[str, ...]
    policy_version: str
    status: str = "PROPOSED_NOT_EXECUTABLE"

    def canonical(self) -> str:
        return json.dumps(
            {
                "mission_id": self.mission_id,
                "capability_ids": list(self.capability_ids),
                "system_ids": list(self.system_ids),
                "policy_version": self.policy_version,
                "status": self.status,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @property
    def digest(self) -> str:
        return sha256(self.canonical().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class JobPlan:
    job_id: str
    prompt: str
    acceptance_criteria: tuple[str, ...]
    plan: Plan


@dataclass(frozen=True)
class MissionPlan:
    mission_id: str
    objective: str
    jobs: tuple[JobPlan, ...]
    parallel_batches: tuple[tuple[str, ...], ...]
    status: str = "PROPOSED_NOT_EXECUTABLE"

    def canonical(self) -> str:
        payload = {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "jobs": [
                {
                    "job_id": j.job_id,
                    "prompt": j.prompt,
                    "acceptance_criteria": list(j.acceptance_criteria),
                    "plan_digest": j.plan.digest,
                }
                for j in self.jobs
            ],
            "parallel_batches": [list(batch) for batch in self.parallel_batches],
            "status": self.status,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @property
    def digest(self) -> str:
        return sha256(self.canonical().encode("utf-8")).hexdigest()


class AuthorityVerifier(Protocol):
    """Must consult an external, trusted authority system; never trust a caller flag."""

    def verify(self, mission: Mission) -> bool: ...


class DenyByDefaultAuthorityVerifier:
    """Safe default until a real external verifier is supplied."""

    def verify(self, mission: Mission) -> bool:
        return False


class ControllerA:
    """Requirement-fit controller: chooses enabled capabilities matching all required tags."""

    version = "fit-controller-v1"

    def propose(self, mission: Mission, registry: Iterable[Capability]) -> Plan:
        candidates = []
        required = set(mission.required_tags)
        for cap in registry:
            if cap.enabled and required.issubset(set(cap.tags)):
                candidates.append(cap)
        candidates.sort(key=lambda c: (c.system_id, c.capability_id))
        return Plan(
            mission_id=mission.mission_id,
            capability_ids=tuple(c.capability_id for c in candidates),
            system_ids=tuple(sorted({c.system_id for c in candidates})),
            policy_version=self.version,
        )


class ControllerB:
    """Risk gate: chooses only enabled, risk-bounded matching capabilities."""

    version = "risk-controller-v1"

    def propose(self, mission: Mission, registry: Iterable[Capability]) -> Plan:
        candidates = []
        required = set(mission.required_tags)
        risk_limit = RISK_ORDER[mission.max_risk]
        for cap in registry:
            tags_match = required.issubset(set(cap.tags))
            risk_permitted = RISK_ORDER[cap.risk] <= risk_limit
            if cap.enabled and tags_match and risk_permitted:
                candidates.append(cap)
        candidates.sort(key=lambda c: (c.system_id, c.capability_id))
        return Plan(
            mission_id=mission.mission_id,
            capability_ids=tuple(c.capability_id for c in candidates),
            system_ids=tuple(sorted({c.system_id for c in candidates})),
            policy_version=ControllerA.version,
        )


class DualControlPlane:
    """Parallel plan controllers; disagreement or uncertainty halts, never auto-overrides."""

    def __init__(
        self,
        authority_verifier: AuthorityVerifier | None = None,
        controller_a: ControllerA | None = None,
        controller_b: ControllerB | None = None,
    ) -> None:
        self.authority_verifier = authority_verifier or DenyByDefaultAuthorityVerifier()
        self.controller_a = controller_a or ControllerA()
        self.controller_b = controller_b or ControllerB()

    def _verify_authority(self, mission: Mission) -> None:
        if not mission.human_authorization_ref.strip():
            raise BridgeHalt("HALT: missing external human-authorization reference")
        try:
            authorized = self.authority_verifier.verify(mission)
        except Exception as exc:
            raise BridgeHalt("HALT: authority verification failed") from exc
        if not authorized:
            raise BridgeHalt("HALT: external human authorization not verified")

    def plan(self, mission: Mission, registry: Iterable[Capability]) -> Plan:
        snapshot = tuple(registry)
        self._verify_authority(mission)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                a_future = pool.submit(self.controller_a.propose, mission, snapshot)
                b_future = pool.submit(self.controller_b.propose, mission, snapshot)
                plan_a = a_future.result()
                plan_b = b_future.result()
        except Exception as exc:
            raise BridgeHalt("HALT: one or more controllers failed") from exc

        selection_a = (plan_a.capability_ids, plan_a.system_ids)
        selection_b = (plan_b.capability_ids, plan_b.system_ids)
        if selection_a != selection_b:
            raise BridgeHalt("HALT: parallel controllers disagree; human review required")
        if not plan_a.capability_ids:
            raise BridgeHalt("HALT: no eligible capability found")
        if plan_a.mission_id != mission.mission_id or plan_b.mission_id != mission.mission_id:
            raise BridgeHalt("HALT: controller mission binding mismatch")

        return Plan(
            mission_id=mission.mission_id,
            capability_ids=plan_a.capability_ids,
            system_ids=plan_a.system_ids,
            policy_version=f"{plan_a.policy_version}+{self.controller_b.version}",
        )

    def plan_mission(
        self,
        mission: Mission,
        jobs: Iterable[JobSpec],
        registry: Iterable[Capability],
    ) -> MissionPlan:
        """Build a prompt-specific multi-job plan and dependency-safe parallel batches.

        This plans concurrency only; it does not execute jobs. Jobs in one batch
        have no declared dependency on each other. Every job receives its own
        capability/risk selection and must pass both controllers.
        """
        job_list = tuple(jobs)
        if not job_list:
            raise BridgeHalt("HALT: mission must contain at least one explicit job")
        by_id = {job.job_id: job for job in job_list}
        if len(by_id) != len(job_list):
            raise BridgeHalt("HALT: duplicate job IDs")
        for job in job_list:
            unknown = set(job.depends_on) - set(by_id)
            if unknown:
                raise BridgeHalt(
                    f"HALT: job {job.job_id} has unknown dependencies: {sorted(unknown)}"
                )

        # Topological batches: each batch can be scheduled concurrently.
        remaining = dict(by_id)
        completed: set[str] = set()
        batches: list[tuple[str, ...]] = []
        while remaining:
            ready = tuple(sorted(
                job_id for job_id, job in remaining.items()
                if set(job.depends_on).issubset(completed)
            ))
            if not ready:
                raise BridgeHalt("HALT: job dependency cycle detected")
            batches.append(ready)
            completed.update(ready)
            for job_id in ready:
                del remaining[job_id]

        snapshot = tuple(registry)
        # First establish authorization for the parent mission.
        self._verify_authority(mission)

        def plan_one(job: JobSpec) -> JobPlan:
            scoped = Mission(
                mission_id=f"{mission.mission_id}/{job.job_id}",
                objective=job.prompt,
                required_tags=job.required_tags,
                max_risk=job.max_risk,
                human_authorization_ref=mission.human_authorization_ref,
            )
            plan = self.plan(scoped, snapshot)
            return JobPlan(
                job_id=job.job_id,
                prompt=job.prompt,
                acceptance_criteria=job.acceptance_criteria,
                plan=plan,
            )

        job_plans: dict[str, JobPlan] = {}
        # Jobs are planned in dependency batches; peers are processed concurrently.
        for batch in batches:
            with ThreadPoolExecutor(max_workers=max(1, len(batch))) as pool:
                futures = {job_id: pool.submit(plan_one, by_id[job_id]) for job_id in batch}
                for job_id in batch:
                    try:
                        job_plans[job_id] = futures[job_id].result()
                    except Exception as exc:
                        for future in futures.values():
                            future.cancel()
                        if isinstance(exc, BridgeHalt):
                            raise
                        raise BridgeHalt(f"HALT: planning failed for job {job_id}") from exc

        ordered_plans = tuple(job_plans[job.job_id] for job in job_list)
        return MissionPlan(
            mission_id=mission.mission_id,
            objective=mission.objective,
            jobs=ordered_plans,
            parallel_batches=tuple(batches),
        )
