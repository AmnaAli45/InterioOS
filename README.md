# InterioOS AI — Multi-Agent Interior Design System

**InterioOS AI** is an intelligent multi-agent platform designed to assist interior designers from concept to execution. Designers provide high-level project requirements (e.g., *"Design a modern bedroom for a client within a budget of Rs. 8 lakh"*), and specialized AI agents collaboratively generate concepts, estimate material costs, generate Bills of Quantities (BOQ), recommend vendors, and manage timelines.

---

## 👥 Member 1 — Design Agent

### **Responsibility & Deliverables:**
1. **Python Function (`design_agent_node` / `generate_design_concept`)**:
   - Takes client requirements (e.g., room type, style, budget, preferences).
2. **LLM API Communication (Groq Ultra-Fast Engine)**:
   - Sends targeted prompt: *"is requirement ke liye design concept do"*.
   - Instructs the model to produce structured design concepts in seconds (theme, spatial zoning, color palette, lighting, materials, furniture).
3. **LangGraph State Preservation**:
   - Saves generated response into `state["design_concept"]` within `InterioOSState`.
   - Makes the concept accessible for downstream team agents (Cost Estimator, BOQ, Vendor, Coordinator).

---

---

## 👥 Member 3 — BOQ Agent (Bill of Quantities / Material List)

### **Responsibility & Deliverables:**
1. **LangGraph Node (`boq_agent` / `boq_agent_node`)**:
   - Takes `design_concept` from Member 1.
2. **LLM API Communication (Claude / Groq Engine)**:
   - Queries Claude: *"is design ke liye materials ki list banao (paint, tiles, furniture) with quantity"*.
   - Produces a comprehensive Material List (Paint, Tiles/Flooring, Carpentry/Furniture, Lighting, False Ceiling, Decor) with realistic quantities and units.
3. **LangGraph State Preservation**:
   - Saves formatted Markdown table into `state["boq_markdown"]`.
   - Saves structured items into `state["items"]` (`[{"name": "...", "quantity": ..., "unit": "..."}]`) for downstream **Member 2 (Cost Estimator)**.

---

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Frontend / UI**: Streamlit
- **Agent Orchestration**: LangGraph (`StateGraph`)
- **LLM / AI Engine**: Anthropic Claude (`claude-3-5-sonnet`) with Groq fallback
- **Data & Tables**: Pandas, CSV

---

## 📁 Project Structure

```text
InterioOS/
├── agents/
│   ├── __init__.py          # Agent package exports
│   ├── boq_agent.py         # Member 3: BOQ Agent (Claude/Groq)
│   └── cost_agent.py        # Member 2: Cost Estimator
├── data/
│   └── pricing_data.csv     # Unit rates for finishes & furniture
├── design_agent.py          # Member 1: Design Agent (LangGraph + Groq)
├── app.py                   # Streamlit UI with Design & BOQ generation
├── test_boq.py              # Member 3 BOQ Agent standalone test
├── test_langgraph_pipeline.py # 3-Agent end-to-end pipeline test
├── test_cost.py             # Member 2 Cost Agent test
├── test_groq.py             # Groq connectivity test
├── test_langgraph_cost.py   # Cost Agent LangGraph test
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
└── README.md                # Documentation and instructions
```

---

## 🚀 Getting Started

### 1. Configure Environment Variables
Create or edit `.env` in the root directory:
```env
# Groq (Fast Inference)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Anthropic Claude (Member 3 BOQ Agent)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 2. Run with Streamlit
Launch the interactive web interface:
```bash
streamlit run app.py
```

### 3. Run Tests from Terminal (CLI)
```bash
# Test Member 3 BOQ Agent
python test_boq.py

# Test Full Multi-Agent Pipeline (Member 1 -> 3 -> 2)
python test_langgraph_pipeline.py

# Test Member 2 Cost Agent
python test_cost.py
```

---

## 🔄 Shared LangGraph State Schema

```python
class InterioOSState(TypedDict, total=False):
    user_requirement: str          # Input client requirement
    budget: Optional[str]          # Project budget (e.g. 'Rs. 8 Lakh')
    room_type: Optional[str]       # Room category
    style: Optional[str]           # Aesthetic style
    model: Optional[str]           # Model used
    design_concept: Optional[str]  # Member 1 Output: Design concept
    boq_markdown: Optional[str]    # Member 3 Output: Markdown BOQ material list
    items: Optional[list]          # Member 3 Output: Structured items for cost calculation
    boq_status: Optional[str]      # Member 3 Status: 'completed' | 'failed'
    cost: Optional[Dict[str, Any]] # Member 2 Output: Cost calculation breakdown
    status: Optional[str]          # Workflow status
    error: Optional[str]           # Error message if any
```
