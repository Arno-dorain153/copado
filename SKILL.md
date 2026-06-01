# SKILL.md — AI Agent Instruction Manual for copado-hx

This document teaches AI coding assistants (e.g., Cursor, Claude Desktop, OpenAI, Salesforce Agentforce) how to autonomously drive the `copado-hx` CLI to manage Salesforce DevOps pipelines on behalf of the developer.

---

## 1. Identity & Scope

You have access to `copado-hx`, a unified terminal CLI giving you full control over the Copado DevOps platform for Salesforce. Through this skill, you can manage user stories, trigger CI/CD pipeline actions (commit, promote, validate, deploy), execute Copado Robotic Testing (CRT) test suites, and converse with Copado's 5 specialist AI agents (Plan, Build, Test, Release, Operate) — completely headless, without opening a browser tab.

---

## 2. Prerequisites & Safety Rules

- `copado-hx auth status` must return an authenticated session before executing any pipeline operations. If not authenticated, instruct the user to run `copado-hx auth login` and pause.
- A working user story context must be set with `copado-hx story set --id <id>` before initiating commit, promote, or deploy operations.
- Never infer or fabricate pipeline IDs, environment names, user story IDs, or suite IDs. Always retrieve them using `copado-hx story list` or `copado-hx test list`.

---

## 3. Commands Reference

Always append `--json` to commands when executing them programmatically to receive structured JSON output.

### `copado-hx commit`
* **Purpose**: Commits metadata components (e.g. `ApexClass:AccountService`) to Git and updates the Copado user story tracking.
* **When to Use**: After the developer has modified local metadata files and wishes to save them to the story branch.
* **Syntax**: `copado-hx commit [--message <msg>] [--us <id>]`
* **Output Example**: `{"status": "Completed Successfully", "commitId": "C-D12A11", "filesCommitted": [...]}`

### `copado-hx promote`
* **Purpose**: Promotes the current user story changes to the next environment in the pipeline.
* **Flags**:
  - `--env <name>`: Target environment (e.g. `UAT`, `PROD`).
  - `--validate`: Validation-only deployment run (does not release/merge).
* **Output**: JSON with `{ "promotionId": "...", "jobExecutionId": "..." }`.

### `copado-hx test run`
* **Purpose**: Triggers a Copado Robotic Testing (CRT) test job in the cloud.
* **Syntax**: `copado-hx test run --suite <suite-id>` or `copado-hx test run --job <job-id>`
* **Output**: JSON with `{ "executionId": "...", "status": "Triggered" }`.

### `copado-hx ai ask`
* **Purpose**: Queries one of the 5 specialist lifecycle agents.
* **Syntax**: `copado-hx ai ask --agent <plan|build|test|release|operate> "<prompt>"`

### `copado-hx ai analyze-logs`
* **Purpose**: Scans a deployment log file for warnings or failures, outputting a risk score (1-100).
* **Syntax**: `copado-hx ai analyze-logs <logfile>`

---

## 4. Workflow Playbooks

### Playbook: Full Story Delivery (Commit ➔ Validate ➔ Test ➔ Release)
*Use this when the developer says: "ship my changes", "deploy US-1234 to UAT", or "promote my story."*

1. **Verify Authentication**: Execute `copado-hx auth status --json`.
2. **Lock Context**: Set active context with `copado-hx story set --id <us-id> --json`.
3. **Analyze Code Scope**: Run `copado-hx ai ask --agent build "What metadata should I commit for <us-id>?"`.
4. **Commit Metadata**: Execute `copado-hx commit --message "feat: apex scoring updates" --us <us-id> --json`.
5. **Validate in UAT**: Execute `copado-hx promote --env UAT --validate --json`.
6. **Check Telemetry**: Wait for completion, or guide user to monitor with `copado-hx status --watch`.
7. **Run Smoke Tests**: Get suite ID via `copado-hx test list --json`, then run `copado-hx test run --suite <suite-id> --json`.
8. **Verify Results**: Check test runs via `copado-hx test status --execution <id> --json`.
9. **STOP & Checkpoint**: If tests pass, ask the human developer: *"All tests passed. Shall I proceed to promote to UAT/Production?"*
10. **Deploy**: Upon explicit confirmation, run `copado-hx deploy --env UAT --json`.

---

## 5. Safety Guardrails (Non-Negotiable)

🚫 **Never run `copado-hx deploy --env PROD` without explicit human confirmation.** Pause and ask the developer to confirm.
🚫 **Never store or output API tokens** in logs, screen prompts, or comments.
🚫 **Never assume or guess story IDs or branch names.** Query the database first.
🚫 **Stop execution if a quality check fails.** Do not attempt promotions if code coverage is below 75% or test runs report errors.
⚠️ **Limit consecutive pipeline modifying operations** (commits/promotions) to a maximum of 3 before asking for manual validation.

---

## 6. Output Parsing Guide

All commands support `--json`. Parse the returned structure using this key:

| Output Field | Status Value | Recommended Agent Action |
|---|---|---|
| `status` | `"Completed Successfully"` | Proceed to next playbook step. |
| `status` | `"Completed with Errors"` | STOP. Retrieve log details and display failures to developer. |
| `status` | `"Failed"` | STOP. Invoke `copado-hx ai ask --agent release "Analyze failure error"` and report. |
| `testResult` | `"Succeeded"` | Safe to proceed with pipeline promotion. |
| `testResult` | `"Failed"` | Test failures found. Halt pipeline, present logs. |
