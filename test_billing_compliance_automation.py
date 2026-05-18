import unittest
from unittest.mock import MagicMock
from billing_compliance_automation import (
    BillingComplianceAutomationPlugin, PatientUpdated, EventResponse, CallExternalAPI, UpdatePatientLabels
)

class TestBillingComplianceAutomationPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = BillingComplianceAutomationPlugin()
        self.plugin.get_config = MagicMock(side_effect=lambda key: {
            "HOME_STATE": "NH",
            "BILLING_WEBHOOK_URL": "https://api.billing.internal/v1/alerts",
            "WEBHOOK_AUTH_TOKEN": "mock_secret"
        }.get(key))

    def create_mock_event(self, state: str, existing_labels=None) -> PatientUpdated:
        mock_event = MagicMock(spec=PatientUpdated)
        mock_event.context = {
            "patient": {
                "id": "pt_123",
                "addresses": [{"use": "home", "state": state}],
                "labels": existing_labels or []
            }
        }
        return mock_event

    def test_new_out_of_state_transition_triggers_both_label_and_webhook(self):
        # Patient moves to MA, has no existing hold labels. Should trigger both internal & external effects.
        event = self.create_mock_event("MA", existing_labels=[])
        response: EventResponse = self.plugin.handle_patient_updated(event)
        
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 2)
        self.assertTrue(any(isinstance(e, UpdatePatientLabels) for e in response.effects))
        self.assertTrue(any(isinstance(e, CallExternalAPI) for e in response.effects))

    def test_idempotence_existing_out_of_state_patient_skips_redundant_label(self):
        # Patient is already flagged in the EMR. Do not generate a redundant database update effect.
        event = self.create_mock_event("MA", existing_labels=["OUT_OF_STATE_COMPLIANCE_HOLD"])
        response: EventResponse = self.plugin.handle_patient_updated(event)
        
        self.assertEqual(len(response.effects), 1)
        self.assertTrue(isinstance(response.effects[0], CallExternalAPI))

    def test_repatriated_patient_automatically_removes_emr_hold(self):
        # Patient moves back to NH. System should emit an effect to clean up the compliance hold.
        event = self.create_mock_event("NH", existing_labels=["OUT_OF_STATE_COMPLIANCE_HOLD"])
        response: EventResponse = self.plugin.handle_patient_updated(event)
        
        self.assertEqual(len(response.effects), 1)
        self.assertTrue(isinstance(response.effects[0], UpdatePatientLabels))
        self.assertEqual(response.effects[0].labels_to_remove, ["OUT_OF_STATE_COMPLIANCE_HOLD"])

if __name__ == "__main__":
    unittest.main()
