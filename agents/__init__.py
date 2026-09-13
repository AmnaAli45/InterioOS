"""
InterioOS AI - Multi-Agent Architecture
Member 1: Design Agent (design_agent.py)
Member 2: Cost Agent (agents.cost_agent)
Member 3: BOQ Agent (agents.boq_agent)
Member 4: Timeline Agent (agents.timeline_agent)
Member 5: Coordinator Agent & LangGraph Orchestrator (agents.coordinator_agent)
"""

try:
    from .cost_agent import cost_agent
    from .boq_agent import boq_agent, boq_agent_node
    from .timeline_agent import timeline_agent, timeline_agent_node
    from .coordinator_agent import (
        coordinator_agent,
        coordinator_agent_node,
        build_full_pipeline,
        run_interioos_pipeline,
        build_final_master_report
    )
except ImportError:
    from agents.cost_agent import cost_agent
    from agents.boq_agent import boq_agent, boq_agent_node
    from agents.timeline_agent import timeline_agent, timeline_agent_node
    from agents.coordinator_agent import (
        coordinator_agent,
        coordinator_agent_node,
        build_full_pipeline,
        run_interioos_pipeline,
        build_final_master_report
    )

__all__ = [
    "cost_agent",
    "boq_agent",
    "boq_agent_node",
    "timeline_agent",
    "timeline_agent_node",
    "coordinator_agent",
    "coordinator_agent_node",
    "build_full_pipeline",
    "run_interioos_pipeline",
    "build_final_master_report",
]

