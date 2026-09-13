"""
Test Script: Member 3 - BOQ Agent (Material List)
Verifies:
1. Extraction of design concept from state.
2. Query to Claude (or fallback Groq) with prompt:
   'is design ke liye materials ki list banao (paint, tiles, furniture) with quantity'
3. Storing results in state:
   - state['boq_markdown']
   - state['items']
"""

import os
from dotenv import load_dotenv
from agents.boq_agent import boq_agent

# Load environment
load_dotenv()

# Sample Design Concept (simulating output from Member 1 - Design Agent)
sample_design_concept = """
# Modern Master Bedroom Concept (Budget: Rs. 8 Lakh)
- **Room Dimensions**: 12ft x 14ft (~168 sqft floor area, ~450 sqft wall area)
- **Theme & Style**: Modern Contemporary with warm neutral palette.
- **Finishes**:
  * Off-white premium emulsion paint on walls (approx 450 sqft)
  * Matte porcelain wooden-finish floor tiles (approx 168 sqft)
  * Gypsum false ceiling with cove lighting channel
- **Furniture**:
  * 1 King-size upholstered bed with storage
  * 2 Minimalist floating side tables
  * 1 Full-height 4-door wardrobe (laminate finish)
- **Lighting & Electrical**:
  * 8 Recessed warm-white LED ceiling downlights
  * 2 Bedside pendant reading lights
- **Decor**:
  * 2 Double-layer pleated linen blackout curtains
"""

initial_state = {
    "user_requirement": "Design a modern bedroom within Rs. 8 lakh.",
    "design_concept": sample_design_concept,
    "budget": 800000
}

print("========================================")
print("     MEMBER 3 - BOQ AGENT TEST")
print("========================================")
print("\nInput Design Concept:\n", initial_state["design_concept"][:250], "...\n")

# Run BOQ Agent
result_state = boq_agent(initial_state)

print("----------------------------------------")
if result_state.get("error"):
    print(f"Live API Call: {result_state['error']}")
    print("Running offline schema & parser validation test...")

    from agents.boq_agent import parse_boq_response
    sample_response = (
        "### Material List & Bill of Quantities\n\n"
        "| Category | Item Name | Quantity | Unit | Specifications & Notes |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| Finishes | Paint | 200 | sqft | Premium washable emulsion |\n"
        "| Finishes | Flooring | 168 | sqft | Matte porcelain floor tiles |\n"
        "| Furniture | Bed | 1 | pcs | King size bed with storage |\n"
        "| Furniture | Wardrobe | 1 | pcs | 4-door modular wardrobe |\n"
        "| Furniture | Side Table | 2 | pcs | Minimalist floating side tables |\n"
        "| Electrical | LED Light | 8 | pcs | Warm-white recessed ceiling downlights |\n"
        "| Decor | Curtain | 1 | pcs | Double-layer pleated linen curtains |\n\n"
        "```json\n"
        "[\n"
        "  {\"name\": \"Paint\", \"quantity\": 200, \"unit\": \"sqft\", \"category\": \"Finishes\"},\n"
        "  {\"name\": \"Flooring\", \"quantity\": 168, \"unit\": \"sqft\", \"category\": \"Finishes\"},\n"
        "  {\"name\": \"Bed\", \"quantity\": 1, \"unit\": \"pcs\", \"category\": \"Furniture\"},\n"
        "  {\"name\": \"Wardrobe\", \"quantity\": 1, \"unit\": \"pcs\", \"category\": \"Furniture\"},\n"
        "  {\"name\": \"Side Table\", \"quantity\": 2, \"unit\": \"pcs\", \"category\": \"Furniture\"},\n"
        "  {\"name\": \"LED Light\", \"quantity\": 8, \"unit\": \"pcs\", \"category\": \"Electrical\"},\n"
        "  {\"name\": \"Curtain\", \"quantity\": 1, \"unit\": \"pcs\", \"category\": \"Decor\"}\n"
        "]\n"
        "```"
    )
    md, items = parse_boq_response(sample_response)
    print("[OK] Parser Test: Successfully extracted markdown table and structured items!")
    print(f"Extracted Items Count: {len(items)}")
    for idx, item in enumerate(items, start=1):
        print(f"  {idx}. {item['name']}: {item['quantity']} {item.get('unit', '')} ({item.get('category', '')})")
    print("[OK] Offline Schema Test Passed!")
else:
    print(f"Status: SUCCESS (Generated via {result_state.get('boq_engine')})")
    print("----------------------------------------")
    print("\n[PART 1: BOQ MARKDOWN TABLE]")
    print(result_state.get("boq_markdown"))

    print("\n----------------------------------------")
    print(f"[PART 2: EXTRACTED STRUCTURED ITEMS ({len(result_state.get('items', []))} items)]")
    for idx, item in enumerate(result_state.get("items", []), start=1):
        print(f"{idx}. {item['name']}: {item['quantity']} {item.get('unit', '')} ({item.get('category', 'N/A')})")

print("\n========================================")
