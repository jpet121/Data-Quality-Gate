# Structured Event Schema Validator

**A Python engineering portfolio project focused on reliable data validation, AI-assisted software development, and evidence-based verification.**

**Stack:** Python 3.12+ · Pydantic v2 · pytest · Hypothesis · SQLite · PostgreSQL · Lean 4

> **In plain English:** This program checks incoming business-event messages for required information, correct data types, and configured business rules. It accepts valid records and rejects invalid ones with an explicit reason. It never invents missing information.

**Current status:** Version 1.0.2 was **technically verified for a local, synthetic demonstration**. Final human release approval remains **pending**. This is not a deployed enterprise service.

## At a glance

| Question | Answer |
| --- | --- |
| **What did I build?** | A configurable validator for structured business-event messages, with typed results, explicit rejection reasons, and optional database persistence. |
| **Why did I build it?** | To practice directing an AI-assisted engineering workflow from requirements through implementation, defect correction, and independently reviewable verification. |
| **What skills does it show?** | Python application architecture, schema design, Pydantic validation, testing, fuzzing, fault injection, data persistence, software assurance, and technical documentation. |
| **Can someone run it?** | Yes. A complete downloadable application archive and sample inputs are provided below. |
| **Is it an AI model or agent?** | No. It demonstrates software-engineering foundations and disciplined use of AI coding tools—not LLM training, RAG, or a deployed agent. |

## See it work: three sample business events

The included demonstration processes three synthetic transactions:

