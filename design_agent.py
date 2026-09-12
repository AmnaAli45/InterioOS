"""
InterioOS AI - Member 1: Design Agent
Tech Stack: Python, Streamlit, LangGraph, Groq / Claude API

Role & Responsibility:
1. Ek Python function jo user ka requirement leta hai.
2. LLM API (Groq LLaMA-3.3 / Claude) ko prompt bhejta hai: "is requirement ke liye design concept do".
3. Response ko LangGraph State mein save karta hai taake downstream team agents (Member 2 Cost Estimator, Member 3 BOQ, etc.) isko access kar sakein.
"""

import os
from typing import Optional, TypedDict, Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Optional imports with graceful availability
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Load environment variables
load_dotenv()


# ==========================================
# 1. LANGGRAPH STATE DEFINITION
# ==========================================
class InterioOSState(TypedDict, total=False):
    """
    Multi-Agent Shared State Schema for InterioOS.
    Member 1 (Design Agent) inputs 'user_requirement' and populates 'design_concept'.
    """
    user_requirement: str          # Client requirement input
    budget: Optional[str]          # Optional budget information
    room_type: Optional[str]       # Optional room type
    style: Optional[str]           # Optional style preference
    provider: Optional[str]        # 'groq' or 'claude'
    design_concept: Optional[str]  # Generated design concept (Saved here in state)
    status: Optional[str]          # Workflow status ('concept_generated', 'failed')
    error: Optional[str]           # Error message if any


