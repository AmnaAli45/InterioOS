"""
InterioOS AI - Member 5: Coordinator Agent + LangGraph Connection
Tech Stack: Python, LangGraph, Anthropic (Claude) / Groq API

Role & Responsibility:
1. Sab 4 agents ka output state se collect karna:
   - Member 1: Design Agent (design_concept)
   - Member 3: BOQ Agent (boq_markdown, items)
   - Member 2: Cost Agent (cost breakdown & budget analysis)
   - Member 4: Timeline Agent (timeline_markdown, estimated_duration)
2. Ek comprehensive final combined report banana (Executive Summary + Design + BOQ + Cost + Timeline + Milestones).
3. LangGraph mein sab 5 agents ko connect karna (add_node, add_edge, START, END).
4. Full pipeline execution ko orchestrate aur test karna.
"""

import os
import datetime
from typing import Any, Dict, List, Optional, cast
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# Import shared state and upstream agents
from design_agent import InterioOSState, design_agent_node
from agents.boq_agent import boq_agent_node
from agents.cost_agent import cost_agent
from agents.timeline_agent import timeline_agent_node

# Load environment variables
load_dotenv()

DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def query_claude(prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Queries Anthropic Claude API for executive report synthesis."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    messages_payload: Any = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=model,
        max_tokens=3500,
        system=system_prompt,
        messages=messages_payload
    )
    text_parts = [getattr(block, "text", "") for block in response.content]
    return "".join(text_parts).strip()


