import unittest

from bridge_core import (
    BridgeHalt,
    Capability,
    DenyByDefaultAuthorityVerifier,
    DualControlPlane,
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


if __name__ == "__main__":
    unittest.main()
