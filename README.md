# Event-Driven Billing Compliance Workflow

## Overview
A custom, decoupled integration prototype built for the **Canvas EMR platform**. This plugin listens for core event lifecycle hooks, intercepts demographic payloads, and evaluates records for out-of-state residency compliance. If a patient's primary address falls outside the clinic's home operating state (e.g., a patient in **Massachusetts (MA)** registering with a **New Hampshire (NH)** clinic), the workflow orchestrates synchronous internal EMR updates and external API side-effects.

## Problem Statement & Startup Constraints
In a scaling clinical environment, catching out-of-state registrations manually introduces human error and revenue leakage. Developing custom workflows for proprietary EMR systems typically requires dedicated, multi-tenant cloud sandbox instances. 

Operating independently without a live tenant sandbox, I took a proactive, engineering-first approach:
* **Defensive Data Architecture:** Real-world data is dirty. The plugin logic safely navigates nested JSON blocks, handles missing address nodes, casing anomalies, and empty data strings gracefully without throwing unhandled runtime exceptions.
* **Idempotent State-Machine Design:** Rather than firing duplicate database modifications or webhook calls on every trivial patient profile update, the plugin evaluates existing internal EMR metadata flags first—standing down safely if compliance parameters are already met to eliminate API and database write bloat.
* **Standalone Test Engineering:** To validate production-readiness, I engineered a comprehensive local test harness using Python mock objects. By simulating the platform runtime environment, database event schemas, and configuration variables, the code achieves 100% deterministic test coverage locally—costing zero infrastructure overhead.

## Architecture & Data Flow
1. **Intercept:** Subscribes to the `PatientUpdated` lifecycle hook inside the `/plugins` directory.
2. **Normalize:** Safely extracts nested address attributes (`.get()` patterns) and normalizes strings to ensure clean boundary checks.
3. **Evaluate:** Compares primary home state metadata against a configurable clinic base (`HOME_STATE`) and inspects current EMR labels to check for an existing `OUT_OF_STATE_COMPLIANCE_HOLD`.
4. **Action:** Simultaneously updates internal EMR patient tracking flags and packages demographic attributes into a platform-managed `CallExternalAPI` webhook effect to the billing endpoint.

## Project Structure
```text
canvas-billing-plugin/
├── README.md
└── plugins/
    ├── billing_compliance_automation.py       # Core EMR SDK Plugin logic
    └── test_billing_compliance_automation.py  # Local mock-driven unit tests
