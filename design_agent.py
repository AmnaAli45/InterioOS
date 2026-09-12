"""
InterioOS AI - Member 1: Design Agent
Tech Stack: Python, Streamlit, LangGraph, OpenRouter / Groq / Claude API

Role & Responsibility:
1. Ek Python function jo user ka requirement leta hai.
2. LLM API (OpenRouter, Groq, Claude) ko prompt bhejta hai: "is requirement ke liye design concept do".
3. Response ko LangGraph State mein save karta hai taake downstream team agents (Member 2 Cost Estimator, Member 3 BOQ, etc.) isko access kar sakein.
"""

import os
import json
import requests
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
    provider: Optional[str]        # 'openrouter', 'groq', or 'claude'
    model: Optional[str]           # Model name used
    design_concept: Optional[str]  # Generated design concept (Saved here in state)
    status: Optional[str]          # Workflow status ('concept_generated', 'failed')
    error: Optional[str]           # Error message if any


def detect_provider(api_key: str, requested_provider: Optional[str] = None) -> str:
    """Auto-detect provider based on API key prefix if not explicitly specified."""
    key = (api_key or "").strip()
    if key.startswith("sk-or-v1-") or key.startswith("sk-or-"):
        return "openrouter"
    if key.startswith("gsk_"):
        return "groq"
    if key.startswith("sk-ant-"):
        return "claude"
    return requested_provider or "openrouter"


# ==========================================
# 2. DESIGN AGENT FUNCTION (LANGGRAPH NODE)
# ==========================================
def design_agent_node(state: InterioOSState) -> InterioOSState:
    """
    Member 1 Design Agent Node:
    - User requirement state se leta hai.
    - LLM API (OpenRouter, Groq, Claude) ko prompt bhejta hai: 'is requirement ke liye design concept do'.
    - Response ko state mein 'design_concept' field mein save karta hai.
    """
    user_requirement = state.get("user_requirement", "").strip()
    if not user_requirement:
        return {
            **state,
            "error": "User requirement cannot be empty.",
            "status": "failed"
        }

    # API Keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # Determine provider
    raw_provider = state.get("provider") or os.getenv("LLM_PROVIDER") or ""
    active_key = openrouter_key or groq_key or anthropic_key or ""
    provider = detect_provider(active_key, raw_provider)

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
    used_model = state.get("model")

    # --- 1. OPENROUTER PATH ---
    if provider == "openrouter" or (openrouter_key and not groq_key and not anthropic_key):
        if not openrouter_key:
            return {
                **state,
                "error": "OPENROUTER_API_KEY is missing. Please enter your OpenRouter key (sk-or-v1-...).",
                "status": "failed"
            }

        model = used_model or os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")

        try:
            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://interioos.ai",
                "X-Title": "InterioOS AI"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }

            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            data = resp.json()

            if resp.status_code != 200 or "error" in data:
                err_msg = data.get("error", {}).get("message", f"HTTP {resp.status_code}")
                return {
                    **state,
                    "error": f"OpenRouter API Error: {err_msg}",
                    "status": "failed"
                }

            concept_text = data["choices"][0]["message"]["content"].strip()
            used_model = model

        except Exception as e:
            return {
                **state,
                "error": f"OpenRouter request failed: {str(e)}",
                "status": "failed"
            }

    # --- 2. GROQ PATH ---
    elif provider == "groq":
        if not groq_key:
            return {
                **state,
                "error": "GROQ_API_KEY missing. Groq keys start with 'gsk_'. If you have an OpenRouter key ('sk-or-v1-'), please select OpenRouter.",
                "status": "failed"
            }
        if not GROQ_AVAILABLE:
            return {
                **state,
                "error": "Groq library not installed.",
                "status": "failed"
            }

        model = used_model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        try:
            client = Groq(api_key=groq_key)
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
            used_model = model

        except Exception as e:
            return {
                **state,
                "error": f"Groq API call failed: {str(e)}",
                "status": "failed"
            }

    # --- 3. CLAUDE PATH ---
    else:
        if not anthropic_key:
            return {
                **state,
                "error": "ANTHROPIC_API_KEY missing. Anthropic keys start with 'sk-ant-'.",
                "status": "failed"
            }
        if not ANTHROPIC_AVAILABLE:
            return {
                **state,
                "error": "Anthropic library not installed.",
                "status": "failed"
            }

        model = used_model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        try:
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            concept_text = "".join([block.text for block in response.content if block.type == "text"]).strip()
            used_model = model

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
        "provider": provider,
        "model": used_model,
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
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> InterioOSState:
    """
    User ka requirement leta hai, LangGraph graph execute karta hai,
    aur updated state (jisme design concept saved hota hai) return karta hai.
    """
    resolved_provider = provider or "openrouter"

    if api_key:
        # Auto-detect if key was supplied
        resolved_provider = detect_provider(api_key, provider)
        if resolved_provider == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif resolved_provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        else:
            os.environ["ANTHROPIC_API_KEY"] = api_key

    initial_state: InterioOSState = {
        "user_requirement": requirement,
        "budget": budget,
        "room_type": room_type,
        "style": style,
        "provider": resolved_provider,
        "model": model,
        "design_concept": None,
        "status": "pending",
        "error": None
    }

    # Execute LangGraph workflow
    final_state: InterioOSState = design_graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    print("--- InterioOS AI: Member 1 - Design Agent (LangGraph) ---")
    test_req = "Design a modern bedroom for a client within a budget of Rs. 8 lakh."
    res = generate_design_concept(test_req, budget="Rs. 8 Lakh")
    print(res)
