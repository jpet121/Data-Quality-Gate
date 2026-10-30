# CAPTURE: Codex Engineering Knowledge, Continuous Improvement & Reusable Skills

## Objective

Conduct a comprehensive, evidence-based retrospective of this completed software development and verification effort.

Capture the original requirements, user corrections, architectural decisions, successful workflows, confirmed defects, root causes, repairs, meaningful tests, verification evidence, failed approaches, and completion criteria.

Convert the resulting knowledge into **permanent, reusable engineering guidance for future builds within this Codex environment**.

This is an operational knowledge capture and installation task—not a request to rebuild the completed application.

**Execute the entire process, including installation and verification, wherever the active environment permits. Do not stop at recommendations or produce files without installing them when installation is authorized and supported.**

## 1. Recover the Complete Engineering History

Examine the available conversation context, original specifications, execution contracts, source code, repository history, tests, verification reports, release artifacts, and supporting references.

Recover and document:

- Original project objectives, specifications, functional requirements, constraints, interfaces, and acceptance criteria.
- All user corrections, clarifications, restrictions, and approved changes.
- Initial architecture and implementation decisions.
- Changes made during development and the reasons for those changes.
- Confirmed defects, their root causes, and corrective actions.
- Regression tests created to prevent recurrence.
- Failed approaches, ineffective solutions, and unnecessary complications.
- Successful development, debugging, testing, and verification techniques.
- Dependency, runtime, environment, persistence, packaging, and installation problems.
- Final verified state, unresolved issues, and documented limitations.

For each significant defect, preserve this structure:

**Defect → Reproduction Evidence → Root Cause → Repair → Regression Verification → Reusable Lesson**

Distinguish verified facts, user-authorized decisions, engineering inferences, proposed improvements, and unresolved questions.

Do not invent missing history or represent unavailable evidence as verified.

## 2. Preserve Requirements and User Authority

Original requirements and subsequent user-approved corrections remain authoritative.

Do not silently change specifications, interfaces, expected behavior, or output contracts.

Preserve the distinction between:

1. Original requirements.
2. Authorized user corrections.
3. Implementation decisions.
4. Engineering recommendations.
5. Unresolved requirements.

A passing test suite does not override an unmet requirement.

Where an authoritative source is unavailable, record the limitation and its effect on verification.

Do not convert historical implementation choices into universal requirements.

## 3. Extract Universal Engineering Guidance

Identify principles that improve reliability across future Python and other software-development projects.

Cover relevant lessons concerning:

- Specification fidelity and requirements traceability.
- Architecture, modularity, separation of concerns, and dependency boundaries.
- Appropriate design patterns and abstraction.
- Type safety, data validation, and immutability where justified.
- Input handling, deterministic behavior, and error propagation.
- Transaction integrity, persistence, and state management.
- Security, dependency management, and environment compatibility.
- Testability, observability, and fault isolation.
- Independent verification and regression prevention.
- Packaging, installation, and artifact integrity.
- Evidence-based completion and release decisions.

Keep universal rules concise, actionable, and technology-neutral whenever possible.

For example, preserve the universal requirement that persistence failures must produce observable failure behavior—not a permanent rule requiring every future application to use the same CLI exit-code convention.

Likewise, Python 3.12, Pydantic v2, PostgreSQL, and standalone `main.py` requirements apply to future projects only when specified by their own contracts.

## 4. Establish the Repeatable Development Workflow

Develop a reusable engineering workflow covering:

1. **Specification intake:** Read all authoritative inputs and identify missing information.
2. **Requirements analysis:** Extract acceptance criteria and establish traceability.
3. **Architecture:** Select justified patterns, interfaces, and dependencies.
4. **Implementation:** Build complete, executable software matching the specification.
5. **Baseline verification:** Execute the available relevant tests and record actual results.
6. **Adversarial review:** Investigate boundary conditions, malformed inputs, unexpected states, and likely failure modes.
7. **Defect reproduction:** Establish reliable evidence before changing code.
8. **Targeted remediation:** Fix root causes rather than suppress symptoms.
9. **Regression verification:** Prove the original defect is corrected.
10. **Risk-based expanded testing:** Check affected interfaces and adjacent behaviors.
11. **Independent verification:** Use available independent checks when warranted by risk.
12. **Repair iteration:** Repeat correction and verification until applicable acceptance criteria pass or a genuine blocker is established.
13. **Artifact construction:** Build exactly the outputs required by the specification.
14. **Release verification:** Validate runtime execution, dependencies, packaging, integrity, and completion evidence.
15. **Knowledge capture:** Preserve new, generalizable lessons for future work.

### Mandatory repair behavior

**When confirmed defects are within the authority and capabilities of the active Codex environment, repair them here.**

Do not stop after identifying failures, generate only a defect report, or unnecessarily instruct the user to transfer the repair to another environment.

