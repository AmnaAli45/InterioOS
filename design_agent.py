"""
InterioOS AI - Member 1: Design Agent
Tech Stack: Python, Streamlit, LangGraph, Groq API (Ultra-Fast)

Role & Responsibility:
1. Ek Python function jo user ka requirement leta hai.
2. Groq API ko prompt bhejta hai: "is requirement ke liye design concept do".
3. Response ko LangGraph State mein save karta hai taake downstream team agents (Member 2 Cost Estimator, Member 3 BOQ, etc.) isko access kar sakein.
"""

import os
from typing import Optional, TypedDict, Dict, Any, List, cast
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END

# Load environment variables from .env
load_dotenv()

DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


# ==========================================
# 1. LANGGRAPH STATE DEFINITION
# ==========================================
class InterioOSState(TypedDict, total=False):
    """
    Multi-Agent Shared State Schema for InterioOS.
    Shared across all 5 Agents:
    - Member 1: Design Agent (design_concept)
    - Member 3: BOQ Agent (boq_markdown, items, boq_status)
    - Member 2: Cost Agent (cost)
    - Member 4: Timeline Agent (timeline_markdown, estimated_duration, timeline_status)
    - Member 5: Coordinator Agent (final_report, coordinator_status, coordinator_engine)
    """
    user_requirement: str          # Client requirement input
    budget: Optional[str]          # Optional budget information
    room_type: Optional[str]       # Optional room type
    style: Optional[str]           # Optional style preference
    model: Optional[str]           # Model name used
    design_concept: Optional[str]  # Generated design concept (Member 1 Output)
    boq_markdown: Optional[str]    # Generated BOQ / Material list in Markdown (Member 3 Output)
    items: Optional[List[Dict[str, Any]]] # Structured items list for downstream cost estimation (Member 3 Output)
    boq_status: Optional[str]      # BOQ status ('completed', 'failed')
    boq_engine: Optional[str]      # BOQ engine used
    cost: Optional[Dict[str, Any]] # Cost calculation breakdown (Member 2 Output)
    timeline_markdown: Optional[str] # Project execution schedule in Markdown (Member 4 Output)
    estimated_duration: Optional[str] # Total project duration (e.g. '4-5 Weeks', '30 Days')
    timeline_status: Optional[str] # Timeline status ('completed', 'failed')
    timeline_engine: Optional[str] # LLM engine used for timeline
    final_report: Optional[str]    # Combined Master Project Report (Member 5 Output)
    coordinator_status: Optional[str] # Coordinator status ('completed', 'failed')
    coordinator_engine: Optional[str] # LLM engine used for coordinator report
    status: Optional[str]          # Overall workflow status
    error: Optional[str]           # Error message if any


# ==========================================
# 2. DESIGN AGENT FUNCTION (LANGGRAPH NODE)
# ==========================================
def design_agent_node(state: InterioOSState) -> InterioOSState:
    """
    Member 1 Design Agent Node:
    - User requirement state se leta hai.
    - Groq API ko prompt bhejta hai: 'is requirement ke liye design concept do'.
    - Response ko state mein 'design_concept' field mein save karta hai.
    """
    user_requirement = state.get("user_requirement", "").strip()
    if not user_requirement:
        return {
            **state,
            "error": "User requirement cannot be empty.",
            "status": "failed"
        }

    # Groq API Key retrieval
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return {
            **state,
            "error": "GROQ_API_KEY is missing. Please set GROQ_API_KEY in your .env file.",
            "status": "failed"
        }

    model = state.get("model") or os.getenv("GROQ_MODEL") or DEFAULT_GROQ_MODEL

    # Prompt context
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

    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.7,
            max_tokens=2500,
        )

        raw_content = chat_completion.choices[0].message.content or ""
        concept_text = raw_content.strip()

        # Save response into LangGraph state
        return {
            **state,
            "design_concept": concept_text,
            "model": model,
            "status": "concept_generated",
            "error": None
        }

    except Exception as e:
        return {
            **state,
            "error": f"Groq API call failed: {str(e)}",
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
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> InterioOSState:
    """
    User ka requirement leta hai, LangGraph graph execute karta hai,
    aur updated state (jisme design concept saved hota hai) return karta hai.
    """
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    initial_state: InterioOSState = {
        "user_requirement": requirement,
        "budget": budget,
        "room_type": room_type,
        "style": style,
        "model": model or DEFAULT_GROQ_MODEL,
        "design_concept": None,
        "status": "pending",
        "error": None
    }

    # Execute LangGraph workflow
    final_state: InterioOSState = cast(InterioOSState, design_graph.invoke(initial_state))
    return final_state


if __name__ == "__main__":
    print("--- InterioOS AI: Member 1 - Design Agent (LangGraph + Groq) ---")
    test_req = "Design a modern bedroom for a client within a budget of Rs. 8 lakh."
    res = generate_design_concept(test_req, budget="Rs. 8 Lakh")
    if res.get("error"):
        print(f"[ERROR] {res.get('error')}")
    else:
        print("=== Design Concept Saved in State (Generated in < 2 seconds!) ===")
        print((res.get("design_concept") or "")[:300] + "...\n[Success!]")
