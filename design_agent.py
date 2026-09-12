"""
InterioOS AI - Member 1: Design Agent
Tech Stack: Python, LangGraph, Anthropic Claude API

Role & Responsibility:
1. Ek Python function jo user ka requirement leta hai.
2. Claude API ko prompt bhejta hai: "is requirement ke liye design concept do".
3. Response ko LangGraph State mein save karta hai taake downstream agents (Cost Estimator, BOQ, Vendor, etc.) isko access kar sakein.
"""

import os
from typing import Optional, TypedDict, Dict, Any
from dotenv import load_dotenv
import anthropic
from langgraph.graph import StateGraph, END

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
    user_requirement: str        # Client requirement input
    budget: Optional[str]        # Optional budget information
    room_type: Optional[str]     # Optional room type
    style: Optional[str]         # Optional style preference
    design_concept: Optional[str]# Claude API se generate hone wala design concept (Saved here)
    status: Optional[str]        # Workflow status (e.g. 'concept_generated', 'error')
    error: Optional[str]         # Error message if any


# ==========================================
# 2. DESIGN AGENT FUNCTION (LANGGRAPH NODE)
# ==========================================
def design_agent_node(state: InterioOSState) -> InterioOSState:
    """
    Member 1 Design Agent Node:
    - User requirement state se leta hai.
    - Claude API ko prompt bhejta hai: 'is requirement ke liye design concept do'.
    - Response ko state mein 'design_concept' field mein save karta hai.
    """
    user_requirement = state.get("user_requirement", "").strip()
    if not user_requirement:
        return {
            **state,
            "error": "User requirement cannot be empty.",
            "status": "failed"
        }

    # API Key retrieval
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            **state,
            "error": "ANTHROPIC_API_KEY is not configured in .env or environment.",
            "status": "failed"
        }

    # Claude API Client
    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Prompt: Claude ko interior design concept tayyar karne ka instruction
    budget_info = f"Budget: {state.get('budget')}\n" if state.get("budget") else ""
    room_info = f"Room Type: {state.get('room_type')}\n" if state.get("room_type") else ""
    style_info = f"Style Preference: {state.get('style')}\n" if state.get("style") else ""

    system_prompt = (
        "You are an expert Lead Interior Designer for InterioOS AI, a multi-agent interior design system.\n"
        "Your task is to take the client requirement and generate a comprehensive, highly practical, and aesthetic interior design concept.\n\n"
        "Please format the design concept clearly in Markdown with the following sections:\n"
        "1. **Concept Summary & Visual Theme**: Design style, ambiance, and mood.\n"
        "2. **Spatial Layout & Zoning**: Space optimization, furniture layout, and functionality.\n"
        "3. **Color Palette & Material Direction**: Primary, secondary, and accent colors, textures, wall & flooring finishes.\n"
        "4. **Lighting Strategy**: Ambient, task, and accent lighting ideas.\n"
        "5. **Key Furniture & Decor Elements**: Essential items, statement pieces, fixtures.\n"
        "6. **Recommendations for Downstream Estimation**: Practical suggestions for material quantification and budgeting."
    )

    user_prompt = (
        f"is requirement ke liye design concept do:\n\n"
        f"Requirement: \"{user_requirement}\"\n"
        f"{room_info}"
        f"{style_info}"
        f"{budget_info}"
    )

    try:
        # Claude API call
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract generated response text
        concept_text = "".join([block.text for block in response.content if block.type == "text"]).strip()

        # Save response in LangGraph state
        return {
            **state,
            "design_concept": concept_text,
            "status": "concept_generated",
            "error": None
        }

    except Exception as e:
        return {
            **state,
            "error": f"Claude API call failed: {str(e)}",
            "status": "failed"
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

    # Workflow entry point and termination
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
        api_key: Optional Anthropic API Key (agar pass kiya jaye toh env mein set hota hai).

    Returns:
        InterioOSState: Updated state dictionary containing 'design_concept'.
    """
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    initial_state: InterioOSState = {
        "user_requirement": requirement,
        "budget": budget,
        "room_type": room_type,
        "style": style,
        "design_concept": None,
        "status": "pending",
        "error": None
    }

    # Execute LangGraph workflow
    final_state: InterioOSState = design_graph.invoke(initial_state)
    return final_state


# CLI Test
if __name__ == "__main__":
    print("--- InterioOS AI: Member 1 - Design Agent (LangGraph) ---")
    test_requirement = "Design a modern bedroom for a client within a budget of Rs. 8 lakh."
    print(f"Test Requirement: {test_requirement}\n")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[NOTE] ANTHROPIC_API_KEY not found in .env. Please set it before running live API calls.")
    else:
        result_state = generate_design_concept(test_requirement, budget="Rs. 8 Lakh")
        if result_state.get("error"):
            print(f"[ERROR] {result_state['error']}")
        else:
            print("=== Design Concept Saved in State ===")
            print(result_state["design_concept"])
