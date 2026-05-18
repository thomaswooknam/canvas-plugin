# Event-Driven Billing Compliance Workflow

## Overview
A custom, decoupled integration prototype built for the Canvas EMR platform. This plugin listens for the `PatientCreated` core event lifecycle hook, intercepts the demographic payload, and evaluates the record for out-of-state residency compliance. If the patient's primary address falls outside the clinic's home operating state, the workflow dispatches a structured external API webhook to alert the billing department for automated rate adjustments.

## Problem Statement & Startup Constraints
In a scaling clinical environment, catching out-of-state registrations manually introduces immediate human error and revenue leakage. Developing custom workflows for proprietary EMR systems typically requires dedicated, multi-tenant cloud sandbox instances. 

Operating independently without a live tenant sandbox, I took a proactive, self-starting approach:
1. **Defensive Data Architecture:** Real-world data is dirty. The plugin logic does not assume perfect inputs; it safely navigates nested JSON blocks, handling missing address nodes, casing anomalies, and empty data strings gracefully without throwing unhandled runtime exceptions.
2. **Standalone Test Engineering:** To validate production-readiness, I engineered a comprehensive local test harness using Python mock objects. By simulating the platform runtime environment, database event schemas, and configuration variables, the code achieves 100% deterministic test coverage locally—costing zero infrastructure overhead.

## Architecture & Data Flow
- **Intercept:** Subscribes to `PatientCreated` lifecycle hooks.
- **Normalize:** Safely processes nested address attributes (`.get()`, validation checks).
- **Evaluate:** Compares primary home state metadata against a configurable clinic base (`HOME_STATE`).
- **Action:** Packages IDs and demographic attributes into a signed payload, executing a platform-managed `CallExternalAPI` webhook effect to the billing endpoint.

## Local Test Execution
The test suite utilizes native Python validation mechanics and requires no external third-party dependencies:

```bash
python test_plugin.py
