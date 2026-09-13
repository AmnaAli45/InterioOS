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
import json
import base64
import streamlit as st
from dotenv import load_dotenv
from boq_parser import parse_boq_items

# Keep the UI importable in demo mode when optional agent dependencies are absent.
try:
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
    PIPELINE_IMPORT_ERROR = None
except Exception as exc:
    InterioOSState = dict
    PIPELINE_IMPORT_ERROR = exc
    generate_design_concept = None
    boq_agent = None
    cost_agent = None
    timeline_agent = None
    coordinator_agent = None
    build_full_pipeline = None
    run_interioos_pipeline = None
    build_final_master_report = None


DEMO_STATE: InterioOSState = {
    "user_requirement": "Demo: modern bedroom within Rs. 8 lakh",
    "design_concept": "Warm modern bedroom with neutral paint, timber flooring, a storage bed, and layered lighting.",
    "boq_markdown": (
        "| Category | Item Name | Quantity | Unit |\n"
        "| --- | --- | --- | --- |\n"
        "| Finishes | Paint | 200 | sqft |\n"
        "| Finishes | Flooring | 168 | sqft |\n"
        "| Furniture | Bed | 1 | pcs |\n"
        "| Furniture | Wardrobe | 1 | pcs |\n"
        "| Electrical | LED Light | 8 | pcs |\n"
        "| Decor | Curtain | 1 | pcs |"
    ),
    "items": [
        {"name": "Paint", "quantity": 200, "unit": "sqft"},
        {"name": "Flooring", "quantity": 168, "unit": "sqft"},
        {"name": "Bed", "quantity": 1, "unit": "pcs"},
        {"name": "Wardrobe", "quantity": 1, "unit": "pcs"},
        {"name": "LED Light", "quantity": 8, "unit": "pcs"},
        {"name": "Curtain", "quantity": 1, "unit": "pcs"},
    ],
    "cost": {"estimated_cost": 0, "budget": 800000, "remaining_budget": 800000, "status": "Demo mode"},
    "timeline_markdown": "### Total Duration: 4 Weeks\n- Procurement and site preparation\n- Finishes and electrical work\n- Furniture installation and handover",
    "estimated_duration": "4 Weeks",
    "final_report": "Demo mode is active. Add API keys to run the live multi-agent pipeline.",
    "status": "demo",
}


def build_room_scene(items: list[dict[str, str]]) -> str:
    """Build the self-contained Three.js room viewer used by Streamlit."""
    item_json = json.dumps(items).replace("</", "<\\/")
    return f"""
<div id="room-viewer"></div>
<style>html,body{{margin:0;overflow:hidden;background:#101820}}#room-viewer{{width:100%;height:520px}}</style>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const items = {item_json};
const root = document.getElementById('room-viewer');
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x101820);
const camera = new THREE.PerspectiveCamera(45, root.clientWidth / root.clientHeight, 0.1, 1000); camera.position.set(15, 12, 17);
const renderer = new THREE.WebGLRenderer({{antialias:true}}); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); renderer.setSize(root.clientWidth, root.clientHeight); root.appendChild(renderer.domElement);
const controls = new THREE.OrbitControls(camera, renderer.domElement); controls.target.set(0, 3, 0); controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xfff5df, 0x203040, 2.4)); const room = new THREE.Group(); scene.add(room);
const floor = new THREE.Mesh(new THREE.BoxGeometry(12, .18, 12), new THREE.MeshStandardMaterial({{color:0x806c58,roughness:.8}})); floor.position.y = -.1; room.add(floor);
const wallMaterial = new THREE.MeshStandardMaterial({{color:0xa4c2c7,transparent:true,opacity:.25,side:THREE.DoubleSide}});
[[0,4.5,-6,12,9,.12],[0,4.5,6,12,9,.12],[-6,4.5,0,.12,9,12],[6,4.5,0,.12,9,12]].forEach(([x,y,z,w,h,d])=>{{const wall=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),wallMaterial);wall.position.set(x,y,z);room.add(wall)}});
const colors={{furniture:0xd98b5f,lighting:0xf4cf58,finish:0x86b6a5,'soft furnishing':0xb38ac7,decor:0xe58f9c,other:0x8ca6bf}};
function label(text,x,y,z){{const canvas=document.createElement('canvas');canvas.width=256;canvas.height=64;const ctx=canvas.getContext('2d');ctx.fillStyle='#ffffff';ctx.font='bold 24px sans-serif';ctx.textAlign='center';ctx.fillText(text.slice(0,20),128,40);const sprite=new THREE.Sprite(new THREE.SpriteMaterial({{map:new THREE.CanvasTexture(canvas),transparent:true}}));sprite.scale.set(2.8,.7,1);sprite.position.set(x,y,z);room.add(sprite)}}
items.forEach((item,index)=>{{const angle=(index/Math.max(items.length,1))*Math.PI*2;const x=Math.cos(angle)*4.1;const z=Math.sin(angle)*4.1;const material=new THREE.MeshStandardMaterial({{color:colors[item.category]||colors.other,roughness:.65}});const box=new THREE.Mesh(new THREE.BoxGeometry(1.8,1.5,1.2),material);box.position.set(x,.75,z);room.add(box);label(item.name,x,2.0,z)}});
function resize(){{camera.aspect=root.clientWidth/root.clientHeight;camera.updateProjectionMatrix();renderer.setSize(root.clientWidth,root.clientHeight)}} window.addEventListener('resize',resize);
function animate(){{requestAnimationFrame(animate);controls.update();renderer.render(scene,camera)}} animate();
</script>"""

