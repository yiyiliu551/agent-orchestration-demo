# agent-orchestration-demo

AI Agent Task Orchestration with LangGraph
A production-ready AI agent pipeline that demonstrates task decomposition, multi-tool coordination, and built-in security layers.
Inspired by studying OpenClaw and thinking deeply about how AI agents should be designed.

Architecture
User Request
     ↓
🛡️  Guardrails (anti-abuse check)
     ↓
🎨  Figma Node (UI design spec)
     ↓
💻  Claude Code Node (code generation)
     ↓
🧪  Test Node (validation)
     ↓ (fail → retry, max 2x)
✅  Done
3 Core Principles
1. Task Decomposition + Routing
Complex tasks are broken into subtasks, each routed to the most capable tool. Not one AI doing everything — each tool does what it does best.
2. Built-in Guardrails (Anti-abuse)
Before any execution, a guardrail layer checks for dangerous instructions (prompt injection, destructive commands). Blocked at intent level, never reaches the sandbox.
3. Evaluation + Retry Loop
Each output is validated. If it fails, the agent retries automatically (up to MAX_RETRIES). No silent failures.

Quickstart
bash# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Run
python main.py

Example Output
TEST 1: Normal request
==================================================
🛡️  Guardrail check...
✅ Guardrail passed.
🎨 Figma: designing UI for 'Build a login page'...
💻 Claude Code: generating code from design spec...
🧪 Test: validating generated code...
✅ Test passed.
📄 Final result: All tests passed

TEST 2: Dangerous request (guardrail test)
==================================================
🛡️  Guardrail check...
🚨 BLOCKED: detected dangerous keyword 'rm -rf'
🚫 Request blocked. Reason: Request blocked by guardrail

Why This Matters
Most AI agents today have too much permission and no safety layer.
This project demonstrates a 3-layer security architecture:

Physical isolation (sandbox per task)
Guardrails (intent-level anti-abuse)
Validation (output evaluation before acceptance)


"Permissions are necessary — but they must come with physical isolation and code-level guardrails."


Tech Stack

LangGraph — task orchestration
Anthropic Claude — code generation
Python 3.11+