# ==========================================
# 2. DESIGN AGENT FUNCTION (LANGGRAPH NODE)
# ==========================================
def design_agent_node(state: InterioOSState) -> InterioOSState:
    """
    Member 1 Design Agent Node:
    - User requirement state se leta hai.
    - Groq / Claude API ko prompt bhejta hai: 'is requirement ke liye design concept do'.
    - Response ko state mein 'design_concept' field mein save karta hai.
    """
    user_requirement = state.get("user_requirement", "").strip()
    if not user_requirement:
        return {
            **state,
            "error": "User requirement cannot be empty.",
            "status": "failed"
        }

    provider = (state.get("provider") or os.getenv("LLM_PROVIDER") or "groq").lower()
    groq_api_key = os.getenv("GROQ_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    # Budget & Room context
    budget_info = f"Budget: {state.get('budget')}\n" if state.get("budget") else ""
    room_info = f"Room Type: {state.get('room_type')}\n" if state.get("room_type") else ""
    style_info = f"Style Preference: {state.get('style')}\n" if state.get("style") else ""

    system_prompt = (
        "You are an expert Lead Interior Designer for InterioOS AI, a multi-agent interior design system.\n"
        "Your task is to take the client requirement and generate a comprehensive, highly practical, and aesthetic interior design concept.\n\n"
        "Please format the design concept clearly in Markdown with the following sections:\n"
        "1. **Concept Summary & Visual Theme**: Design style, ambiance, color harmony, and mood.\n"
        "2. **Spatial Layout & Zoning**: Space optimization, furniture layout, traffic flow, and ergonomics.\n"
        "3. **Color Palette & Material Direction**: Primary, secondary, and accent colors, textures, wall & flooring finishes.\n"
        "4. **Lighting Strategy**: Ambient, task, and accent lighting ideas.\n"
        "5. **Key Furniture & Decor Elements**: Essential items, statement pieces, and customized fixtures.\n"
        "6. **Recommendations for Downstream Estimation**: Practical suggestions for material quantification, durability, and budgeting."
    )

    user_prompt = (
        f"is requirement ke liye design concept do:\n\n"
        f"Requirement: \"{user_requirement}\"\n"
        f"{room_info}"
        f"{style_info}"
        f"{budget_info}"
    )

    concept_text = ""

    # --- EXECUTION PATH: GROQ (Primary/Default) ---
    if provider == "groq" or (groq_api_key and not anthropic_api_key):
        if not groq_api_key:
            return {
                **state,
                "error": "GROQ_API_KEY missing. Please set GROQ_API_KEY in .env or enter it in the app sidebar.",
                "status": "failed"
            }
        if not GROQ_AVAILABLE:
            return {
                **state,
                "error": "Groq package not installed. Run 'pip install groq'.",
                "status": "failed"
            }

        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        try:
            client = Groq(api_key=groq_api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=0.7,
                max_tokens=4096,
            )
            concept_text = chat_completion.choices[0].message.content.strip()

        except Exception as e:
            return {
                **state,
                "error": f"Groq API call failed: {str(e)}",
                "status": "failed"
            }

    # --- EXECUTION PATH: CLAUDE (Anthropic Fallback) ---
    else:
        if not anthropic_api_key:
            return {
                **state,
                "error": "ANTHROPIC_API_KEY missing. Please set ANTHROPIC_API_KEY or GROQ_API_KEY.",
                "status": "failed"
            }
        if not ANTHROPIC_AVAILABLE:
            return {
                **state,
                "error": "Anthropic package not installed. Run 'pip install anthropic'.",
                "status": "failed"
            }

        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        try:
            client = anthropic.Anthropic(api_key=anthropic_api_key)
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            concept_text = "".join([block.text for block in response.content if block.type == "text"]).strip()

        except Exception as e:
            return {
                **state,
                "error": f"Claude API call failed: {str(e)}",
                "status": "failed"
            }

    # Save response into LangGraph state
    return {
        **state,
        "design_concept": concept_text,
        "status": "concept_generated",
        "error": None
    }


# ==========================================
# 3. LANGGRAPH WORKFLOW BUILDER
# ==========================================
def build_design_graph():
    """
    LangGraph StateGraph build karta hai.
    Design Agent node add karke graph compile karta hai.
    """
    workflow = StateGraph(InterioOSState)

    # Add Design Agent Node
    workflow.add_node("design_agent", design_agent_node)

    # Entry point and termination
    workflow.set_entry_point("design_agent")
    workflow.add_edge("design_agent", END)

    return workflow.compile()


# Compile graph for reuse
design_graph = build_design_graph()


# ==========================================
# 4. CONVENIENCE FUNCTION
# ==========================================
def generate_design_concept(
    requirement: str,
    budget: Optional[str] = None,
    room_type: Optional[str] = None,
    style: Optional[str] = None,
    provider: str = "groq",
    api_key: Optional[str] = None
) -> InterioOSState:
    """
    User ka requirement leta hai, LangGraph graph execute karta hai,
    aur updated state (jisme design concept saved hota hai) return karta hai.

    Args:
        requirement: User ka design requirement (e.g. 'Design a modern bedroom within Rs. 8 lakh').
        budget: Optional budget.
        room_type: Optional room type.
        style: Optional style preference.
        provider: 'groq' (default) or 'claude'.
        api_key: Optional API Key for the chosen provider.

    Returns:
        InterioOSState: Updated state dictionary containing 'design_concept'.
    """
    if api_key:
        if provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        else:
            os.environ["ANTHROPIC_API_KEY"] = api_key

    initial_state: InterioOSState = {
        "user_requirement": requirement,
        "budget": budget,
        "room_type": room_type,
        "style": style,
        "provider": provider,
        "design_concept": None,
        "status": "pending",
        "error": None
    }

    # Execute LangGraph workflow
    final_state: InterioOSState = design_graph.invoke(initial_state)
    return final_state


# CLI Test
if __name__ == "__main__":
    print("--- InterioOS AI: Member 1 - Design Agent (LangGraph + Groq) ---")
    test_req = "Design a modern bedroom for a client within a budget of Rs. 8 lakh."
    print(f"Test Requirement: {test_req}\n")

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("[NOTE] GROQ_API_KEY not found in .env. Please set GROQ_API_KEY before running live.")
    else:
        print("Running LangGraph workflow with Groq...")
        res = generate_design_concept(test_req, budget="Rs. 8 Lakh", provider="groq")
        if res.get("error"):
            print(f"[ERROR] {res['error']}")
        else:
            print("=== Design Concept Saved in State ===")
            print(res["design_concept"][:400] + "...\n[Full concept saved in state]")