# Page configuration
st.set_page_config(
    page_title="InterioOS AI — Multi-Agent Interior Design Operating System",
    page_icon=":material/architecture:",
    layout="wide"
)

# Load environment variables from .env
load_dotenv()

# Sidebar: API Key Configuration & Multi-Agent Architecture
with st.sidebar:
    st.markdown("### :material/key: API configuration")
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

    st.markdown("### :material/groups: Multi-agent team")
    st.markdown("1. :material/design_services: **Member 1**: Design Agent *(Groq)*")
    st.markdown("2. :material/inventory_2: **Member 3**: BOQ Agent *(Claude/Groq)*")
    st.markdown("3. :material/payments: **Member 2**: Cost Estimator *(Pricing Engine)*")
    st.markdown("4. :material/calendar_month: **Member 4**: Execution Timeline *(Claude/Groq)*")
    st.markdown("5. :material/account_tree: **Member 5**: Coordinator Agent *(LangGraph Orchestrator)*")
    st.caption("InterioOS AI · LangGraph multi-agent architecture")

# Optional background asset. The UI remains fully usable when the image is absent.
background_image_path = os.path.join(os.path.dirname(__file__), "assets", "background.jpg")
if os.path.isfile(background_image_path):
    with open(background_image_path, "rb") as background_file:
        background_data = base64.b64encode(background_file.read()).decode("ascii")
    background_image_css = f"url('data:image/jpeg;base64,{background_data}')"
else:
    background_image_css = "none"