| Incoming event | What the validator finds | Result |
| --- | --- | --- |
| Order created for **$25.00** | Required fields are present; the record follows the configured schema. | **ACCEPTED** |
| Order created **without an amount** | Required \`gross_amount\` field is missing. | **REJECTED** — \`missing_field\` |
| Payment authorized for **$25.00** | Required payment fields and types are valid. | **ACCEPTED** |

An accepted payment **does not** mean that a bank actually transferred money. The validator checks event data against its rules; it is not connected to a payment network.

### What happens inside?

\`\`\`text
Incoming event text
        |
        v
Parse fields and normalize permitted aliases
        |
        v
Select an unambiguous rule from a configurable event matrix
        |
        v
Strict Pydantic v2 validation
        |
        +---- VALID ----> ACCEPTED structured record
        |
        +---- INVALID --> REJECTED with a specific error
                                   |
                                   v
                   Optional SQLite / PostgreSQL audit storage
\`\`\`

The demonstration recognizes five types of event: **ORDER_CREATED**, **PAYMENT_AUTHORIZED**, **INVENTORY_RESERVED**, **SHIPMENT_DISPATCHED**, and **ORDER_CANCELLED**. These are **synthetic examples**, not live customer or enterprise integrations.

## Why this project exists

My goal is to transition into **AI engineering**. I built this project to demonstrate a practice that matters when using AI to write software: **generating code is not the same as proving it behaves as required**.

I directed an engineering process involving specification and architecture contracts, AI-assisted implementation through Codex, independent verification, defect remediation, repeated testing, and preserved evidence. I supplied the objectives, source materials, quality requirements, and human approval boundaries. AI tools helped produce and revise implementation and verification artifacts.

The objective was to create an inspectable *engineering result*, not just a program that appeared to work once.

## How the engineering was tested

These are results **recorded in the verified release evidence**. They are finite, scoped test results—not proof that every possible defect has been eliminated.

| Method | What we actually tested | Recorded result |
| --- | --- | --- |
| **Unit, integration, regression, property-based, and stateful testing** | Parsing, validation, storage, concurrency, and failure behaviors in the required suite. | **410 / 410 passed**, with 0 failures, errors, or skips. |
| **Hypothesis and boundary fuzzing** | Generated unusual and malformed inputs, including Unicode and structured-data edge cases, to search for crashes and inconsistent outcomes. | **50,000** seeded boundary cases in an additional campaign. |
| **Differential testing** | Compared the program with a separately implemented reference over an explicitly supported subset of input behavior. | **100,000** comparisons; 0 reported anomalies. |
| **Mutation testing** | Intentionally altered code behavior to see whether the tests detected the faults. | **16 / 16** selected valid mutations detected. |
| **Fault injection and database testing** | Exercised rollback, persistence failures, duplicate/conflicting messages, and concurrent PostgreSQL operations. | Required integration and regression checks passed. |
| **Lean 4 formal modeling** | Checked mathematical models of release-gate and data-store properties. | **14 checked theorems** across two models. |
| **Application coverage** | Measured the application code exercised by the suite. | **97.22% statement** and **90.57% branch** coverage. |
| **Packaged-artifact replay** | Retrieved the uploaded release ZIP, checked file integrity, and reran required tests against extracted files. | **410 / 410 passed** in the recorded post-upload replay. |

### The thinking behind the tests

**Feynman-inspired falsification.** Rather than asking only, “Can I demonstrate that this works?”, the verification process asked, “What assumption could be wrong, and what test would expose it?” This is an engineering mindset inspired by scientific falsification—not a claim of implementing a formal “Feynman protocol.”

**Fuzzing with Hypothesis.** Traditional tests check cases engineers think to write. Property-based tests generate more varied cases and look for violations of invariants: malformed input should be rejected predictably, duplicate fields should not be silently accepted, and processing should remain deterministic where required.

**Differential verification.** One implementation agreeing with its own tests can still be wrong. A second, differently implemented reference helps detect disagreement. The reference has limits and some shared underlying language behavior; it is not an infallible oracle.

**Mutation testing.** A passing suite might be too weak to detect actual mistakes. By deliberately changing comparisons, conditions, state transitions, and other behaviors, the verification checked whether the tests failed when the code was made wrong.

**LIGO-inspired signal/failure injection.** High-assurance systems benefit from deliberately inserting known conditions and checking whether detection and recovery behave correctly. Here, that idea informed *software* fault injection and verifier calibration; this project did not test a physical detector or receive LIGO certification.

**Formal methods with Lean 4.** Abstract release and storage models were mathematically checked. These results support specific properties of those models; they do **not** amount to a formal proof that the entire Python application is correct.

### Defects were found and repaired

Verification was not a ceremonial pass. The work identified and addressed issues including PostgreSQL JSON handling, concurrent uniqueness conflicts, nested money parsing, Decimal arithmetic under altered contexts, and oversized/deep configuration inputs. The retained evidence distinguishes original failures, subsequent fixes, and regression tests.

See the [verification report](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/delivery/VERIFIED_RELEASE_REPORT.md) and [engineering case study](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/engineering-knowledge/project/CASE_STUDY.md) for the detailed record.

## Try it yourself (Windows PowerShell)

**Download:** [Complete v1.0.2 application and evidence ZIP](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/delivery/Structured_Event_Schema_Validator_v1_0_2_RELEASE_AND_EVIDENCE.zip?raw=true). If GitHub displays a file page, select **Download raw file**.

1. Extract \`Structured_Event_Schema_Validator_v1_0_2_RELEASE_AND_EVIDENCE.zip\`.
2. Inside the extracted contents, find and extract \`Structured_Event_Schema_Validator_v1_0_2_VERIFIED_CANDIDATE.zip\` to a **fresh folder**.
3. Open the folder containing \`main.py\`, \`src/\`, and \`examples/\`. In File Explorer, type \`powershell\` in the address bar to open PowerShell there.
4. Install Python **3.12** if it is not installed, then run:

\`\`\`powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "pydantic>=2.10,<3"
.\.venv\Scripts\python.exe main.py --matrix .\examples\matrix_v1.json --input .\examples\replay.jsonl | ForEach-Object { ($_ | ConvertFrom-Json).status }
\`\`\`

**Expected output:**

\`\`\`text
ACCEPTED
REJECTED
ACCEPTED
\`\`\`

That is a **functional smoke test**, not the complete verification campaign. To view the full structured JSON output, rerun the last command without the PowerShell \`| ForEach-Object { ... }\` filter.

The complete technical suite uses additional declared dependencies and supporting tools, including PostgreSQL and Lean 4. Its existing execution logs and evidence are available below.

## Evidence and release materials

| Resource | What it contains |
| --- | --- |
| [Application and evidence ZIP](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/delivery/Structured_Event_Schema_Validator_v1_0_2_RELEASE_AND_EVIDENCE.zip?raw=true) | Portable code, tests, sample inputs, and verification artifacts. |
| [Verification report](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/delivery/VERIFIED_RELEASE_REPORT.md) | Test methods, defects, corrections, evidence, and caveats. |
| [Requirements traceability](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/delivery/REQUIREMENTS_TRACEABILITY.csv) | Requirements mapped to verification dispositions. |
| [Post-upload verification](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/delivery/post_upload_check/POST_UPLOAD_ZIP_CHECK.json) | Integrity check and test replay of the published artifact. |
| [Engineering retrospective](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/engineering-knowledge/project/CASE_STUDY.md) | How the engineering decisions, defect corrections, and verification evolved. |
| [Release readiness decision](https://github.com/jpet121/Structured_Event_Schema_Validator/blob/verified-v1.0.2-delivery/delivery/RELEASE_READINESS.json) | Technical readiness and outstanding human-release approval. |

**Repository note:** The default \`main\` branch is the portfolio landing page. The verified application and evidence are preserved on \`verified-v1.0.2-delivery\`; the full application source is included inside its downloadable ZIP.

## Limitations and release status

- The tested application is a **local, synthetic business-event demonstration**. It does not ship with live ERP, payment, warehouse, or carrier connections.
- It is not a deployed production service and does not provide all organization-specific access controls, operational recovery, or production integrations.
- Fuzzing, mutation testing, differential comparisons, and model checking cover **bounded, specified scopes**, not every imaginable input or failure.
- The technical verification record reports no confirmed unresolved defects within its verified scope. **Final human release approval has not been granted.**
- This project demonstrates **AI-assisted software engineering and verification**, not an AI model, RAG pipeline, or autonomous AI agent.

---

**Portfolio focus:** Engineering reliable systems with clear requirements, testable behavior, observable failures, reproducible evidence, and accountable human decisions—even when AI contributes the implementation.
