"""
InterioOS AI - Member 1: Design Agent Streamlit Application
Tech Stack: Python, Streamlit, LangGraph, Anthropic Claude API
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

# Import the Design Agent LangGraph module
from design_agent import generate_design_concept, InterioOSState

# Page configuration
st.set_page_config(
    page_title="InterioOS AI - Design Agent",
    page_icon="🛋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Custom CSS for clean, premium styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .badge-member {
        background-color: #EEF2FF;
        color: #4F46E5;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 1rem;
        border: 1px solid #C7D2FE;
    }
    .status-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #4338CA;
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for persistent results
if "interio_os_state" not in st.session_state:
    st.session_state["interio_os_state"] = None

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Agent Configuration")
    st.markdown("Configure your **Claude API** credentials and agent settings.")

    env_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=env_api_key,
        type="password",
        help="Enter your Anthropic API Key (or set ANTHROPIC_API_KEY in your .env file)."
    )

    model_choice = st.selectbox(
        "Claude Model",
        options=[
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-haiku-20240307",
            "claude-3-opus-20240229"
        ],
        index=0,
        help="Select model for design concept generation."
    )

    if model_choice:
        os.environ["ANTHROPIC_MODEL"] = model_choice

    st.markdown("---")
    st.markdown("### 👥 Team Role Details")
    st.markdown("""
    **Member 1 — Design Agent**
    - **Input**: User Design Requirement
    - **Action**: Prompt Claude API for design concept
    - **State**: Saves `design_concept` in **LangGraph State**
    - **Tech Stack**: `Python`, `Streamlit`, `LangGraph`
    """)

# Main Content
st.markdown('<div class="badge-member">Member 1 — Design Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🛋️ InterioOS AI — Design Concept Generator</div>', unsafe_allow_html=True)
st.markdown("Input client requirements to trigger the **LangGraph Design Agent**, communicate with **Claude API**, and save structured concepts into the shared multi-agent state.")

st.markdown("---")

# Quick Preset Buttons
st.markdown("##### ⚡ Quick Requirement Presets")
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
with st.form("design_agent_form"):
    st.markdown("##### 📝 Client Requirement Details")

    default_req = preset_text if preset_text else "Design a modern bedroom for a client within a budget of Rs. 8 lakh."
    user_req = st.text_area(
        "Design Requirement Prompt *",
        value=default_req,
        height=120,
        help="Enter the specific client requirements, room type, style, budget, or constraints."
    )

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        budget_input = st.text_input("Budget (Optional)", value="Rs. 8 Lakh")
    with col_f2:
        room_type_input = st.text_input("Room Type (Optional)", value="Master Bedroom")
    with col_f3:
        style_input = st.text_input("Style (Optional)", value="Modern Contemporary")

    submit_button = st.form_submit_button("🚀 Generate Design Concept (LangGraph Node)")

# Execution Logic
if submit_button:
    if not user_req.strip():
        st.error("Please enter a valid user requirement.")
    elif not api_key_input.strip():
        st.warning("⚠️ Anthropic API Key is missing. Please enter your API Key in the sidebar or save it in your .env file.")
    else:
        with st.spinner("🤖 Design Agent is calling Claude API and updating LangGraph State..."):
            result_state: InterioOSState = generate_design_concept(
                requirement=user_req.strip(),
                budget=budget_input.strip() if budget_input else None,
                room_type=room_type_input.strip() if room_type_input else None,
                style=style_input.strip() if style_input else None,
                api_key=api_key_input.strip()
            )

            st.session_state["interio_os_state"] = result_state

            if result_state.get("error"):
                st.error(f"❌ Error: {result_state['error']}")
            else:
                st.success("✅ Design concept successfully generated and saved into LangGraph State!")

# Display Results if Available
saved_state = st.session_state.get("interio_os_state")
if saved_state and saved_state.get("design_concept"):
    st.markdown("---")
    st.markdown("### 📊 Agent Results & State")

    tab_concept, tab_state, tab_team = st.tabs([
        "📄 Generated Design Concept",
        "🧠 LangGraph State Inspector",
        "🤝 Downstream Multi-Agent Hand-off"
    ])

    with tab_concept:
        st.markdown(saved_state["design_concept"])
        st.download_button(
            label="📥 Download Design Concept (.md)",
            data=saved_state["design_concept"],
            file_name="interioos_design_concept.md",
            mime="text/markdown"
        )

    with tab_state:
        st.markdown("**Current LangGraph State (`InterioOSState`):**")
        st.caption("This state object is maintained by LangGraph and accessible to all team members' agents.")
        st.json(saved_state)

    with tab_team:
        st.markdown("""
        #### 🔄 How Team Members Use This State:
        Member 1 has populated `design_concept` in the shared state. Other agents can now continue the workflow:

        1. **Member 2 (Cost & Material Agent)**:
           - Reads `state["design_concept"]`
           - Estimates materials and total project cost within budget.
        2. **Member 3 (BOQ Agent)**:
           - Extracts itemized components and creates Bill of Quantities.
        3. **Member 4 (Vendor Agent)**:
           - Matches material requirements with potential suppliers.
        4. **Member 5 (Coordinator / PM Agent)**:
           - Builds timeline, milestones, and consolidated project report.
        """)