def query_groq_fallback(prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Fallback query to Groq for executive synthesis."""
    from groq import Groq
    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        model=model,
        temperature=0.3,
        max_tokens=3500,
    )
    raw_text = chat_completion.choices[0].message.content or ""
    return raw_text.strip()


def synthesize_fallback_executive_summary(state: InterioOSState) -> str:
    """
    Creates an algorithmic, high quality executive synthesis when LLM APIs are offline.
    """
    req = state.get("user_requirement", "Interior Design Project")
    budget_raw = state.get("budget", "Not specified")
    room_type = state.get("room_type", "Standard Living Area")
    style = state.get("style", "Modern")

    cost_info = state.get("cost") or {}
    est_cost = cost_info.get("estimated_cost", 0)
    budget_val = cost_info.get("budget", 0)
    status_budget = cost_info.get("status", "Pending")
    rem_budget = cost_info.get("remaining_budget", 0)

    duration = state.get("estimated_duration", "4-5 Weeks (Approx. 30 Days)")
    items_count = len(state.get("items") or cost_info.get("items") or [])

    summary = (
        f"### 🎯 Project Overview & Executive Summary\n\n"
        f"InterioOS Multi-Agent Intelligence System has synthesized a turnkey execution blueprint for the client request: **\"{req}\"**.\n\n"
        f"- **Project Scope**: {room_type} ({style} Style)\n"
        f"- **Allocated Client Budget**: Rs. {budget_val:,.0f} ({budget_raw})\n"
        f"- **Total Estimated Cost**: Rs. {est_cost:,.0f}\n"
        f"- **Financial Health**: **{status_budget}** (Variance / Reserve: Rs. {rem_budget:,.0f})\n"
        f"- **Estimated Turnaround Duration**: **{duration}**\n"
        f"- **Billed Quantified Items**: {items_count} verified material/furniture components\n\n"
        f"#### 🔍 Key Takeaways & Coordinator Recommendations:\n"
        f"1. **Design Feasibility**: Aesthetic concept aligns directly with functional zoning and spatial ergonomics.\n"
        f"2. **Budget Optimization**: The estimated expenditure is within healthy parameters with financial buffer.\n"
        f"3. **Execution Readiness**: Material specifications (BOQ) and phase scheduling are synchronized to prevent contractor bottlenecks."
    )
    return summary


def build_final_master_report(
    state: InterioOSState,
    executive_synthesis: Optional[str] = None
) -> str:
    """
    Combines all 4 upstream agents' outputs and the Coordinator's executive synthesis
    into a comprehensive, executive-ready Master Project Report.
    """
    today_str = datetime.date.today().strftime("%B %d, %Y")
    req = state.get("user_requirement", "Turnkey Interior Design")
    room_type = state.get("room_type", "Residential Space")
    style = state.get("style", "Modern Contemporary")
    budget_raw = state.get("budget", "N/A")

    cost_info = state.get("cost") or {}
    est_cost = cost_info.get("estimated_cost", 0)
    budget_val = cost_info.get("budget", 0)
    status_budget = cost_info.get("status", "Evaluated")
    remaining = cost_info.get("remaining_budget", 0)

    duration = state.get("estimated_duration", "4 to 5 Weeks")
    design_concept = state.get("design_concept") or "*Design concept pending or in draft.*"
    boq_markdown = state.get("boq_markdown") or "*BOQ material table not generated.*"
    timeline_markdown = state.get("timeline_markdown") or "*Timeline schedule not generated.*"

    exec_summary = executive_synthesis or synthesize_fallback_executive_summary(state)

    report = f"""# 🏛️ INTERIOOS AI — MASTER PROJECT DOSSIER & FINAL REPORT

**Generated by**: InterioOS Multi-Agent Coordinator (Member 5)  
**Date**: {today_str}  
**Project Name**: {room_type} — {style}  
**Client Requirement**: *\"{req}\"*  
**Budget Allocation**: Rs. {budget_val:,.0f} ({budget_raw})  

---

## 📊 1. Executive Summary & Multi-Agent Synthesis
{exec_summary}

---

## 🎨 2. Architectural & Interior Design Concept (Member 1: Design Agent)
{design_concept}

---

## 🧱 3. Bill of Quantities (BOQ) & Material Specification (Member 3: BOQ Agent)
{boq_markdown}

---

## 💰 4. Financial & Budget Feasibility Analysis (Member 2: Cost Estimator)
| Financial Metric | Amount (PKR / INR) | Status / Notes |
| :--- | :--- | :--- |
| **Client Budget Target** | Rs. {budget_val:,.0f} | Target limit set by client |
| **Total Estimated Material Cost** | Rs. {est_cost:,.0f} | Calculated from unit rates & quantities |
| **Variance / Reserve Budget** | Rs. {remaining:,.0f} | {'Surplus buffer available' if remaining >= 0 else 'Deficit alert'} |
| **Budget Health Status** | **{status_budget}** | Automated pricing validation |

"""

    # Add item cost table if available
    cost_items = cost_info.get("items", [])
    if cost_items:
        report += "### 📋 Itemized Cost Breakdown\n"
        report += "| Item Name | Quantity | Unit | Unit Price | Total Cost | Pricing Status |\n"
        report += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for it in cost_items:
            item_name = it.get("item", "Item")
            qty = it.get("quantity", 1)
            unit = it.get("unit", "pcs")
            u_price = it.get("unit_price", 0)
            t_cost = it.get("total", 0)
            status_item = it.get("status", "OK")
            report += f"| {item_name} | {qty} | {unit} | Rs. {u_price:,.0f} | Rs. {t_cost:,.0f} | {status_item} |\n"
        report += "\n"

    report += f"""---

## 📅 5. Project Execution Schedule & Timeline (Member 4: Timeline Agent)
**Estimated Turnaround Duration**: `{duration}`

{timeline_markdown}

---

## 🛡️ 6. Risk Mitigation & Project Coordinator Milestones (Member 5: Coordinator)
1. **Material Lead Times**: Procurement for custom modular carpentry and tiles should commence during Phase 1 site prep.
2. **Quality Checkpoints**:
   - **Gate 1**: Civil and conduit electrical sign-off before false ceiling closure.
   - **Gate 2**: Flooring curing and surface leveling before carpentry delivery.
   - **Gate 3**: Final coat of paint strictly after fixed woodwork sanding.
3. **Budget Contingency**: Maintain a 5-10% contingency reserve for unforeseen civil site variations.

---

## ✍️ 7. Client & Project Sign-Off
- **Lead Interior Designer**: `InterioOS AI (Member 1)`
- **Quantity Surveyor**: `InterioOS AI (Member 3)`
- **Cost Estimator**: `InterioOS AI (Member 2)`
- **Project Execution Manager**: `InterioOS AI (Member 4)`
- **Lead Project Coordinator**: `InterioOS AI (Member 5)`

*Status: Approved for Execution Readiness.*
"""
    return report.strip()


# =========================================================
# MEMBER 5: COORDINATOR AGENT NODE
# =========================================================

def coordinator_agent(state: InterioOSState) -> InterioOSState:
    """
    Member 5 - Coordinator Agent Node:
    1. Collects outputs from Member 1 (Design), Member 3 (BOQ), Member 2 (Cost), Member 4 (Timeline).
    2. Synthesizes an executive review and builds a comprehensive final combined report.
    3. Saves final report into state["final_report"].
    """
    design_concept = state.get("design_concept") or ""
    boq_markdown = state.get("boq_markdown") or ""
    cost_info = state.get("cost") or {}
    timeline_markdown = state.get("timeline_markdown") or ""

    user_req = state.get("user_requirement") or "Interior Design Project"
    budget = state.get("budget") or cost_info.get("budget", "N/A")
    est_cost = cost_info.get("estimated_cost", "N/A")
    duration = state.get("estimated_duration") or "4 to 5 Weeks"

    system_prompt = (
        "You are the Lead Executive Coordinator & Project Director for InterioOS AI.\n"
        "Your role is to evaluate the complete multi-agent deliverables (Design Concept, BOQ Material Quantities, Cost Calculation, and Execution Timeline), "
        "and synthesize an insightful, high-level Executive Summary & Strategic Review for the client and contractors.\n\n"
        "Include in your executive synthesis:\n"
        "1. Project Summary & Design Alignment\n"
        "2. Financial Health & Cost Viability\n"
        "3. Timeline Feasibility & Critical Dependencies\n"
        "4. Risk Management & Actionable Next Steps\n\n"
        "Keep the tone highly professional, concise, structured in Markdown."
    )

    prompt = (
        f"Synthesize an Executive Summary for the completed interior project:\n\n"
        f"--- CLIENT REQUIREMENT ---\n{user_req}\n\n"
        f"--- BUDGET & FINANCIALS ---\nBudget: Rs. {budget} | Estimated Cost: Rs. {est_cost} | Status: {cost_info.get('status', 'OK')}\n\n"
        f"--- DURATION ---\nEstimated Duration: {duration}\n\n"
        f"--- SCOPE SUMMARY ---\n"
        f"Design Highlights: {design_concept[:400]}...\n"
        f"Timeline Highlights: {timeline_markdown[:400]}...\n"
    )

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    executive_text = ""
    llm_provider = ""

    try:
        if anthropic_api_key:
            llm_provider = "Claude"
            model = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            executive_text = query_claude(prompt, system_prompt, model, anthropic_api_key)
        elif groq_api_key:
            llm_provider = "Groq (Fallback)"
            model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
            executive_text = query_groq_fallback(prompt, system_prompt, model, groq_api_key)
        else:
            executive_text = synthesize_fallback_executive_summary(state)
            llm_provider = "Algorithmic Synthesis (Offline)"
    except Exception as e:
        # Fallback to algorithmic synthesis if LLM fails
        executive_text = synthesize_fallback_executive_summary(state)
        llm_provider = f"Algorithmic Synthesis (Error: {str(e)[:40]})"

    # Assemble Final Combined Master Report
    final_report = build_final_master_report(state, executive_synthesis=executive_text)

    state["final_report"] = final_report
    state["coordinator_status"] = "completed"
    state["coordinator_engine"] = llm_provider
    state["status"] = "pipeline_completed"

    return state


def coordinator_agent_node(state: InterioOSState) -> InterioOSState:
    """LangGraph node alias for coordinator_agent."""
    return coordinator_agent(state)


# =========================================================
# LANGGRAPH 5-AGENT PIPELINE BUILDER
# =========================================================

def build_full_pipeline():
    """
    LangGraph StateGraph Connection for ALL 5 Agents:
    1. Member 1: Design Agent (design_concept)
    2. Member 3: BOQ Agent (boq_markdown, items)
    3. Member 2: Cost Agent (cost calculation against pricing)
    4. Member 4: Timeline Agent (timeline_markdown, estimated_duration)
    5. Member 5: Coordinator Agent (collects all outputs & creates final report)
    """
    workflow = StateGraph(InterioOSState)

    # 1. Add all 5 agent nodes
    workflow.add_node("design_agent", design_agent_node)
    workflow.add_node("boq_agent", boq_agent_node)
    workflow.add_node("cost_agent", cost_agent)
    workflow.add_node("timeline_agent", timeline_agent_node)
    workflow.add_node("coordinator_agent", coordinator_agent_node)

    # 2. Add sequential edges (1 -> 3 -> 2 -> 4 -> 5)
    workflow.add_edge(START, "design_agent")
    workflow.add_edge("design_agent", "boq_agent")
    workflow.add_edge("boq_agent", "cost_agent")
    workflow.add_edge("cost_agent", "timeline_agent")
    workflow.add_edge("timeline_agent", "coordinator_agent")
    workflow.add_edge("coordinator_agent", END)

    return workflow.compile()


# Precompiled pipeline for reuse
full_pipeline = build_full_pipeline()


def run_interioos_pipeline(
    requirement: str,
    budget: Optional[str] = "800000",
    room_type: Optional[str] = "Master Bedroom",
    style: Optional[str] = "Modern Contemporary",
    groq_key: Optional[str] = None,
    anthropic_key: Optional[str] = None
) -> InterioOSState:
    """
    Executes the entire 5-Agent InterioOS pipeline from start to finish.
    """
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key

    initial_state: InterioOSState = {
        "user_requirement": requirement,
        "budget": budget,
        "room_type": room_type,
        "style": style,
        "status": "started"
    }

    result = cast(InterioOSState, full_pipeline.invoke(initial_state))
    return result


if __name__ == "__main__":
    print("--- InterioOS AI: Member 5 - Coordinator Agent & LangGraph Pipeline ---")
    mock_state: InterioOSState = {
        "user_requirement": "Design a modern bedroom for a client within Rs. 8 lakh budget.",
        "budget": "800000",
        "room_type": "Master Bedroom",
        "style": "Modern Contemporary",
        "design_concept": "Modern aesthetic bedroom with wooden flooring, false ceiling, warm LED lighting, and matte wardrobe.",
        "boq_markdown": "| Category | Item | Qty | Unit |\n| Finishes | Paint | 200 | sqft |\n| Finishes | Flooring | 168 | sqft |",
        "items": [
            {"name": "Paint", "quantity": 200, "unit": "sqft"},
            {"name": "Flooring", "quantity": 168, "unit": "sqft"},
            {"name": "Bed", "quantity": 1, "unit": "pcs"},
            {"name": "Wardrobe", "quantity": 1, "unit": "pcs"}
        ],
        "cost": {
            "estimated_cost": 364440,
            "budget": 800000,
            "remaining_budget": 435560,
            "status": "Within Budget",
            "items": [
                {"item": "Paint", "quantity": 200, "unit": "sqft", "unit_price": 50, "total": 10000, "status": "OK"},
                {"item": "Flooring", "quantity": 168, "unit": "sqft", "unit_price": 120, "total": 20160, "status": "OK"},
                {"item": "Bed", "quantity": 1, "unit": "pcs", "unit_price": 45000, "total": 45000, "status": "OK"},
                {"item": "Wardrobe", "quantity": 1, "unit": "pcs", "unit_price": 60000, "total": 60000, "status": "OK"}
            ]
        },
        "timeline_markdown": "### Total Duration: 4 Weeks\n- Phase 1: Procurement (Days 1-3)\n- Phase 2: Flooring & Paint (Days 4-14)\n- Phase 3: Furniture & Handover (Days 15-28)",
        "estimated_duration": "4 Weeks (28 Days)"
    }

    res = coordinator_agent(mock_state)
    print(f"\n[SUCCESS] Final Report generated via {res.get('coordinator_engine')}!")
    print("\n--- FINAL MASTER REPORT PREVIEW ---")
    print((res.get("final_report") or "")[:600] + "\n...")