Repeat:

**Detect → Reproduce → Diagnose → Repair → Test → Reassess**

Preserve existing working functionality and original tests.

Do not remove failing tests, weaken acceptance criteria, or silence errors merely to obtain a passing result.

A genuine blocker must be explained with supporting evidence.

## 5. Preserve Meaningful Testing Without Overengineering

Capture the methods that materially contributed to verification.

Consider, where applicable:

- Unit and functional testing.
- Boundary-value and malformed-input testing.
- Property-based testing with Hypothesis.
- Stateful and differential testing.
- Fuzzing and randomized adversarial inputs.
- Mutation testing.
- Fault injection and failure-path testing.
- Database integration and transaction testing.
- CLI and subprocess behavior.
- Serialization and schema validation.
- Dependency and runtime compatibility.
- Installation and packaging verification.
- File integrity and reproducible builds.

For each technique, document its purpose, applicable risks, prerequisites, limitations, and evidence produced.

**Select future tests according to the specific change, its affected components, and the potential consequences of failure.**

Do not require every method for every modification.

Do not preserve arbitrary historical test counts, excessive fuzzing targets, temporary workarounds, unnecessary infrastructure, or redundant testing as mandatory global rules.

Use deterministic checks where practical. Add permanent regression tests when a failure is reproducible and its expected behavior can be reliably asserted.

Never claim that testing was performed when it was not.

## 6. Define Evidence-Based Completion Criteria

Establish distinct completion states:

- Implementation complete.
- Applicable tests passing.
- Original requirements verified.
- Runtime and integration behavior verified.
- Release artifact and installation verified.
- Independent verification completed where required.
- Release approved.
- Release blocked.

Before recommending release, verify that:

1. Required functionality is implemented.
2. Original requirements and authorized corrections are satisfied.
3. No confirmed unresolved defects remain within the required release scope.
4. Relevant regression and verification tests pass.
5. Required runtime and integration conditions have been checked.
6. The delivered artifact matches the specified interface and format.
7. Installation and execution instructions are accurate.
8. Unverified requirements, skipped tests, and residual risks are disclosed.
9. Required user approval has been obtained.

Do not interpret passing tests as mathematical proof that software contains zero defects.

Do not claim production readiness without evidence satisfying the applicable release criteria.

## 7. Separate Global Guidance From Detailed Skills

Organize the captured knowledge into three layers.

### Layer A — Global Codex Instructions

Use the effective global `AGENTS.md` mechanism supported by this installation.

Keep the global addition short and limited to durable engineering principles:

- Preserve authoritative requirements and user corrections.
- Implement and repair within the active environment when feasible.
- Diagnose root causes and preserve regression coverage.
- Select verification according to risk and affected behavior.
- Never fabricate execution or test results.
- Preserve existing code, guidance, and unrelated files.
- Verify the exact requested deliverables.
- Disclose blockers and unresolved risks.
- Invoke the reusable engineering skill when the task warrants its full workflow.

Do not insert the complete development playbook into global instructions.

### Layer B — Reusable Codex Engineering Skill

Create or update a focused skill named:

`evidence-driven-python-build`

Use the supported Codex skill-creation mechanism, preferably `$skill-creator` when available.

Include a valid `SKILL.md` with appropriate metadata, a concise trigger description, and a clear workflow.

Put detailed information in supporting references rather than inflating `SKILL.md`.

The skill must cover:

- Specification intake and traceability.
- Architecture and implementation planning.
- Development and test execution.
- Defect reproduction and root-cause repair.
- Risk-based verification selection.
- Independent and adversarial checks.
- Iterative repair and regression control.
- Release criteria and evidence reporting.
- Post-build engineering retrospectives.

Create executable scripts or validators only where they provide meaningful, reusable, deterministic value. Test them before adoption.

Prefer updating an existing equivalent skill over creating overlapping skills.

### Layer C — Project-Specific Evidence

Preserve detailed historical information separately from universal instructions and the core skill.

Include:

- Original requirements and corrections.
- Architecture and implementation decisions.
- Confirmed defects and corrections.
- Test evidence and limitations.
- Release artifacts and integrity information.
- Remaining gaps and unresolved questions.
- Source references and provenance.

Store project-specific evidence in an appropriate repository or project knowledge location.

Do not make unrelated future builds inherit project-specific requirements.

## 8. Discover and Preserve Existing Codex Configuration

Before writing anything:

1. Identify the active Codex home directory and effective configuration.
2. Read existing global `AGENTS.md` instructions.
3. Identify applicable `AGENTS.override.md` and repository-level instructions.
4. Locate existing user-level and repository-level skills.
5. Inspect existing skills related to development, verification, testing, and retrospectives.
6. Determine which existing instructions should be preserved, extended, or reused.
7. Check permissions and whether the current environment supports persistent writes.