# Custom CSS for modern, premium styling
st.markdown("""
<style>
    :root {
        --interio-accent: #4F46E5;
        --interio-accent-dark: #3730A3;
        --interio-ink: #172033;
        --interio-muted: #64748B;
        --interio-border: #E2E8F0;
        --interio-surface: #FFFFFF;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #F6F8FC;
        background-image: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), var(--interio-background-image);
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        background-repeat: no-repeat;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        background: rgba(255, 255, 255, 0.12);
    }
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"] [data-testid="stMainBlockContainer"] {
        position: relative;
        z-index: 1;
    }
    [data-testid="stMainBlockContainer"] {
        background: rgba(255, 255, 255, 0.76);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 0.85rem;
        box-shadow: 0 12px 36px rgba(15, 23, 42, 0.06);
    }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.97);
        border-right: 1px solid var(--interio-border);
        box-shadow: 4px 0 18px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stSidebarContent"] {
        padding: 1.35rem 1.1rem;
    }
    .main-title {
        font-size: 2.35rem;
        font-weight: 800;
        color: var(--interio-ink);
        margin: 0.25rem 0 0.4rem;
        letter-spacing: 0;
        line-height: 1.15;
    }
    .badge-member {
        background: #EEF2FF;
        color: var(--interio-accent-dark);
        padding: 0.35rem 0.7rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
        margin-bottom: 0.65rem;
        border: 1px solid #C7D2FE;
    }
    .badge-coordinator {
        background: #EEF2FF;
        color: var(--interio-accent-dark);
        padding: 0.35rem 0.7rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
        margin-bottom: 0.65rem;
        border: 1px solid #C7D2FE;
    }
    .section-card {
        background: var(--interio-surface);
        border: 1px solid var(--interio-border);
        border-radius: 0.65rem;
        padding: 1rem 1.15rem 0.75rem;
        margin: 0.75rem 0 1.15rem;
        box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
    }
    .section-card h5 {
        color: var(--interio-ink);
        margin: 0 0 0.7rem;
        font-size: 1rem;
        font-weight: 700;
    }
    .stButton>button {
        background: var(--interio-accent);
        color: #FFFFFF;
        border-radius: 0.5rem;
        min-height: 2.55rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: 1px solid var(--interio-accent);
        transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
    }
    .stButton>button:hover {
        background: var(--interio-accent-dark);
        border-color: var(--interio-accent-dark);
        color: #FFFFFF;
        transform: translateY(-1px);
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
        color: var(--interio-ink);
        font-weight: 800;
    }
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.98);
        border: 1px solid var(--interio-border);
        border-radius: 0.65rem;
        padding: 0.15rem 1.15rem 0.85rem;
        box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
    }
    div[data-testid="stExpander"] {
        border-color: var(--interio-border);
        border-radius: 0.5rem;
    }
    .visualization-card {
        background: rgba(255, 255, 255, 0.98);
        border: 1px solid var(--interio-border);
        border-radius: 0.65rem;
        padding: 0.85rem;
        box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.98);
        border-color: var(--interio-border);
        box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
    }
    @media (max-width: 640px) {
        [data-testid="stAppViewContainer"] {
            background-attachment: scroll;
            background-position: center top;
            background-image: linear-gradient(rgba(255, 255, 255, 0.93), rgba(255, 255, 255, 0.93)), var(--interio-background-image);
        }
        [data-testid="stMainBlockContainer"] {
            border-radius: 0.55rem;
            box-shadow: none;
        }
        .main-title {
            font-size: 1.85rem;
        }
    }
</style>
""".replace("var(--interio-background-image)", background_image_css), unsafe_allow_html=True)

# Initialize session state for persistent results
if "interio_os_state" not in st.session_state:
    st.session_state["interio_os_state"] = None

# Main Content Header
st.markdown('<div class="badge-coordinator">:material/account_tree: Member 5 — Lead Coordinator & LangGraph Orchestrator</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">InterioOS AI — Turnkey Interior Design Suite</div>', unsafe_allow_html=True)
st.markdown("Client requirement enter karein aur tamam 5 AI Agents ke zariye complete turnkey concept, BOQ, costing, timeline aur master report hasil karein.")

# Quick Preset Buttons
preset_text = ""
with st.container(border=True):
    st.markdown("##### :material/bolt: Quick project presets")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button(":material/bed: Modern bedroom (Rs. 8 lakh)", width="stretch"):
            preset_text = "Design a modern bedroom for a client within a budget of Rs. 8 lakh. Include neutral tones, natural wood headboard, ergonomic wardrobe, and ambient warm lighting."

    with col_p2:
        if st.button(":material/weekend: Japandi living room (Rs. 12 lakh)", width="stretch"):
            preset_text = "Design a minimalist Japandi style living room with budget of Rs. 12 lakh. Needs oak wood textures, linen upholstery, indoor plants, and layered indirect cove lighting."

    with col_p3:
        if st.button(":material/table_restaurant: Modular kitchen (Rs. 6 lakh)", width="stretch"):
            preset_text = "Design a contemporary modular kitchen for an apartment with Rs. 6 lakh budget. Quartz countertop, matte acrylic cabinets, under-cabinet task lighting, and smart pull-out pantry."

