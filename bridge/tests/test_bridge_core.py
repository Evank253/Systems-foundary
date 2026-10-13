import unittest

from bridge.bridge_core import (
    BridgeHalt,
    Capability,
    DenyByDefaultAuthorityVerifier,
    DualControlPlane,
    JobSpec,
    Mission,
)


class AllowTestAuthority:
    """Test double only; not suitable for production."""

    def verify(self, mission):
        return mission.human_authorization_ref == "test-authorized-record"


def capability(cid="cap-api", system="system-api", tags=("api",), risk="low", enabled=True):
    return Capability(
        capability_id=cid,
        system_id=system,
        description="test capability",
        tags=tuple(tags),
        risk=risk,
        adapter="not-connected",
        enabled=enabled,
    )


def mission(tags=("api",), max_risk="moderate", auth="test-authorized-record"):
    return Mission(
        mission_id="mission-test",
        objective="test bounded capability selection",
        required_tags=tuple(tags),
        max_risk=max_risk,
        human_authorization_ref=auth,
    )


def job(job_id, tags=("api",), risk="moderate", depends_on=(), prompt=None):
    return JobSpec(
        job_id=job_id,
        prompt=prompt or f"Perform the specifically scoped work for {job_id}. Do not perform unrelated work.",
        required_tags=tuple(tags),
        max_risk=risk,
        acceptance_criteria=(f"Verify the defined output for {job_id}",),
        depends_on=tuple(depends_on),
    )


class BridgeCoreTests(unittest.TestCase):
    def setUp(self):
        self.bridge = DualControlPlane(authority_verifier=AllowTestAuthority())

    def test_selects_matching_authorized_capability_as_plan_only(self):
        plan = self.bridge.plan(mission(), [capability()])
        self.assertEqual(plan.capability_ids, ("cap-api",))
        self.assertEqual(plan.status, "PROPOSED_NOT_EXECUTABLE")
        self.assertEqual(len(plan.digest), 64)

    def test_default_authority_verifier_denies(self):
        bridge = DualControlPlane(authority_verifier=DenyByDefaultAuthorityVerifier())
        with self.assertRaisesRegex(BridgeHalt, "not verified"):
            bridge.plan(mission(), [capability()])

    def test_risk_controller_disagreement_halts(self):
        with self.assertRaisesRegex(BridgeHalt, "disagree"):
            self.bridge.plan(mission(max_risk="low"), [capability(risk="critical")])

    def test_no_matching_capability_halts(self):
        with self.assertRaisesRegex(BridgeHalt, "no eligible"):
            self.bridge.plan(mission(tags=("database",)), [capability()])

    def test_disabled_capability_is_not_selected(self):
        with self.assertRaisesRegex(BridgeHalt, "no eligible"):
            self.bridge.plan(mission(), [capability(enabled=False)])

    def test_missing_authorization_reference_halts(self):
        with self.assertRaisesRegex(BridgeHalt, "missing external"):
            self.bridge.plan(mission(auth=""), [capability()])

    def test_plan_order_is_deterministic(self):
        plan = self.bridge.plan(
            mission(),
            [capability("z", "z-system"), capability("a", "a-system")],
        )
        self.assertEqual(plan.capability_ids, ("a", "z"))

    def test_independent_jobs_are_grouped_for_parallel_execution(self):
        result = self.bridge.plan_mission(
            mission(),
            [job("api"), job("docs")],
            [capability("cap-api", tags=("api",)), capability("cap-docs", tags=("docs",))],
        )
        self.assertEqual(result.parallel_batches, (("api", "docs"),))
        self.assertEqual([x.job_id for x in result.jobs], ["api", "docs"])
        self.assertEqual(result.status, "PROPOSED_NOT_EXECUTABLE")

    def test_dependent_jobs_are_separated_into_batches(self):
        result = self.bridge.plan_mission(
            mission(),
            [job("design"), job("build", depends_on=("design",))],
            [capability("cap-api", tags=("api",))],
        )
        self.assertEqual(result.parallel_batches, (("design",), ("build",)))

    def test_duplicate_job_ids_halt(self):
        with self.assertRaisesRegex(BridgeHalt, "duplicate job IDs"):
            self.bridge.plan_mission(mission(), [job("same"), job("same")], [capability()])

    def test_unknown_dependency_halts(self):
        with self.assertRaisesRegex(BridgeHalt, "unknown dependencies"):
            self.bridge.plan_mission(mission(), [job("build", depends_on=("missing",))], [capability()])

    def test_dependency_cycle_halts(self):
        with self.assertRaisesRegex(BridgeHalt, "dependency cycle"):
            self.bridge.plan_mission(
                mission(),
                [job("a", depends_on=("b",)), job("b", depends_on=("a",))],
                [capability()],
            )

    def test_job_prompt_and_acceptance_criteria_are_required(self):
        with self.assertRaisesRegex(ValueError, "prompt-specific"):
            JobSpec("bad", " ", ("api",), "low", ("output exists",))
        with self.assertRaisesRegex(ValueError, "acceptance criteria"):
            JobSpec("bad", "Do one bounded task", ("api",), "low", ())


if __name__ == "__main__":
    unittest.main()
