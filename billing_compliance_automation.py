try:
    from canvas_sdk.plugins import CanvasPlugin
    from canvas_sdk.events import EventResponse, PatientCreated
    from canvas_sdk.effects.external_api import CallExternalAPI
except ImportError:
    class CanvasPlugin: pass
    class EventResponse: 
        def __init__(self, success, effects=None):
            self.success = success
            self.effects = effects or []
    class PatientCreated: pass
    class CallExternalAPI:
        def __init__(self, url, method, headers=None, payload=None):
            self.url = url; self.method = method; self.headers = headers or {}; self.payload = payload or {}

import logging
logger = logging.getLogger(__name__)

class BillingComplianceAutomationPlugin(CanvasPlugin):
    CONFIG_SCHEMA = {
        "HOME_STATE": {"type": "string", "required": True},
        "BILLING_WEBHOOK_URL": {"type": "string", "required": True},
        "WEBHOOK_AUTH_TOKEN": {"type": "string", "required": True, "secure": True}
    }

    def compute_patient_state(self, patient_data: dict) -> str:
        addresses = patient_data.get("addresses", [])
        if not addresses:
            return ""
        primary_address = next((addr for addr in addresses if addr.get("use") == "home"), addresses[0])
        return primary_address.get("state", "").strip().upper()

    def handle_patient_created(self, event: PatientCreated) -> EventResponse:
        home_state = self.get_config("HOME_STATE").strip().upper()
        webhook_url = self.get_config("BILLING_WEBHOOK_URL")
        auth_token = self.get_config("WEBHOOK_AUTH_TOKEN")

        patient_record = event.context.get("patient", {})
        patient_id = patient_record.get("id")
        patient_state = self.compute_patient_state(patient_record)

        if not patient_state or patient_state == home_state:
            return EventResponse(success=True)
        
        payload = {
            "event_type": "patient.created.out_of_state",
            "canvas_patient_id": patient_id,
            "patient_state": patient_state,
            "first_name": patient_record.get("first_name"),
            "last_name": patient_record.get("last_name")
        }

        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        webhook_effect = CallExternalAPI(url=webhook_url, method="POST", headers=headers, payload=payload)
        return EventResponse(success=True, effects=[webhook_effect])
