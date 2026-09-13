"""
InterioOS AI - Multi-Agent Interior Design Platform
Tech Stack: Python, Streamlit, LangGraph, Groq API, Anthropic Claude
Agents:
- Member 1: Design Agent (Concept Generation)
- Member 3: BOQ Agent (Materials & Quantities)
- Member 2: Cost Estimator (Financial Feasibility)
- Member 4: Timeline Agent (Project Schedule)
- Member 5: Coordinator Agent (Master Report & Orchestration)
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Import the LangGraph modules and agents
from design_agent import generate_design_concept, InterioOSState
from agents.boq_agent import boq_agent
from agents.cost_agent import cost_agent
from agents.timeline_agent import timeline_agent
from agents.coordinator_agent import (
    coordinator_agent,
    build_full_pipeline,
    run_interioos_pipeline,
    build_final_master_report
)

# Page configuration
st.set_page_config(
    page_title="InterioOS AI — Multi-Agent Interior Design Operating System",
    page_icon="🏛️",
    layout="wide"
)

# Load environment variables from .env
load_dotenv()

# Sidebar: API Key Configuration & Multi-Agent Architecture
with st.sidebar:
    st.markdown("### 🔑 API Configuration")
    env_groq = os.getenv("GROQ_API_KEY", "")
    env_anthropic = os.getenv("ANTHROPIC_API_KEY", "")

    groq_input = st.text_input(
        "Groq API Key",
        value=env_groq,
        type="password",
        help="Get free key at console.groq.com/keys"
    )
    anthropic_input = st.text_input(
        "Anthropic API Key (Optional)",
        value=env_anthropic,
        type="password",
        help="For Claude (Member 3 BOQ, Member 4 Timeline & Member 5 Coordinator)"
    )

    if groq_input:
        os.environ["GROQ_API_KEY"] = groq_input.strip()
    if anthropic_input:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_input.strip()

    st.markdown("---")
    st.markdown("### 👥 5-Agent Multi-Agent Team")
    st.markdown("1. 🎨 **Member 1**: Design Agent *(Groq)*")
    st.markdown("2. 🧱 **Member 3**: BOQ Agent *(Claude/Groq)*")
    st.markdown("3. 💰 **Member 2**: Cost Estimator *(Pricing Engine)*")
    st.markdown("4. 📅 **Member 4**: Execution Timeline *(Claude/Groq)*")
    st.markdown("5. 🏛️ **Member 5**: Coordinator Agent *(LangGraph Orchestrator)*")
    st.markdown("---")
    st.caption("InterioOS AI • LangGraph Multi-Agent Architecture")

# Custom CSS for modern, premium styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .badge-member {
        background-color: #EEF2FF;
        color: #4F46E5;
        padding: 4px 14px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 0.8rem;
        border: 1px solid #C7D2FE;
    }
    .badge-coordinator {
        background-color: #ECFDF5;
        color: #059669;
        padding: 4px 14px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 0.8rem;
        border: 1px solid #A7F3D0;
    }
    .stButton>button {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        padding: 10px 22px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #4338CA;
        color: white;
    }
    .kpi-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .kpi-title {
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
    }
    .kpi-val {
        font-size: 1.4rem;
        color: #0F172A;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for persistent results
if "interio_os_state" not in st.session_state:
    st.session_state["interio_os_state"] = None

# Main Content Header
st.markdown('<div class="badge-coordinator">🏛️ Member 5 — Lead Coordinator & LangGraph Orchestrator</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏛️ InterioOS AI — Turnkey Interior Design Suite</div>', unsafe_allow_html=True)
st.markdown("Client requirement enter karein aur tamam 5 AI Agents ke zariye complete turnkey concept, BOQ, costing, timeline aur master report hasil karein.")

st.markdown("---")

# Quick Preset Buttons
st.markdown("##### ⚡ Quick Project Presets")
col_p1, col_p2, col_p3 = st.columns(3)

preset_text = ""
with col_p1:
    if st.button("🛏️ Modern Bedroom (Rs. 8 Lakh)", use_container_width=True):
        preset_text = "Design a modern bedroom for a client within a budget of Rs. 8 lakh. Include neutral tones, natural wood headboard, ergonomic wardrobe, and ambient warm lighting."

with col_p2:
    if st.button("🛋️ Japandi Living Room (Rs. 12 Lakh)", use_container_width=True):
        preset_text = "Design a minimalist Japandi style living room with budget of Rs. 12 lakh. Needs oak wood textures, linen upholstery, indoor plants, and layered indirect cove lighting."

with col_p3:
    if st.button("🍽️ Modular Kitchen (Rs. 6 Lakh)", use_container_width=True):
        preset_text = "Design a contemporary modular kitchen for an apartment with Rs. 6 lakh budget. Quartz countertop, matte acrylic cabinets, under-cabinet task lighting, and smart pull-out pantry."

# Input Form
with st.form("main_project_form"):
    st.markdown("##### 📝 Client Project Requirements")

    default_req = preset_text if preset_text else "Design a modern bedroom for a client within a budget of Rs. 8 lakh."
    user_req = st.text_area(
        "Design Requirement *",
        value=default_req,
        height=110,
        help="Client requirements, room type, style, budget, or constraints."
    )

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        budget_input = st.text_input("Budget (Optional)", value="Rs. 8 Lakh")
    with col_f2:
        room_type_input = st.text_input("Room Type (Optional)", value="Master Bedroom")
    with col_f3:
        style_input = st.text_input("Style (Optional)", value="Modern Contemporary")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        run_full_pipeline_btn = st.form_submit_button("⚡ Run Full 5-Agent Pipeline (One-Click)", use_container_width=True)
    with col_b2:
        generate_concept_only_btn = st.form_submit_button("🎨 Step 1 Only: Generate Design Concept", use_container_width=True)

# 1. Execution Logic: Full 5-Agent Pipeline
if run_full_pipeline_btn:
    if not user_req.strip():
        st.error("Please enter a valid user requirement.")
    else:
        with st.status("🚀 Orchestrating 5-Agent Multi-Agent LangGraph Pipeline...", expanded=True) as status:
            st.write("🎨 **Step 1/5**: Member 1 Design Agent generating design concept...")
            # Step 1: Design
            res_state = generate_design_concept(
                requirement=user_req.strip(),
                budget=budget_input.strip() if budget_input else None,
                room_type=room_type_input.strip() if room_type_input else None,
                style=style_input.strip() if style_input else None
            )

            if res_state.get("design_concept"):
                st.write("🧱 **Step 2/5**: Member 3 BOQ Agent quantifying materials & items...")
                res_state = boq_agent(res_state)

            if res_state.get("items"):
                st.write("💰 **Step 3/5**: Member 2 Cost Estimator calculating budget vs item rates...")
                res_state = cost_agent(res_state)

            st.write("📅 **Step 4/5**: Member 4 Timeline Agent building phase execution schedule...")
            res_state = timeline_agent(res_state)

            st.write("🏛️ **Step 5/5**: Member 5 Coordinator Agent synthesizing Master Project Report...")
            res_state = coordinator_agent(res_state)

            st.session_state["interio_os_state"] = res_state
            status.update(label="✅ Full 5-Agent Pipeline Completed Successfully!", state="complete", expanded=False)
            st.success("🎉 Complete Turnkey Dossier ready! Scroll down to inspect all agent deliverables.")

# 2. Execution Logic: Concept Only
elif generate_concept_only_btn:
    if not user_req.strip():
        st.error("Please enter a valid user requirement.")
    else:
        with st.spinner("⚡ Generating design concept via Member 1 (Groq)..."):
            res_state = generate_design_concept(
                requirement=user_req.strip(),
                budget=budget_input.strip() if budget_input else None,
                room_type=room_type_input.strip() if room_type_input else None,
                style=style_input.strip() if style_input else None
            )
            st.session_state["interio_os_state"] = res_state
            if res_state.get("error"):
                st.error(f"❌ Error: {res_state.get('error')}")
            else:
                st.success("✅ Design concept generated & successfully saved in LangGraph State!")

# Display Pipeline Results
saved_state = st.session_state.get("interio_os_state")

if saved_state and (saved_state.get("design_concept") or saved_state.get("final_report")):

    # =========================================================================
    # EXECUTIVE KPI DASHBOARD (If cost / timeline available)
    # =========================================================================
    cost_info = saved_state.get("cost") or {}
    est_cost = cost_info.get("estimated_cost", 0)
    budget_val = cost_info.get("budget", 0)
    rem_budget = cost_info.get("remaining_budget", 0)
    budget_status = cost_info.get("status", "Pending")
    duration = saved_state.get("estimated_duration", "4 to 5 Weeks")
    items_count = len(saved_state.get("items") or cost_info.get("items") or [])

    st.markdown("### 📊 Project Summary & Executive KPIs")
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Total Estimated Cost", f"Rs. {est_cost:,.0f}" if est_cost else "Calculating...")
    with col_k2:
        st.metric("Client Budget", f"Rs. {budget_val:,.0f}" if budget_val else (saved_state.get("budget") or "N/A"))
    with col_k3:
        st.metric("Budget Health", budget_status, delta=f"Rs. {rem_budget:,.0f} reserve" if rem_budget else None)
    with col_k4:
        st.metric("Est. Project Duration", duration)

    st.markdown("---")

    # =========================================================================
    # MEMBER 5: COORDINATOR AGENT — FINAL MASTER REPORT TAB & SECTION
    # =========================================================================
    st.markdown('<div class="badge-coordinator">Member 5 — Master Project Dossier & Final Report</div>', unsafe_allow_html=True)
    st.markdown("### 🏛️ Complete Multi-Agent Turnkey Report")
    st.markdown("Tamam 4 agents ke data ko synthesize karke banayi gayi master executive report.")

    if not saved_state.get("final_report"):
        if st.button("🏛️ Synthesize & Generate Final Master Report (Member 5)", key="gen_master_report_btn"):
            with st.spinner("⚡ Member 5 Coordinator Agent synthesizing executive dossier..."):
                updated_state = coordinator_agent(saved_state)
                st.session_state["interio_os_state"] = updated_state
                st.success("✅ Master Project Report successfully generated!")
                st.rerun()

    if saved_state.get("final_report"):
        tab_report, tab_design, tab_boq, tab_cost, tab_timeline = st.tabs([
            "📑 Master Project Dossier (Member 5)",
            "🎨 Design Concept (Member 1)",
            "🧱 BOQ & Materials (Member 3)",
            "💰 Financial & Cost (Member 2)",
            "📅 Execution Timeline (Member 4)"
        ])

        with tab_report:
            st.markdown(saved_state["final_report"])
            st.download_button(
                label="📥 Download Complete Master Dossier (.md)",
                data=saved_state["final_report"],
                file_name="InterioOS_Master_Project_Report.md",
                mime="text/markdown",
                key="dl_master_report"
            )

        with tab_design:
            st.markdown(saved_state.get("design_concept", "*No design concept found.*"))
            if saved_state.get("design_concept"):
                st.download_button(
                    label="📥 Download Design Concept (.md)",
                    data=saved_state["design_concept"],
                    file_name="interior_design_concept.md",
                    mime="text/markdown",
                    key="dl_design_concept"
                )

        with tab_boq:
            if saved_state.get("boq_markdown"):
                st.markdown(saved_state["boq_markdown"])
            if saved_state.get("items"):
                with st.expander(f"🔍 Raw Structured Items ({len(saved_state['items'])} items)", expanded=False):
                    st.table(saved_state["items"])

        with tab_cost:
            if cost_info:
                st.markdown(f"**Estimated Cost:** `Rs. {est_cost:,.0f}` | **Budget Status:** `{budget_status}`")
                if cost_info.get("items"):
                    st.table(cost_info["items"])

        with tab_timeline:
            st.markdown(f"**⏱️ Total Duration:** `{duration}`")
            st.markdown(saved_state.get("timeline_markdown", "*No timeline found.*"))

    else:
        # Step-by-Step Individual Agent Generation Controls
        st.markdown("---")
        st.markdown('<div class="badge-member">Member 1 — Design Concept</div>', unsafe_allow_html=True)
        st.markdown(saved_state.get("design_concept", ""))

        # Member 3: BOQ Trigger
        st.markdown("---")
        st.markdown('<div class="badge-member">Member 3 — BOQ Agent</div>', unsafe_allow_html=True)
        if st.button("📦 Generate Material List & BOQ", key="step_boq_btn"):
            with st.spinner("⚡ Member 3 (Claude/Groq) generating BOQ..."):
                updated_state = boq_agent(saved_state)
                if updated_state.get("items"):
                    updated_state = cost_agent(updated_state)
                st.session_state["interio_os_state"] = updated_state
                st.rerun()

        if saved_state.get("boq_markdown"):
            st.markdown(saved_state["boq_markdown"])

        # Member 4: Timeline Trigger
        st.markdown("---")
        st.markdown('<div class="badge-member">Member 4 — Timeline Agent</div>', unsafe_allow_html=True)
        if st.button("⏱️ Generate Execution Timeline", key="step_timeline_btn"):
            with st.spinner("⚡ Member 4 generating schedule..."):
                updated_state = timeline_agent(saved_state)
                st.session_state["interio_os_state"] = updated_state
                st.rerun()

        if saved_state.get("timeline_markdown"):
            st.markdown(saved_state["timeline_markdown"])
