# Installation, recovery and fresh-session use

## What is actually installed

The inspected Codex home is `/home/agent/.codex`, with an initially empty config.toml and no global AGENTS.md or override. The user-level skill directory `/home/agent/.agents/skills` did not exist. No equivalent engineering skill or skill-creator was available in the cloud/executor catalogs or inspected local skill roots. Existing document/PDF/presentation/spreadsheet skills were preserved.

Installed here:

- `/home/agent/.codex/AGENTS.md`: one marked 179-word global engineering addition.
- `/home/agent/.agents/skills/evidence-driven-python-build/SKILL.md`: the named user-scoped skill, with four references and three templates. The supporting `.installation.json` tracks owned file hashes.

This is an actual Linux user-home installation, not installation on the user's Windows PC or into every account/chat. The current chat's cloud plugin catalog is separate from local CLI disk discovery; installing a file does not promise an immediate new entry in an already-running chat's tool catalog.

The installer preserves unrelated global bytes and skill files, backs up existing files before a change, refuses conflicting/unrecognized/locally edited skill content or active global overrides, and is idempotent. Since the real global file was absent, no old global file required a backup; the existing-content/backup case is tested with isolated fixtures. Inspect backups under `<Codex home>/knowledge-backups/evidence-driven-python-build/` if a future authorized change affects an existing file.

## Portable installation

Extract the single knowledge-backup ZIP, open a terminal in its engineering-knowledge directory, and inspect this guide, `guidance/GLOBAL_AGENTS_ADDITION.md` and the skill. Use Python 3 with the standard library (tested with this environment's Python 3.12). No runtime dependency, token, login or network request is needed by the installer/validator.

```bash
python3 tools/validate.py --skill skills/evidence-driven-python-build --manifest-root .
python3 tools/install.py --dry-run
python3 tools/install.py --report /tmp/engineering-knowledge-install.json
```

On Windows use `py -3` instead of `python3` and select a suitable writable report path. The defaults inspect `CODEX_HOME` if configured, otherwise the current user's `.codex`; the user skill root defaults to that user's `.agents/skills`. Do not replace CODEX_HOME or HOME with another installation merely to make the command succeed. To select an explicitly inspected custom installation, use `--codex-home <actual Codex home> --skills-root <actual supported skill root>`. No automatic Windows installation or discovery has been tested here.

Validate the installed paths, substituting the actual discovered home:

```bash
python3 tools/validate.py --skill /home/agent/.agents/skills/evidence-driven-python-build --global-file /home/agent/.codex/AGENTS.md
```

A rerun produces zero changed files when the installed content matches. Do not force through a conflict: inspect existing authorized guidance and reconcile it before an update. For recovery, restore a needed content-addressed backup and validate before resuming. Removing this package means removing only its marked block and owned skill files after review, not deleting unrelated global instructions or a whole skill root. The installer intentionally supplies no destructive blanket uninstall.

## Discovery, precedence and scope

Codex's global guidance mechanism uses the selected Codex home's AGENTS.md. Project guidance is resolved along the working-directory path; relevant AGENTS.override.md and repository instructions must be inspected. More local guidance can narrow implementation details, and current user/higher-priority instructions retain their precedence. A real conflict is a reporting/adjudication issue, not permission to overwrite a source requirement. This package never modifies another project's overrides.

The installed user skill is discoverable outside this repository by a fresh Codex process using the same home. A fresh `codex app-server` with native `skills/list` and forceReload actually reported this skill enabled, user-scoped, at its exact path with zero parser errors. The detailed response and probe are in verification/. File parsing, native discovery and inference-driven application are separate stages.

The latter stage was attempted using read-only `codex --no-daemon exec --ephemeral` from a fresh directory, an explicit skill invocation and a response schema. Proxy HTTP CONNECT 403 blocked the inference endpoint before the model could execute. It was stopped without authentication changes or network bypass. **Automatic global instruction application by a fresh model session is not verified.** Repeat that check in a permitted context rather than treating native discovery as proof of model compliance.

## Start a new build

1. Start a new Codex CLI session using this installed home, or restore/install the portable package in the intended Codex installation first.
2. Set the actual project working directory and inspect its own instructions/specifications. A new task must supply its own authoritative inputs; the validator sample is not its functional specification.
3. Invoke exactly:

```text
Use $evidence-driven-python-build to implement and verify this project against its attached authoritative specification. Repair confirmed defects here, run risk-appropriate tests, preserve regression coverage, and verify the exact required release artifacts.
```

4. Confirm the new session can list/read the installed skill. If the hosting interface exposes only plugin-managed skills, use a native Codex context with the installed user skill root or attach/read the portable SKILL.md and references explicitly; do not claim automatic plugin installation.
5. The workflow establishes source roles, chooses proportionate architecture/tests, repairs reproducible defects and verifies the exact requested outputs. It does not force PostgreSQL, Pydantic, a particular Python version, main.py, fuzz counts or manual approval on an unrelated contract.

## Managed cloud persistence

The current environment draft's existing install script and startup instructions were preserved and extended with an idempotent knowledge restore/validation step. Repository membership, network policy and credential requirements were left unchanged. The appended commands were executed successfully. The draft is saved but **not published**. Review/save it in environment settings and publish if a new filesystem snapshot is desired; no cold restoration was tested.

The configured repository ref is still main, whereas this knowledge package is stored on `verified-v1.0.2-delivery`. The live filesystem contains the installed package. If a future checkout/snapshot lacks `engineering-knowledge`, restore it from that delivery branch or the portable backup before the saved restore step can succeed. No hidden checkout, force-reset, new worktree, credential migration or network broadening was introduced.

The private repository also supplies a working download route for the backup. Prior chat workspace/sandbox links failed and are not used as a delivery claim. Verify the external ZIP checksum and the internal manifest after downloading. Cross-device installation, cloud publication and final application release approval remain separate user actions.
