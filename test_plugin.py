import unittest
from unittest.mock import MagicMock
from plugin import OutOfStateBillingAlerterPlugin, PatientCreated, EventResponse

class TestOutOfStateBillingAlerterPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = OutOfStateBillingAlerterPlugin()
        self.plugin.get_config = MagicMock(side_effect=lambda key: {
            "HOME_STATE": "New Hampshire ",  # Input with space to test utility normalization
            "BILLING_WEBHOOK_URL": "https://api.billing.internal/v1/alerts",
            "WEBHOOK_AUTH_TOKEN": "mock_secret_token"
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

    def test_in_state_abbreviation_emits_no_effects(self):
        event = self.create_mock_event("NH")
        response: EventResponse = self.plugin.handle_patient_created(event)
        self.assertTrue(response.success)
        self.assertEqual(len(response.effects), 0)

    def test_out_of_state_abbreviation_triggers_webhook(self):
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

    def test_full_state_names_are_normalized_correctly(self):
        # Full name out-of-state input ("Massachusetts") should normalize to "MA" and trigger webhook
        event_out = self.create_mock_event("Massachusetts")
        response_out = self.plugin.handle_patient_created(event_out)
        self.assertEqual(len(response_out.effects), 1)
        self.assertEqual(response_out.effects[0].payload["patient_state"], "MA")

        # Full name in-state input ("New Hampshire") should normalize to "NH" and match HOME_STATE
        event_in = self.create_mock_event("New Hampshire")
        response_in = self.plugin.handle_patient_created(event_in)
        self.assertEqual(len(response_in.effects), 0)

if __name__ == "__main__":
    unittest.main()
