# InterioOS AI — Multi-Agent Interior Design System

**InterioOS AI** is an intelligent multi-agent platform designed to assist interior designers from concept to execution. Designers provide high-level project requirements (e.g., *"Design a modern bedroom for a client within a budget of Rs. 8 lakh"*), and specialized AI agents collaboratively generate concepts, estimate material costs, generate Bills of Quantities (BOQ), recommend vendors, and manage timelines.

---

## 👥 Member 1 — Design Agent

### **Responsibility & Deliverables:**
1. **Python Function (`design_agent_node` / `generate_design_concept`)**:
   - Takes client requirements (e.g., room type, style, budget, preferences).
2. **OpenRouter API Communication**:
   - Sends targeted prompt: *"is requirement ke liye design concept do"*.
   - Instructs the model to produce structured design concepts (theme, spatial zoning, color palette, lighting, materials, furniture).
3. **LangGraph State Preservation**:
   - Saves generated response into `state["design_concept"]` within `InterioOSState`.
   - Makes the concept accessible for downstream team agents (Cost Estimator, BOQ, Vendor, Coordinator).

---

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Frontend / UI**: Streamlit
- **Agent Orchestration**: LangGraph (`StateGraph`)
- **LLM / AI Engine**: OpenRouter API (`nvidia/nemotron-3.5-lightning:free` / `anthropic/claude-3.5-sonnet`)

---

## 📁 Project Structure

```text
InteriorOSAI/
├── design_agent.py      # Core Member 1 module: LangGraph State & OpenRouter node
├── app.py               # Streamlit interactive UI & state inspector
├── requirements.txt     # Dependencies (requests, langgraph, streamlit, etc.)
├── .env                 # Local API configuration (ignored by git)
├── .env.example         # Environment template for OPENROUTER_API_KEY
├── .gitignore           # Protects .env secrets and cache directories
└── README.md            # Documentation and instructions
```

---

## 🚀 Getting Started

### 1. Configure Environment Variables
Create or edit `.env` in the root directory:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```
*(Get your key from [openrouter.ai/keys](https://openrouter.ai/keys))*

### 2. Run with Streamlit
Launch the interactive web interface:
```bash
streamlit run app.py
```

### 3. Run directly from Terminal (CLI)
```bash
python design_agent.py
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
    design_concept: Optional[str]  # Member 1 output saved here
    status: Optional[str]          # 'concept_generated' | 'failed'
    error: Optional[str]           # Error message if any
```

Downstream agents (Member 2 Cost Estimator, Member 3 BOQ Agent, Member 4 Vendor Agent, etc.) receive this state directly and process `state["design_concept"]`.
