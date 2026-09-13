"""
InterioOS AI - Test Script for Member 5: Coordinator Agent & Report Aggregator
Tests:
1. Output collection from Member 1 (Design), Member 3 (BOQ), Member 2 (Cost), Member 4 (Timeline).
2. Final Combined Master Report generation.
3. LangGraph 5-Agent graph compilation verification.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from design_agent import InterioOSState
from agents.coordinator_agent import (
    coordinator_agent,
    build_full_pipeline,
    build_final_master_report
)

def test_coordinator_aggregation():
    print("================================================================")
    print(" TEST: Member 5 Coordinator Agent Output Aggregation & Report ")
    print("================================================================")

    # Mock full upstream state populated by Members 1, 3, 2, 4
    mock_state: InterioOSState = {
        "user_requirement": "Design a luxury master bedroom with walking wardrobe within Rs. 8 lakh budget.",
        "budget": "Rs. 8 Lakh",
        "room_type": "Master Bedroom",
        "style": "Contemporary Luxury",
        "design_concept": (
            "### 1. Concept Summary\n"
            "An elegant luxury bedroom featuring acoustic fluted wood paneling, warm ambient indirect lighting, "
            "and premium Italian marble texture flooring.\n\n"
            "### 2. Spatial Layout\n"
            "King-size bed positioned along the central focal wall, floating nightstands, and a walk-in wardrobe partition."
        ),
        "boq_markdown": (
            "| Category | Item Name | Quantity | Unit | Specifications |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| Finishes | Paint | 250 | sqft | Premium washable emulsion |\n"
            "| Finishes | Flooring | 180 | sqft | Vitrified matte tiles |\n"
            "| Furniture | Bed | 1 | pcs | King size upholstered bed |\n"
            "| Furniture | Wardrobe | 1 | pcs | 4-door modular acrylic wardrobe |\n"
            "| Electrical | LED Light | 10 | pcs | Warm white 9W ceiling downlights |"
        ),
        "items": [
            {"name": "Paint", "quantity": 250, "unit": "sqft", "category": "Finishes"},
            {"name": "Flooring", "quantity": 180, "unit": "sqft", "category": "Finishes"},
            {"name": "Bed", "quantity": 1, "unit": "pcs", "category": "Furniture"},
            {"name": "Wardrobe", "quantity": 1, "unit": "pcs", "category": "Furniture"},
            {"name": "LED Light", "quantity": 10, "unit": "pcs", "category": "Electrical"}
        ],
        "cost": {
            "estimated_cost": 385000,
            "budget": 800000,
            "remaining_budget": 415000,
            "status": "Within Budget",
            "items": [
                {"item": "Paint", "quantity": 250, "unit": "sqft", "unit_price": 50, "total": 12500, "status": "OK"},
                {"item": "Flooring", "quantity": 180, "unit": "sqft", "unit_price": 120, "total": 21600, "status": "OK"},
                {"item": "Bed", "quantity": 1, "unit": "pcs", "unit_price": 45000, "total": 45000, "status": "OK"},
                {"item": "Wardrobe", "quantity": 1, "unit": "pcs", "unit_price": 60000, "total": 60000, "status": "OK"},
                {"item": "LED Light", "quantity": 10, "unit": "pcs", "unit_price": 400, "total": 4000, "status": "OK"}
            ]
        },
        "timeline_markdown": (
            "### Overall Project Duration: 4 Weeks (28 Days)\n\n"
            "- **Phase 1: Site Survey & Material Orders (Days 1–3)**\n"
            "- **Phase 2: Civil, Conduiting & False Ceiling (Days 4–9)**\n"
            "- **Phase 3: Flooring & Wall Putty (Days 10–15)**\n"
            "- **Phase 4: Carpentry & Fixed Wardrobe (Days 16–22)**\n"
            "- **Phase 5: Painting, Fixtures & Snagging (Days 23–28)**"
        ),
        "estimated_duration": "4 Weeks (28 Days)"
    }

    # Run Member 5 Coordinator Agent
    result = coordinator_agent(mock_state)

    assert result.get("coordinator_status") == "completed", "Coordinator status should be completed"
    assert result.get("final_report") is not None, "Final report should be generated"
    assert "MASTER PROJECT DOSSIER" in result["final_report"], "Report header missing"
    assert "Member 1: Design Agent" in result["final_report"], "Design section missing in report"
    assert "Member 3: BOQ Agent" in result["final_report"], "BOQ section missing in report"
    assert "Member 2: Cost Estimator" in result["final_report"], "Cost section missing in report"
    assert "Member 4: Timeline Agent" in result["final_report"], "Timeline section missing in report"

    print("\n[PASS] Member 5 Coordinator Agent successfully aggregated all 4 agent outputs!")
    print(f"Engine Used: {result.get('coordinator_engine')}")
    print(f"Report Length: {len(result['final_report'])} characters\n")
    print("--- PREVIEW OF FINAL MASTER REPORT ---")
    print(result["final_report"][:900])
    print("\n... [Report Truncated for display] ...\n")


def test_full_pipeline_compilation():
    print("================================================================")
    print(" TEST: LangGraph 5-Agent Pipeline Graph Build & Compilation     ")
    print("================================================================")

    pipeline = build_full_pipeline()
    assert pipeline is not None, "Pipeline graph failed to compile"

    print("[PASS] LangGraph 5-Agent pipeline graph compiled successfully!")
    print("Nodes: ['design_agent', 'boq_agent', 'cost_agent', 'timeline_agent', 'coordinator_agent']")
    print("Flow: START -> design_agent -> boq_agent -> cost_agent -> timeline_agent -> coordinator_agent -> END")


if __name__ == "__main__":
    test_coordinator_aggregation()
    test_full_pipeline_compilation()
    print("\n[SUCCESS] ALL MEMBER 5 TESTS PASSED SUCCESSFULLY!")
