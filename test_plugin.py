
import unittest
from unittest.mock import MagicMock

# Pull the simulated/stubbed SDK elements directly from your local plugin file
from plugin import OutOfStateBillingAlerterPlugin, PatientCreated, EventResponse, CallExternalAPI

class TestOutOfStateBillingAlerterPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = OutOfStateBillingAlerterPlugin()
        self.plugin.get_config = MagicMock(side_effect=lambda key: {
            "HOME_STATE": "NH",
            "BILLING_WEBHOOK_URL": "https://api.billing.internal/v1/alerts",
            "WEBHOOK_AUTH_TOKEN": "mock_secret_token"
        }.get(key))

    def create_mock_event(self, state_code: str, use_type: str = "home") -> PatientCreated:
        mock_event = MagicMock(spec=PatientCreated)
        mock_event.context = {
            "patient": {
                "id": "pt_12345",
                "first_name": "John",
                "last_name": "Doe",
                "addresses": [{"use": use_type, "state": state_code}]
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

        effect = response.effects[0]
        self.assertIsInstance(effect, CallExternalAPI)
        self.assertEqual(effect.url, "https://api.billing.internal/v1/alerts")
        self.assertEqual(effect.headers["Authorization"], "Bearer mock_secret_token")
        self.assertEqual(effect.payload["patient_state"], "MA")

    def test_missing_address_handled_gracefully(self):
        event = MagicMock(spec=PatientCreated)
        event.context = {"patient": {"id": "pt_99999", "addresses": []}}
        response: EventResponse = self.plugin.handle_patient_created(event)
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 0)

if __name__ == "__main__":
    unittest.main()
