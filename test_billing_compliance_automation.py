import unittest
from unittest.mock import MagicMock
from billing_compliance_automation import (
    BillingComplianceAutomationPlugin, PatientUpdated, EventResponse, CallExternalAPI, UpdatePatientLabels
)

class TestBillingComplianceAutomationPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = BillingComplianceAutomationPlugin()
        self.plugin.get_config = MagicMock(side_effect=lambda key: {
            "HOME_STATE": "NH",  # Clinic is anchored in New Hampshire
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

    def test_nh_patient_remains_silent_in_operating_state(self):
        # Scenario 1: Patient address is NH, matching clinic home state. No effects should fire.
        event = self.create_mock_event("NH", existing_labels=[])
        response: EventResponse = self.plugin.handle_patient_updated(event)
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 0)

    def test_ma_patient_triggers_compliance_hold_and_billing_api_webhook(self):
        # Scenario 2: Patient updates address to MA. System must apply internal hold and call external API.
        event = self.create_mock_event("MA", existing_labels=[])
        response: EventResponse = self.plugin.handle_patient_updated(event)
        
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 2)
        self.assertTrue(any(isinstance(e, UpdatePatientLabels) for e in response.effects))
        self.assertTrue(any(isinstance(e, CallExternalAPI) for e in response.effects))

    def test_idempotent_guardrail_ignores_subsequent_updates_for_ma_patient(self):
        # Scenario 3: Patient is in MA but already has the compliance label. Stand down to avoid API/DB spam.
        event = self.create_mock_event("MA", existing_labels=["OUT_OF_STATE_COMPLIANCE_HOLD"])
        response: EventResponse = self.plugin.handle_patient_updated(event)
        
        # Only the external clearinghouse webhook is dispatched; internal EMR state is left untouched
        self.assertEqual(len(response.effects), 1)
        self.assertTrue(isinstance(response.effects[0], CallExternalAPI))

if __name__ == "__main__":
    unittest.main()