# Input Form
with st.form("main_project_form"):
    st.markdown("##### :material/edit_note: Client project requirements")

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
        run_full_pipeline_btn = st.form_submit_button(":material/play_arrow: Generate plan (run full pipeline)", width="stretch")
    with col_b2:
        generate_concept_only_btn = st.form_submit_button(":material/design_services: Generate design concept", width="stretch")

# 1. Execution Logic: Full 5-Agent Pipeline
if run_full_pipeline_btn:
    if not user_req.strip():
        st.error("Please enter a valid user requirement.")
    else:
        with st.status("Running the multi-agent pipeline...", expanded=True) as status:
            st.write(":material/account_tree: **Steps 1-5**: Running the compiled Member 5 LangGraph pipeline...")
            try:
                res_state = run_interioos_pipeline(
                    requirement=user_req.strip(),
                    budget=budget_input.strip() if budget_input else None,
                    room_type=room_type_input.strip() if room_type_input else None,
                    style=style_input.strip() if style_input else None,
                    groq_key=groq_input.strip() if groq_input else None,
                    anthropic_key=anthropic_input.strip() if anthropic_input else None,
                )
                if res_state.get("error"):
                    raise RuntimeError(res_state["error"])
            except Exception as exc:
                res_state = dict(DEMO_STATE)
                res_state["user_requirement"] = user_req.strip()
                res_state["error"] = f"Live pipeline unavailable; showing demo data ({exc})"

            st.session_state["interio_os_state"] = res_state
            is_demo = res_state.get("status") == "demo"
            status.update(label="Demo plan ready" if is_demo else "Full 5-agent pipeline completed", state="complete", expanded=False)
            if is_demo:
                st.warning(res_state.get("error", "Live pipeline unavailable; showing demo data."))
            else:
                st.success("Complete turnkey dossier ready. Scroll down to inspect all agent deliverables.", icon=":material/check_circle:")

# 2. Execution Logic: Concept Only
elif generate_concept_only_btn:
    if not user_req.strip():
        st.error("Please enter a valid user requirement.")
    else:
        with st.spinner("Generating design concept via Member 1 (Groq)..."):
            res_state = generate_design_concept(
                requirement=user_req.strip(),
                budget=budget_input.strip() if budget_input else None,
                room_type=room_type_input.strip() if room_type_input else None,
                style=style_input.strip() if style_input else None
            )
            st.session_state["interio_os_state"] = res_state
            if res_state.get("error"):
                st.error(f"Error: {res_state.get('error')}", icon=":material/error:")
            else:
                st.success("Design concept generated and saved in LangGraph state.", icon=":material/check_circle:")

# Display Pipeline Results
saved_state = st.session_state.get("interio_os_state")

