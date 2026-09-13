"""
InterioOS AI - Member 4: Timeline Agent (Project Execution Schedule)
Tech Stack: Python, Anthropic (Claude) / Groq fallback, LangGraph

Role & Responsibility:
1. Design Concept (Member 1) + Cost & Scope (Member 2 / 3) ka output state se lena.
2. Claude se prompt pochna: "is project ka simple timeline banao — kaunsa kaam kab hoga".
3. Response ko LangGraph State mein save karna:
   - state["timeline_markdown"]: Formatted phase-by-phase execution timeline.
   - state["estimated_duration"]: Overall estimated project duration.
   - state["timeline_status"]: 'completed' | 'failed'
"""

import os
import re
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def extract_duration_from_text(text: str) -> str:
    """Extracts overall project duration string from LLM output if present."""
    # Look for common duration patterns like "4-5 weeks", "30 days", "3 to 4 weeks", etc.
    match = re.search(
        r"(?:total\s+(?:estimated\s+)?duration|overall\s+timeline|timeline)\s*[:–-]\s*([^\n\r#*]+)",
        text,
        re.IGNORECASE
    )
    if match:
        val = match.group(1).strip().rstrip(".*#")
        if val:
            return val
    
    # Fallback search for week/day patterns
    pattern = re.search(r"(\d+(?:\s*[-–to]+\s*\d+)?\s*(?:weeks|days|months))", text, re.IGNORECASE)
    if pattern:
        return pattern.group(1).strip()
    
    return "4 to 5 Weeks (Approx. 30 Days)"


def query_claude(prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Queries Anthropic Claude API."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    messages_payload: Any = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=model,
        max_tokens=3000,
        system=system_prompt,
        messages=messages_payload
    )
    text_parts = [getattr(block, "text", "") for block in response.content]
    return "".join(text_parts).strip()


