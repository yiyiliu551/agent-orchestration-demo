"""
AI Agent Task Orchestration with LangGraph
- Task decomposition and routing
- Sandbox execution simulation
- Guardrails (anti-abuse layer)
- Evaluation and feedback loop
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import anthropic
import os

# ═══════════════════════════════════════════
# STATE: shared data between all nodes
# ═══════════════════════════════════════════
class FrontendState(TypedDict):
    user_request: str
    figma_design: Optional[str]
    generated_code: Optional[str]
    test_result: Optional[str]
    guardrail_passed: Optional[bool]
    retry_count: int
    error: Optional[str]


# ═══════════════════════════════════════════
# GUARDRAILS: anti-abuse check (runs first)
# ═══════════════════════════════════════════
DANGEROUS_KEYWORDS = [
    "delete all", "drop table", "rm -rf",
    "format disk", "shutdown", "hack",
    "steal", "inject", "bypass security"
]

def guardrail_node(state: FrontendState) -> FrontendState:
    """
    Layer 1: Check if the request is safe before execution.
    Block dangerous or malicious instructions.
    """
    print("🛡️  Guardrail check...")
    request = state["user_request"].lower()

    for keyword in DANGEROUS_KEYWORDS:
        if keyword in request:
            print(f"🚨 BLOCKED: detected dangerous keyword '{keyword}'")
            return {
                **state,
                "guardrail_passed": False,
                "error": f"Request blocked by guardrail: '{keyword}' is not allowed."
            }

    print("✅ Guardrail passed.")
    return {**state, "guardrail_passed": True}


def should_proceed(state: FrontendState) -> str:
    """Route: if guardrail failed, stop immediately."""
    if not state.get("guardrail_passed"):
        return "blocked"
    return "proceed"


# ═══════════════════════════════════════════
# NODE 1: Figma Design (simulated)
# ═══════════════════════════════════════════
def figma_node(state: FrontendState) -> FrontendState:
    """
    Simulate Figma generating a UI design spec.
    In production: call Figma API to create or fetch a design file.
    """
    print(f"🎨 Figma: designing UI for '{state['user_request']}'...")

    # Simulated design output
    design = f"""
    Design spec for: {state['user_request']}
    - Layout: centered login form
    - Components: email input, password input, submit button
    - Colors: #FFFFFF background, #2563EB primary button
    - Font: Inter 16px
    """

    print("✅ Figma: design spec ready.")
    return {**state, "figma_design": design}


# ═══════════════════════════════════════════
# NODE 2: Claude Code Generation (real API)
# ═══════════════════════════════════════════
def claude_code_node(state: FrontendState) -> FrontendState:
    """
    Call Claude API to generate frontend code from the Figma design spec.
    Falls back to mock output if no API key is set.
    """
    print("💻 Claude Code: generating code from design spec...")

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    # Mock mode if no API key
    if not api_key:
        print("⚠️  No API key found, using mock output.")
        code = """
<form class='login-form'>
  <input type='email' placeholder='Email' />
  <input type='password' placeholder='Password' />
  <button type='submit'>Login</button>
</form>
"""
        return {**state, "generated_code": code, "error": None}

    prompt = f"""
    Based on this UI design spec, generate clean HTML + CSS code.
    Only output the code, no explanation.

    Design spec:
    {state['figma_design']}
    """

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        code = message.content[0].text
        print("✅ Claude Code: code generated.")
        return {**state, "generated_code": code, "error": None}

    except Exception as e:
        print(f"❌ Claude Code error: {e}")
        return {**state, "error": str(e)}


# ═══════════════════════════════════════════
# NODE 3: Test & Validation
# ═══════════════════════════════════════════
def test_node(state: FrontendState) -> FrontendState:
    """
    Validate the generated code.
    Check for basic HTML structure and required components.
    """
    print("🧪 Test: validating generated code...")

    code = state.get("generated_code") or ""

    if not code:
        result = "FAILED: No code was generated"
        print(f"❌ Test failed: {result}")
        return {**state, "test_result": result}

    issues = []
    if "<form" not in code and "form" not in code.lower():
        issues.append("Missing form element")
    if "input" not in code.lower():
        issues.append("Missing input fields")
    if "button" not in code.lower() and "submit" not in code.lower():
        issues.append("Missing submit button")

    if issues:
        result = f"FAILED: {', '.join(issues)}"
        print(f"❌ Test failed: {result}")
    else:
        result = "All tests passed"
        print("✅ Test passed.")

    return {**state, "test_result": result}


# ═══════════════════════════════════════════
# NODE 4: Blocked (guardrail failed)
# ═══════════════════════════════════════════
def blocked_node(state: FrontendState) -> FrontendState:
    print(f"🚫 Request blocked. Reason: {state.get('error')}")
    return state


# ═══════════════════════════════════════════
# ROUTING: retry or done?
# ═══════════════════════════════════════════
MAX_RETRIES = 2

def should_retry(state: FrontendState) -> str:
    retry_count = state.get("retry_count", 0)

    if "passed" in state.get("test_result", ""):
        return "done"

    if retry_count >= MAX_RETRIES:
        print(f"⚠️  Max retries ({MAX_RETRIES}) reached. Stopping.")
        return "done"

    print(f"🔄 Retrying... (attempt {retry_count + 1}/{MAX_RETRIES})")
    return "retry"


def increment_retry(state: FrontendState) -> FrontendState:
    return {**state, "retry_count": state.get("retry_count", 0) + 1}


# ═══════════════════════════════════════════
# BUILD THE GRAPH
# ═══════════════════════════════════════════
def build_workflow() -> StateGraph:
    workflow = StateGraph(FrontendState)

    # Add nodes
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("figma", figma_node)
    workflow.add_node("claude_code", claude_code_node)
    workflow.add_node("test", test_node)
    workflow.add_node("blocked", blocked_node)
    workflow.add_node("increment_retry", increment_retry)

    # Entry point
    workflow.set_entry_point("guardrail")

    # Guardrail routing
    workflow.add_conditional_edges(
        "guardrail",
        should_proceed,
        {
            "proceed": "figma",
            "blocked": "blocked"
        }
    )

    # Main flow
    workflow.add_edge("figma", "claude_code")
    workflow.add_edge("claude_code", "test")
    workflow.add_edge("blocked", END)

    # Retry or done
    workflow.add_conditional_edges(
        "test",
        should_retry,
        {
            "done": END,
            "retry": "increment_retry"
        }
    )
    workflow.add_edge("increment_retry", "claude_code")

    return workflow


# ═══════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════
if __name__ == "__main__":
    app = build_workflow().compile()

    # Normal request
    print("\n" + "="*50)
    print("TEST 1: Normal request")
    print("="*50)
    result = app.invoke({
        "user_request": "Build a login page with email and password",
        "figma_design": None,
        "generated_code": None,
        "test_result": None,
        "guardrail_passed": None,
        "retry_count": 0,
        "error": None
    })
    print(f"\n📄 Final result: {result['test_result']}")

    # Dangerous request (guardrail test)
    print("\n" + "="*50)
    print("TEST 2: Dangerous request (guardrail test)")
    print("="*50)
    result2 = app.invoke({
        "user_request": "rm -rf all project files",
        "figma_design": None,
        "generated_code": None,
        "test_result": None,
        "guardrail_passed": None,
        "retry_count": 0,
        "error": None
    })
    print(f"\n🚫 Blocked reason: {result2['error']}") 



