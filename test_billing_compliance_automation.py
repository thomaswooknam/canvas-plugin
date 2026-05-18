import unittest
from unittest.mock import MagicMock
from billing_compliance_automation import BillingComplianceAutomationPlugin, PatientCreated, EventResponse

class TestBillingComplianceAutomationPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = BillingComplianceAutomationPlugin()
        self.plugin.get_config = MagicMock(side_effect=lambda key: {
            "HOME_STATE": "NH",
            "BILLING_WEBHOOK_URL": "https://api.billing.internal/v1/alerts",
            "WEBHOOK_AUTH_TOKEN": "mock_secret"
        }.get(key))

    def create_mock_event(self, state_code: str) -> PatientCreated:
        mock_event = MagicMock(spec=PatientCreated)
        mock_event.context = {
            "patient": {
                "id": "pt_12345",
                "first_name": "John",
                "last_name": "Doe",
                "addresses": [{"use": "home", "state": state_code}]
            }
        }
        return mock_event

    def test_in_state_patient_emits_no_effects(self):
        event = self.create_mock_event("NH")
        response: EventResponse = self.plugin.handle_patient_created(event)
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 0)

    def test_out_of_state_patient_triggers_webhook(self):
        event = self.create_mock_event("MA")
        response: EventResponse = self.plugin.handle_patient_created(event)
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 1)

    def test_missing_address_handled_gracefully(self):
        event = MagicMock(spec=PatientCreated)
        event.context = {"patient": {"id": "pt_99999", "addresses": []}}
        response: EventResponse = self.plugin.handle_patient_created(event)
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 0)

if __name__ == "__main__":
    unittest.main()
