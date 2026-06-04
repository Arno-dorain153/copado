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

### Playbook: Investigate a Failed Deployment
*Use this when the developer says: "why did my deployment fail?", "fix my pipeline error."*

1. **Get Failed Job**: Run `copado-hx status --json` to retrieve the failed job execution ID.
2. **Analyze Blocker**: Run `copado-hx ai ask --agent release "Analyze the job execution error for <jobExecutionId>"`.
3. **Present Root Cause**: Present the root cause and suggested fix to the developer.
4. **Code Fix (Optional)**: If a code fix is needed, run `copado-hx ai ask --agent build "Fix the issue: <error summary>"`.

### Playbook: Generate and Run a Test
*Use this when the developer says: "write a test for my class", "test this feature."*

1. **Generate Test Script**: Run `copado-hx ai ask --agent test "Generate a CRT QWord test script for <class/feature>"`.
2. **Review Script**: Present the generated script to the developer for review.
3. **STOP & Checkpoint**: Ask the developer: *"Shall I trigger this test suite?"*
4. **Trigger test**: On approval, execute `copado-hx test run --suite <id> --json`.
5. **Retrieve report**: Download test execution report cards: `copado-hx test results --execution <id> --json`.

---

## 5. Safety Guardrails (Non-Negotiable)

🚫 **Never deploy to a PROD or production environment without explicit human confirmation.** Always pause and ask: "I'm about to deploy to PROD. Please confirm."
🚫 **Never fabricate or guess IDs** (user story IDs, pipeline IDs, environment names, suite IDs). Always retrieve them from the CLI first.
🚫 **Never run `copado-hx deploy` immediately after `copado-hx promote`** without checking test results and receiving human approval.
🚫 **Never store or log API tokens** in any output, file, or message.
🚫 **Never chain more than 3 destructive actions** (commit, promote, deploy) without a human checkpoint between each stage.
⚠️ **Always surface test failures to the human** before proceeding to the next pipeline stage. Do not auto-retry failed tests.

---

## 6. Output Parsing Guide

All `copado-hx` commands support `--json` for structured output. Always use `--json` when parsing output programmatically.

| Field | Meaning | Agent Action |
|---|---|---|
| `status: "Completed Successfully"` | Action succeeded | Proceed to next step |
| `status: "Completed with Errors"` | Partial failure | Stop, surface errors to human |
| `status: "In Progress"` | Still running | Poll again in 10 seconds |
| `status: "Failed"` | Hard failure | Stop, invoke Release Agent for analysis |
| `testResult: "Succeeded"` | All tests passed | Safe to proceed |
| `testResult: "Failed"` | Tests failed | Stop, surface failures, do not deploy |

---

## 7. Agent Persona Routing

When the developer's request maps to a DevOps lifecycle stage, route to the appropriate Copado AI agent using `copado-hx ai ask --agent <id>`:

| Developer Says | Route to Agent |
|---|---|
| "Write a user story", "plan this feature", "check for conflicts" | `plan` |
| "Write the code", "generate Apex", "review my class", "fix this bug" | `build` |
| "Write a test", "generate test script", "improve coverage" | `test` |
| "Deploy this", "promote to UAT", "why did it fail?", "release notes" | `release` |
| "Write docs", "create training material", "change management plan" | `operate` |
