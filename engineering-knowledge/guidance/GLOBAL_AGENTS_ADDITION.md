<!-- BEGIN evidence-driven-engineering v1 -->
## Evidence-driven engineering

- Preserve authoritative requirements and explicit user corrections; distinguish them from implementation choices and recommendations. Report material conflicts rather than silently changing expected behavior.
- Implement and repair confirmed defects in the active environment when authorized and feasible. Reproduce, diagnose the root cause, fix it, and retain meaningful regression coverage.
- Preserve existing code, tests, guidance and unrelated files. Do not suppress failures or weaken acceptance criteria to obtain a passing result.
- Select verification according to the change, affected interfaces and consequences of failure; run required gates and disclose skips, uncertainty and genuine blockers.
- Record actual execution and evidence. Never invent tests, measurements, proofs, installation success or release approval.
- Verify the exact requested deliverables, their installation/runtime behavior where required, and their integrity. Keep implementation, testing, requirements verification and release approval as distinct states.
- For substantial implementation, remediation, specification audits, release verification or engineering retrospectives, use the installed `evidence-driven-python-build` skill. Keep routine changes proportionate; its full workflow is not mandatory for every edit.
<!-- END evidence-driven-engineering v1 -->
