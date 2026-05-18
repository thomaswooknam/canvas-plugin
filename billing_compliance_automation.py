try:
    from canvas_sdk.plugins import CanvasPlugin
    from canvas_sdk.events import EventResponse, PatientUpdated
    from canvas_sdk.effects.external_api import CallExternalAPI
    from canvas_sdk.effects.patient import UpdatePatientLabels
except ImportError:
    class CanvasPlugin: pass
    class EventResponse: 
        def __init__(self, success, effects=None):
            self.success = success
            self.effects = effects or []
    class PatientUpdated: pass
    class CallExternalAPI:
        def __init__(self, url, method, headers=None, payload=None):
            self.url = url; self.method = method; self.headers = headers or {}; self.payload = payload or {}
    class UpdatePatientLabels:
        def __init__(self, patient_id, labels_to_add=None, labels_to_remove=None):
            self.patient_id = patient_id
            self.labels_to_add = labels_to_add or []
            self.labels_to_remove = labels_to_remove or []

import logging
logger = logging.getLogger(__name__)

class BillingComplianceAutomationPlugin(CanvasPlugin):
    CONFIG_SCHEMA = {
        "HOME_STATE": {"type": "string", "required": True},
        "BILLING_WEBHOOK_URL": {"type": "string", "required": True},
        "WEBHOOK_AUTH_TOKEN": {"type": "string", "required": True, "secure": True}
    }

    def handle_patient_updated(self, event: PatientUpdated) -> EventResponse:
        home_state = self.get_config("HOME_STATE").strip().upper()
        webhook_url = self.get_config("BILLING_WEBHOOK_URL")
        auth_token = self.get_config("WEBHOOK_AUTH_TOKEN")

        patient_record = event.context.get("patient", {})
        patient_id = patient_record.get("id")
        
        # Extract and sanitize state data
        addresses = patient_record.get("addresses", [])
        if not addresses:
            return EventResponse(success=True)
            
        primary_address = next((addr for addr in addresses if addr.get("use") == "home"), addresses[0])
        patient_state = primary_address.get("state", "").strip().upper()

        # Inspect current EMR state tags to ensure idempotence
        current_labels = patient_record.get("labels", [])
        has_compliance_hold = "OUT_OF_STATE_COMPLIANCE_HOLD" in current_labels

        generated_effects = []

        # CONDITION 1: Patient is out-of-state
        if patient_state and patient_state != home_state:
            # Only add the EMR hold label if it is not already there (prevents duplicate DB writes)
            if not has_compliance_hold:
                generated_effects.append(
                    UpdatePatientLabels(patient_id=patient_id, labels_to_add=["OUT_OF_STATE_COMPLIANCE_HOLD"])
                )

            # Dispatch external notification payload to billing infrastructure
            payload = {
                "event_type": "billing.compliance.state_transition",
                "canvas_patient_id": patient_id,
                "detected_state": patient_state,
                "requires_network_review": True
            }
            headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
            generated_effects.append(
                CallExternalAPI(url=webhook_url, method="POST", headers=headers, payload=payload)
            )

        # CONDITION 2: Patient moved BACK into home operating state
        elif patient_state == home_state and has_compliance_hold:
            # Programmatically clean up the EMR hold label automatically
            generated_effects.append(
                UpdatePatientLabels(patient_id=patient_id, labels_to_remove=["OUT_OF_STATE_COMPLIANCE_HOLD"])
            )

        return EventResponse(success=True, effects=generated_effects)
