# 🚀 copado-hx: The Headless DevOps Experience

`copado-hx` is a modern, unified command-line interface (CLI) and AI agent coordinator built for the **Copado Headless Hackathon (CopadoCON Bangalore — June 2026)**. 

Our goal: **Eliminate the friction of context-switching to browser tabs.** Manage user stories, commit metadata, trigger robotic tests, promote changes, run live telemetry dashboards, and assess deployment logs with an AI Risk Engine — entirely from your terminal or AI environment.

---

## ✨ Features

- 🔐 **OAuth/Token Authentication**: Secure local profiles and connection validation.
- 📋 **User Story Workspace Context**: Track metadata scope and lock story contexts.
- 🚀 **Source Format Promotions & Deployments**: Automated validation/promotion runs.
- 📺 **Live Telemetry Dashboard**: Fullscreen Rich-updating dashboard (2-second refresh) tracking quality gates, Apex tests, and build logs.
- 🧪 **Copado Robotic Testing (CRT)**: Manage and run browser test suites.
- 🤖 **5 Specialist AI Agents**: Plan, Build, Test, Release, and Operate.
- 🧠 **AI Risk Analyzer**: Evaluates logs, generates 1-100 risk scores, and suggests safety rollbacks.
- 🔌 **Model Context Protocol (MCP)**: Native stdio server letting AI agents (Cursor, Claude) run DevOps pipelines.
- 💼 **Agentforce Actions Schema**: Standard OpenAPI 3.0 specs ready to load into Salesforce.

---

## 📂 Architecture

```
copado_hx/
├── main.py                  # CLI command registry & shortcuts
├── config.py                # Local state database (~/.copado_hx/db.json)
├── utils.py                 # Premium Rich CLI wrappers & auth guards
├── auth/                    # auth login/logout/status
├── story/                   # story list/create/set/show
├── deploy/                  # commit, promote, deploy & Live Dashboard
├── test/                    # test list, run, status, results
├── ai/                      # ai ask, chat, log analyzer, multi-agent handoff
└── mcp/                     # Stdio FastMCP Server for external agents
```

---

## 🛠 Setup & Installation

### Prerequisites
- Python **>= 3.10**
- Pip (Python Package Manager)

### Install in Developer Mode
From the root directory:
```bash
pip install -e .
```
This registers the global binary `copado-hx` on your system.

---

## 📖 CLI Commands Reference

### 🔐 Authentication
```bash
# Token-based login (CI / non-interactive)
copado-hx auth login --token <api-token>

# Interactive login
copado-hx auth login

# Check active profile
copado-hx auth status

# Clear session
copado-hx auth logout
```

### 📋 User Story Management
```bash
# List assigned stories
copado-hx story list

# Lock working context
copado-hx story set --id US-1234

# Show details, metadata changes, and pipeline path
copado-hx story show
```

### 🚀 Deployments & Promotions
```bash
# Commit metadata to current story context
copado-hx commit --message "feat: apex handler updates"

# Run a validation-only deployment to UAT and watch live logs
copado-hx promote --env UAT --validate --watch

# Perform a full promotion
copado-hx promote --env UAT

# Full environment deployment (PROD triggers safety approval confirmation)
copado-hx deploy --env PROD
```

### 📺 Live Telemetry Dashboard
To launch the fullscreen live-updating monitor directly:
```bash
copado-hx status --watch
```

### 🧪 Robotic Testing (CRT)
```bash
# List available robotic jobs
copado-hx test list

# Execute test suite
copado-hx test run --suite CRT-JOB-910

# Poll test results
copado-hx test results --execution <execution-id>
```

### 🤖 AI Agent Interactions & Risk Engine
```bash
# Query a specialist agent (plan, build, test, release, operate)
copado-hx ai ask --agent build "Generate Apex LeadScoring class"

# Start interactive chat REPL session
copado-hx ai chat --agent plan

# AI Risk Engine: Parse deployment logs, calculate score, evaluate rollbacks
copado-hx ai analyze-logs sample_logs/critical_failure_log.txt

# Demo: Build agent results handed off automatically to Test agent via JSON
copado-hx ai handoff
```

---

## 🔌 Model Context Protocol (MCP) Server

`copado-hx` includes an MCP server. Exposing the CLI directly to agents like Cursor or Claude Desktop allows them to run DevOps pipelines autonomously.

### Start MCP Server
```bash
copado-hx mcp
```

### Connect to Cursor
Add the following to your Cursor settings (`Features -> MCP`):
- **Name**: `copado-hx`
- **Type**: `command`
- **Command**: `python -m copado_hx.mcp.server` or path to your installation.

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