if saved_state:
    raw_boq = saved_state.get("boq_markdown") or ""
    scene_items = parse_boq_items(raw_boq)
    if not scene_items:
        scene_items = [
            {"name": str(item.get("name", "Item")), "category": str(item.get("category", "other")).lower()}
            for item in (saved_state.get("items") or [])
            if isinstance(item, dict) and item.get("name")
        ]
    with st.container(border=True):
        st.markdown("### :material/view_in_ar: 3D room preview")
        st.caption(f"{len(scene_items)} BOQ items placed approximately around a 12 ft x 12 ft room.")
        import streamlit.components.v1 as components
        components.html(build_room_scene(scene_items), height=540, scrolling=False)

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

    st.markdown("### :material/analytics: Project summary and executive KPIs")
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Total Estimated Cost", f"Rs. {est_cost:,.0f}" if est_cost else "Calculating...")
    with col_k2:
        st.metric("Client Budget", f"Rs. {budget_val:,.0f}" if budget_val else (saved_state.get("budget") or "N/A"))
    with col_k3:
        st.metric("Budget Health", budget_status, delta=f"Rs. {rem_budget:,.0f} reserve" if rem_budget else None)
    with col_k4:
        st.metric("Est. Project Duration", duration)

    # =========================================================================
    # MEMBER 5: COORDINATOR AGENT — FINAL MASTER REPORT TAB & SECTION
    # =========================================================================
    st.markdown('<div class="badge-coordinator">Member 5 — Master Project Dossier & Final Report</div>', unsafe_allow_html=True)
    st.markdown("### :material/description: Complete multi-agent turnkey report")
    st.markdown("Tamam 4 agents ke data ko synthesize karke banayi gayi master executive report.")

    if not saved_state.get("final_report"):
        if st.button(":material/auto_awesome: Synthesize final master report (Member 5)", key="gen_master_report_btn"):
            with st.spinner("Member 5 Coordinator Agent synthesizing executive dossier..."):
                updated_state = coordinator_agent(saved_state)
                st.session_state["interio_os_state"] = updated_state
                st.success("Master project report successfully generated.", icon=":material/check_circle:")
                st.rerun()

    if saved_state.get("final_report"):
        tab_report, tab_design, tab_boq, tab_cost, tab_timeline = st.tabs([
            ":material/description: Master project dossier (Member 5)",
            ":material/design_services: Design concept (Member 1)",
            ":material/inventory_2: BOQ and materials (Member 3)",
            ":material/payments: Financial and cost (Member 2)",
            ":material/calendar_month: Execution timeline (Member 4)"
        ])

        with tab_report:
            st.markdown(saved_state["final_report"])
            st.download_button(
                label="Download complete master dossier (.md)",
                data=saved_state["final_report"],
                file_name="InterioOS_Master_Project_Report.md",
                mime="text/markdown",
                key="dl_master_report"
            )

        with tab_design:
            st.markdown(saved_state.get("design_concept", "*No design concept found.*"))
            if saved_state.get("design_concept"):
                st.download_button(
                    label="Download design concept (.md)",
                    data=saved_state["design_concept"],
                    file_name="interior_design_concept.md",
                    mime="text/markdown",
                    key="dl_design_concept"
                )

        with tab_boq:
            if saved_state.get("boq_markdown"):
                st.markdown(saved_state["boq_markdown"])
            if saved_state.get("items"):
                with st.expander(f"Raw structured items ({len(saved_state['items'])} items)", expanded=False, icon=":material/search:"):
                    st.table(saved_state["items"])

        with tab_cost:
            if cost_info:
                st.markdown(f"**Estimated Cost:** `Rs. {est_cost:,.0f}` | **Budget Status:** `{budget_status}`")
                if cost_info.get("items"):
                    st.table(cost_info["items"])

        with tab_timeline:
            st.markdown(f"**:material/schedule: Total duration:** `{duration}`")
            st.markdown(saved_state.get("timeline_markdown", "*No timeline found.*"))

    else:
        # Step-by-Step Individual Agent Generation Controls
        st.markdown("---")
        st.markdown('<div class="badge-member">Member 1 — Design Concept</div>', unsafe_allow_html=True)
        st.markdown(saved_state.get("design_concept", ""))

        # Member 3: BOQ Trigger
        st.markdown("---")
        st.markdown('<div class="badge-member">Member 3 — BOQ Agent</div>', unsafe_allow_html=True)
        if st.button(":material/inventory_2: Generate material list and BOQ", key="step_boq_btn"):
            with st.spinner("Member 3 (Claude/Groq) generating BOQ..."):
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
        if st.button(":material/calendar_month: Generate execution timeline", key="step_timeline_btn"):
            with st.spinner("Member 4 generating schedule..."):
                updated_state = timeline_agent(saved_state)
                st.session_state["interio_os_state"] = updated_state
                st.rerun()

        if saved_state.get("timeline_markdown"):
            st.markdown(saved_state["timeline_markdown"])
