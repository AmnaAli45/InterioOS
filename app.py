"""
InterioOS AI - Design Agent
Tech Stack: Python, Streamlit, LangGraph, Groq API
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Import the LangGraph modules
from design_agent import generate_design_concept, InterioOSState
from agents.boq_agent import boq_agent

# Page configuration
st.set_page_config(
    page_title="InterioOS AI - Design Agent",
    page_icon="🛋️",
    layout="wide"
)

# Load environment variables from .env
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

# Main Content Header
st.markdown('<div class="badge-member">Member 1 — Design Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🛋️ Interior Design Concept Generator</div>', unsafe_allow_html=True)
st.markdown("Client requirement enter karein aur ultra-fast AI design concept generate karein.")

st.markdown("---")

# Quick Preset Buttons
st.markdown("##### ⚡ Quick Presets")
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
        "Design Requirement *",
        value=default_req,
        height=120,
        help="Client requirements, room type, style, budget, or constraints."
    )

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        budget_input = st.text_input("Budget (Optional)", value="Rs. 8 Lakh")
    with col_f2:
        room_type_input = st.text_input("Room Type (Optional)", value="Master Bedroom")
    with col_f3:
        style_input = st.text_input("Style (Optional)", value="Modern Contemporary")

    submit_button = st.form_submit_button("🚀 Generate Design Concept (Ultra-Fast Groq)")

# Execution Logic
if submit_button:
    if not user_req.strip():
        st.error("Please enter a valid user requirement.")
    else:
        with st.spinner("⚡ Generating concept in seconds via Groq..."):
            result_state: InterioOSState = generate_design_concept(
                requirement=user_req.strip(),
                budget=budget_input.strip() if budget_input else None,
                room_type=room_type_input.strip() if room_type_input else None,
                style=style_input.strip() if style_input else None
            )

            st.session_state["interio_os_state"] = result_state

            if result_state.get("error"):
                st.error(f"❌ Error: {result_state['error']}")
            else:
                st.success("✅ Design concept generated & successfully saved in LangGraph State!")

# Display Clean Results (Direct Concept Only)
saved_state = st.session_state.get("interio_os_state")
if saved_state and saved_state.get("design_concept"):
    st.markdown("---")
    st.markdown("### 📋 Generated Design Concept")

    st.markdown(saved_state["design_concept"])
    st.download_button(
        label="📥 Download Concept (.md)",
        data=saved_state["design_concept"],
        file_name="interior_design_concept.md",
        mime="text/markdown"
    )

    # Member 3: BOQ Agent Section
    st.markdown("---")
    st.markdown('<div class="badge-member">Member 3 — BOQ Agent</div>', unsafe_allow_html=True)
    st.markdown("### 🧱 Bill of Quantities (BOQ) & Material List")
    st.markdown("Design concept se materials ki complete list generate karein (Paint, Tiles/Flooring, Furniture, Electrical) with realistic quantities.")

    if st.button("📦 Generate Material List & BOQ", key="generate_boq_btn"):
        with st.spinner("⚡ Claude/Groq analyzing design concept and generating BOQ with quantities..."):
            updated_state = boq_agent(saved_state)
            st.session_state["interio_os_state"] = updated_state
            if updated_state.get("error"):
                st.error(f"❌ {updated_state['error']}")
            else:
                st.success(f"✅ BOQ generated via {updated_state.get('boq_engine', 'AI')} and saved to State!")

    # Display BOQ results if generated
    if saved_state.get("boq_markdown"):
        st.markdown("#### 📋 Material & Quantity Breakdown")
        st.markdown(saved_state["boq_markdown"])

        if saved_state.get("items"):
            with st.expander(f"🔍 Structured Items for Cost Agent ({len(saved_state['items'])} items)", expanded=False):
                st.table(saved_state["items"])

        st.download_button(
            label="📥 Download BOQ Material List (.md)",
            data=saved_state["boq_markdown"],
            file_name="boq_material_list.md",
            mime="text/markdown"
        )
