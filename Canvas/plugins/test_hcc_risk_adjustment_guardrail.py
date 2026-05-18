import unittest
from unittest.mock import MagicMock
from Canvas.plugins.hcc_risk_adjustment_guardrail import HCCRiskAdjustmentGuardrail

class TestHCCRiskAdjustmentGuardrail(unittest.TestCase):

    def setUp(self):
        # Base mock context mirrors
        self.mock_context = {
            "note": {
                "patient_id": 99012,
                "encounter_id": 7741,
                "diagnoses": [
                    {"code": "I10", "description": "Essential hypertension"}
                ]
            },
            "laboratory_results": [
                {"test_name": "Microalbumin/Creatinine Ratio", "value": "45.2"}
            ]
        }

    def test_triggers_task_on_risk_code_leakage(self):
        """Should append an AddTask effect if clinical biomarkers indicate HCC gap."""
        handler = HCCRiskAdjustmentGuardrail(context=self.mock_context, secrets={})
        results = handler.compute_effects()

        # Assertions
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["effect_type"], "ADD_TASK")
        self.assertEqual(results[0]["status"], "QUEUED")

    def test_stands_down_if_hcc_code_is_properly_documented(self):
        """Should generate zero effects if the clinician correctly recorded the diagnosis."""
        # Append target manifestation code to the mock note context
        self.mock_context["note"]["diagnoses"].append(
            {"code": "E11.22", "description": "Type 2 diabetes with diabetic nephropathy"}
        )

        handler = HCCRiskAdjustmentGuardrail(context=self.mock_context, secrets={})
        results = handler.compute_effects()

        # Assertions
        self.assertEqual(len(results), 0)

    def test_defensive_handling_for_corrupted_lab_values(self):
        """Should handle non-numeric or broken lab metrics gracefully without a runtime crash."""
        self.mock_context["laboratory_results"] = [
            {"test_name": "Microalbumin/Creatinine Ratio", "value": "CRITICAL_ERROR_STRING"}
        ]

        handler = HCCRiskAdjustmentGuardrail(context=self.mock_context, secrets={})
        results = handler.compute_effects()

        # Assertions
        self.assertEqual(len(results), 0)

if __name__ == "__main__":
    unittest.main()
