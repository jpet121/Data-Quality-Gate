# Repeatable development and repair workflow

Scale these steps to the task. Required project checks remain mandatory; unrelated techniques are optional.

| Step | Action and durable output | Exit condition |
|---|---|---|
| 1. Specification intake | Inventory authoritative inputs, actual source baseline, existing guidance/tests, historical claims and access limits. | Sources and roles are explicit; consequential gaps recorded. |
| 2. Requirements analysis | Map source locations to expected behavior, boundaries, errors, interfaces, state, side effects and acceptance. Separate user decisions from engineering recommendations. | Requirements can be judged independently of observed implementation behavior. |
| 3. Architecture | Choose responsibilities, dependency direction, types/state ownership and minimal interfaces. Record the reason for significant decisions. | Design supports specified behavior without speculative infrastructure. |
| 4. Implementation | Implement complete executable paths and visible failure behavior. Preserve required contracts and compatibility. | Required behavior exists; missing work is not hidden by a placeholder or success return. |
| 5. Baseline verification | Record actual runtime/dependencies, complete commands, exit status, relevant test inventory and prerequisites. | Test, harness, environment and application outcomes are distinguished. |
| 6. Adversarial review | Probe meaningful valid/invalid boundaries, encoding, nested representations, unexpected state and dependencies. | Expected outcomes precede interpreting observations. |
| 7. Defect reproduction | Preserve a minimal input/state/command and expected versus observed behavior. | Failure is reproducible, or uncertainty is honestly recorded. |
| 8. Targeted remediation | Repair the source of the failure, maintaining original assertions and requirements. | Original reproduction now behaves correctly. |
| 9. Regression verification | Add permanent tests when reliable and valuable; rerun affected checks. | Failure would be detected if reintroduced. |
| 10. Expanded testing | Examine adjacent interfaces/serialization/transactions/install behavior according to consequences. | Relevant checks and mandatory gates pass. |
| 11. Independent verification | Use a simpler reference or materially different method where needed; calibrate it and disclose common dependencies. | Required independent evidence exists, or its precise gap is reported. |
| 12. Repair iteration | Repeat reproduction/repair/reassessment when new findings arise; preserve contradictory runs. | No confirmed unresolved defect within required scope, or an evidence-supported blocker. |
| 13. Artifact construction | Generate only required distributions and reviewable evidence; freeze exact source/config/dependency identities. | Outputs match the specified interface and format. |
| 14. Release verification | Check install, entry points, generated outputs, checksums and required integrations. Verify delivered bytes, including remote retrieval when relevant. | Evidence refers to the actual delivered artifact; required approval is separate. |
| 15. Knowledge capture | Separate general principles, detailed skill guidance and project facts; preserve provenance and scope. | Reusable guidance is installed/validated where supported; limits are explicit. |

Before broad reruns, establish why source changes, a failure or an unresolved concern makes the rerun useful. After required checks pass, complete delivery instead of repeatedly expanding the campaign without a reason.

When configuration is ambiguous, inspect connected/repository sources before asking. Advance unrelated work while a decision is pending. Silence is neither approval nor an answer. A current explicit user decision supersedes an earlier local recommendation, but does not automatically grant unrelated deployment or publication authority.