def query_groq_fallback(prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Fallback query to Groq when Claude key is unavailable."""
    from groq import Groq
    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        model=model,
        temperature=0.3,
        max_tokens=3000,
    )
    raw_text = chat_completion.choices[0].message.content or ""
    return raw_text.strip()


def timeline_agent(state: Any) -> Any:
    """
    Member 4 - Timeline Agent Node:
    1. Ingests Design output (design_concept) and Cost output (cost/items/budget).
    2. Sends prompt to Claude: 'is project ka simple timeline banao — kaunsa kaam kab hoga'.
    3. Saves generated timeline schedule and duration into LangGraph state.
    """
    # 1. Design + Cost ka output lena
    design_concept = (
        state.get("design_concept") or
        state.get("user_requirement") or
        state.get("requirement") or
        ""
    )

    cost_data = state.get("cost") or {}
    items_data = state.get("items") or cost_data.get("items") or []
    budget = state.get("budget") or cost_data.get("budget") or "Not specified"
    estimated_cost = cost_data.get("estimated_cost", "Pending")

    if not design_concept.strip():
        state["timeline_status"] = "failed"
        state["error"] = "No design concept or project requirement found to build timeline."
        return state

    # Format item scope summary for the LLM
    items_summary_lines = []
    if items_data:
        for it in items_data:
            if isinstance(it, dict):
                name = it.get("name") or it.get("item", "Item")
                qty = it.get("quantity", 1)
                unit = it.get("unit", "")
                items_summary_lines.append(f"- {name}: {qty} {unit}")
    items_scope_text = "\n".join(items_summary_lines) if items_summary_lines else "Standard finishes, carpentry, electrical & loose furniture."

    # System prompt for Interior Project Manager
    system_prompt = (
        "You are an expert Interior Project Execution Manager & Scheduling Specialist for InterioOS AI.\n"
        "Your task is to take the interior design concept and estimated cost/material scope, then create a clear, realistic, and practical project execution timeline.\n\n"
        "Format the timeline in clean, professional Markdown with the following structure:\n\n"
        "### ⏱️ Overall Project Duration\n"
        "State the total estimated time (e.g., 'Total Estimated Duration: 4 to 5 Weeks (Approx. 30 Days)').\n\n"
        "### 📅 Sequential Phase-by-Phase Timeline (Kaunsa Kaam Kab Hoga)\n"
        "Break down the project chronologically into sequential phases with practical day/week ranges:\n"
        "- **Phase 1: Site Prep & Procurement (Days 1–3)**: Site survey, material orders, site protection.\n"
        "- **Phase 2: Civil, Electrical & False Ceiling (Days 4–8)**: Wiring conduits, switch boxes, false ceiling framing & gypsum.\n"
        "- **Phase 3: Flooring & Wall Prep (Days 9–14)**: Tile/wooden flooring installation, base wall putty & primer.\n"
        "- **Phase 4: Carpentry & Fixed Woodwork (Days 15–22)**: Modular wardrobes, bed framing, storage units.\n"
        "- **Phase 5: Wall Finishes & Painting (Days 23–27)**: Final coats of emulsion paint, wallpaper accent wall.\n"
        "- **Phase 6: Fixtures, Loose Furniture & Decor (Days 28–30)**: Lighting installation, loose furniture placement, curtains.\n"
        "- **Phase 7: Deep Cleaning, Snag List & Handover (Days 31–32)**: Final quality audit, touch-ups, site handover.\n\n"
        "### ⚠️ Critical Dependencies & Milestones\n"
        "Highlight 3-4 essential dependencies (e.g. flooring must cure before heavy carpentry; painting after woodwork sanding; final fixtures after painting)."
    )

    # User prompt incorporating the exact requested phrase
    user_prompt = (
        f"is project ka simple timeline banao — kaunsa kaam kab hoga:\n\n"
        f"--- PROJECT SCOPE & DESIGN ---\n"
        f"Design Concept: {design_concept}\n\n"
        f"--- COST & MATERIAL SCOPE ---\n"
        f"Project Budget: Rs. {budget}\n"
        f"Estimated Cost: Rs. {estimated_cost}\n"
        f"Materials & Key Items:\n"
        f"{items_scope_text}\n"
        f"--- END PROJECT SCOPE ---"
    )

    # API Credentials: Claude (Primary) with Groq (Fallback)
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    response_text = ""
    llm_provider = ""

    try:
        if anthropic_api_key:
            llm_provider = "Claude"
            model = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            response_text = query_claude(user_prompt, system_prompt, model, anthropic_api_key)
        elif groq_api_key:
            llm_provider = "Groq (Fallback)"
            model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
            response_text = query_groq_fallback(user_prompt, system_prompt, model, groq_api_key)
        else:
            state["timeline_status"] = "failed"
            state["error"] = "Neither ANTHROPIC_API_KEY nor GROQ_API_KEY is configured in .env."
            return state

        # Extract duration metric
        duration = extract_duration_from_text(response_text)

        # 3. Response state mein save karna
        state["timeline_markdown"] = response_text
        state["estimated_duration"] = duration
        state["timeline_status"] = "completed"
        state["timeline_engine"] = llm_provider
        state["error"] = None

    except Exception as e:
        state["timeline_status"] = "failed"
        state["error"] = f"Timeline generation failed via {llm_provider or 'LLM'}: {str(e)}"

    return state


def timeline_agent_node(state: Any) -> Any:
    """LangGraph node alias for timeline_agent."""
    return timeline_agent(state)


if __name__ == "__main__":
    print("--- InterioOS AI: Member 4 - Timeline Agent ---")
    mock_state = {
        "design_concept": "Modern Contemporary Master Bedroom with wooden flooring, false ceiling, modular wardrobe, bed, and warm LED lighting.",
        "budget": 800000,
        "cost": {
            "estimated_cost": 364440,
            "budget": 800000,
            "status": "Within Budget"
        },
        "items": [
            {"name": "Paint", "quantity": 200, "unit": "sqft"},
            {"name": "Flooring", "quantity": 168, "unit": "sqft"},
            {"name": "Bed", "quantity": 1, "unit": "pcs"},
            {"name": "Wardrobe", "quantity": 1, "unit": "pcs"},
            {"name": "Side Table", "quantity": 2, "unit": "pcs"},
            {"name": "LED Light", "quantity": 8, "unit": "pcs"},
            {"name": "Curtain", "quantity": 1, "unit": "pcs"}
        ]
    }

    result = timeline_agent(mock_state)
    if result.get("error"):
        print(f"[ERROR]: {result.get('error')}")
    else:
        print(f"[SUCCESS] Timeline generated via {result.get('timeline_engine')}!")
        print(f"Duration: {result.get('estimated_duration')}\n")
        print((result.get("timeline_markdown") or "")[:500] + "...\n")
