"""Fail-closed Systems Foundry bridge prototype.

Planning only: this module never invokes registered capabilities.
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
            if not cap.enabled:
                continue
            if required.issubset(set(cap.tags)):
                candidates.append(cap)
        candidates.sort(key=lambda c: (c.system_id, c.capability_id))
        return Plan(
            mission_id=mission.mission_id,
            capability_ids=tuple(c.capability_id for c in candidates),
            system_ids=tuple(sorted({c.system_id for c in candidates})),
            policy_version=self.version,
        )


class ControllerB:
    """Independent risk gate: selects only enabled, risk-bounded matching capabilities."""

    version = "risk-controller-v1"

    def propose(self, mission: Mission, registry: Iterable[Capability]) -> Plan:
        candidates = []
        required = set(mission.required_tags)
        risk_limit = RISK_ORDER[mission.max_risk]
        for cap in registry:
            tags_match = all(tag in cap.tags for tag in required)
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

    def plan(self, mission: Mission, registry: Iterable[Capability]) -> Plan:
        # Snapshot input so both controllers see the same immutable sequence.
        snapshot = tuple(registry)
        if not mission.human_authorization_ref.strip():
            raise BridgeHalt("HALT: missing external human-authorization reference")
        try:
            authorized = self.authority_verifier.verify(mission)
        except Exception as exc:
            raise BridgeHalt("HALT: authority verification failed") from exc
        if not authorized:
            raise BridgeHalt("HALT: external human authorization not verified")

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                a_future = pool.submit(self.controller_a.propose, mission, snapshot)
                b_future = pool.submit(self.controller_b.propose, mission, snapshot)
                plan_a = a_future.result()
                plan_b = b_future.result()
        except Exception as exc:
            raise BridgeHalt("HALT: one or more controllers failed") from exc

        # Compare capability/system selection, not controller labels.
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