Do not assume paths or installation capabilities without inspection.

Preserve all unrelated instructions and skills.

Make backups before modifying existing files.

Use clearly delimited, idempotent updates. Repeated execution must not duplicate instruction blocks or create unnecessary copies.

Do not overwrite conflicting guidance silently. Identify material conflicts and seek approval before changing existing authorized behavior.

Do not modify unrelated repositories, credentials, external services, or deployment configuration.

## 9. Install the Reusable Guidance

After completing the retrospective:

1. Prepare the concise global instruction addition.
2. Prepare or update the engineering skill.
3. Add only necessary supporting references, templates, and validators.
4. Preserve project-specific evidence in its designated location.
5. Apply the changes using the supported persistent mechanisms of the active Codex environment.
6. Verify the written files directly.
7. Validate skill structure, metadata, and reference links.
8. Check for duplicated instructions, conflicts, and unintended modifications.
9. Confirm that existing guidance remains intact.

If persistent installation is unavailable, produce a portable installation package and report that installation was not completed.

Do not claim persistence outside the actual environment where files were written.

## 10. Verify Fresh-Session Discovery

Verify how a future Codex session will discover and apply the installed knowledge.

Check:

- Effective global instruction path and scope.
- Skill installation path and discovery scope.
- Skill metadata and trigger conditions.
- Supporting reference availability.
- Compatibility with repository-specific instructions.
- Precedence or override conflicts.

When supported, conduct a fresh-session test confirming that Codex can discover the skill and load its instructions.

Document an explicit invocation example:

`Use $evidence-driven-python-build to implement and verify this project against its attached authoritative specification. Repair confirmed defects here, run risk-appropriate tests, preserve regression coverage, and verify the exact required release artifacts.`

Distinguish successful file validation from actual fresh-session discovery. Do not claim the latter unless tested.

## 11. Preserve Provenance and Continuous Improvement

For each reusable engineering improvement, record:

- Supporting project evidence.
- The generalizable failure or success mechanism.
- The change being introduced.
- Where the guidance is stored.
- Whether the change was tested.
- Its scope of applicability.
- Any known limitations.

Update existing guidance when new evidence supports a meaningful improvement.

Do not accumulate contradictory instructions, repeated rules, obsolete workarounds, or unnecessary skills.

Prefer the smallest durable improvement that addresses a verified problem.

## 12. Create a Portable Backup

In addition to installing supported persistent guidance, produce **one self-contained ZIP backup** containing:

- The global instruction addition.
- The complete reusable engineering skill.
- All necessary skill references and scripts.
- A detailed project case study.
- Requirements and correction history.
- Significant failures and fixes.
- Testing and verification evidence.
- Completion and release criteria.
- An installation and recovery guide.
- A fresh-session invocation example.
- A source inventory and missing-materials list.
- A SHA-256 integrity manifest.

Include original evidence artifacts only when accessible, relevant, and appropriate to redistribute.

The ZIP is a portable backup, not a substitute for verifying live Codex installation.

## 13. Final Verification

Before declaring this task complete:

- Confirm all intended files were created or updated.
- Verify that existing guidance was preserved.
- Check instruction precedence and conflicts.
- Validate the skill and supporting references.
- Execute relevant validator tests where supported.
- Verify installed file contents and permissions.
- Verify ZIP integrity and SHA-256 hashes.
- Check that the documented invocation references the installed skill.
- Distinguish actual persistence and discovery from untested assumptions.
- Inventory unavailable sources and incomplete verification.

Do not modify the completed application's code merely to perform this knowledge-capture task.

## Final Output Requirements

Provide:

**1. Installation result**

State whether global instructions and reusable skills were actually installed, their exact paths, and their scope.

**2. Knowledge captured**

Summarize original requirements, user corrections, proven workflows, significant defects and repairs, testing lessons, and completion criteria.

**3. Reusable skill**

Identify the skill, its trigger conditions, supporting materials, and how to invoke it.

**4. Verification evidence**

Report actual checks performed, their results, and any limitations.

**5. Portable package**

Provide one downloadable ZIP containing the retained guidance and supporting evidence.

**6. Manual requirements**

Identify anything requiring manual attachment, installation, access authorization, or user approval.

**7. Fresh-build instructions**

Explain precisely how a new Codex session will load and apply the global guidance and reusable skill.

## Governing Principles

**Preserve requirements. Repair defects. Verify results. Capture proven lessons. Generalize only what is reusable. Keep global instructions concise. Maintain detailed workflows in skills. Preserve existing guidance. Never claim verification or persistence that did not occur.**

The objective is a Codex engineering environment that becomes more reliable through accumulated, evidence-backed experience without becoming unnecessarily restrictive or complicated.

