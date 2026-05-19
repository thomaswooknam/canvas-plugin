# Canvas EMR Extensibility Suite (PoC)

A production-grade collection of event-driven, platform-agnostic automation plugins built for the Canvas EMR SDK ecosystem. This repository demonstrates defensive data architecture, state-machine idempotency, and clinical data integrity within complex healthcare data environments.

---

## Active Workflow: Event-Driven Billing Compliance

This core integration prototype listens for EMR lifecycle hooks, intercepts demographic payloads, and evaluates patient records for geographic billing compliance. 

If a patient's primary address falls outside the clinic's home operating state (e.g., a patient in Massachusetts registering with a New Hampshire clinic), the workflow orchestrates synchronous internal EMR status updates and external API side-effects.

### Architecture & Data Flow
1. **Intercept:** Subscribes to the `PatientUpdated` lifecycle hook inside the application workspace.
2. **Normalize:** Safely extracts nested address attributes using defensive `.get()` patterns to handle missing address nodes, casing anomalies, and empty strings without throwing runtime exceptions.
3. **Evaluate:** Compares primary home state metadata against a configurable clinic base (`HOME_STATE`) and inspects current EMR labels for existing compliance holds.
4. **Action:** Eliminates database write bloat by evaluating state flags first (idempotent design), then updates tracking flags and packages attributes into a platform-managed `CallExternalAPI` webhook payload.

---

## Engineering-First Approach & Constraints

Developing custom workflows for proprietary EMR systems typically requires dedicated, multi-tenant cloud sandbox instances. Operating independently without a live tenant sandbox, I engineered a comprehensive local test harness using Python mock objects. 

By simulating the platform runtime environment, database event schemas, and configuration variables, the code achieves deterministic test coverage locally—costing zero infrastructure overhead.

---

## Repository Structure

```text
canvas-billing-plugin/
├── .gitignore                          # Environment and cache isolation
├── requirements.txt                    # Project dependencies (sqlglot, arrow, etc.)
├── README.md                           # Core project documentation
├── test_plugin.py                      # Local mock-driven unit test suite
└── Canvas/                             # Domain-specific SDK workspace
    └── plugins/
        └── billing_compliance_automation.py  # Core automated compliance logic
