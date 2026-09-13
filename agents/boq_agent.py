"""
InterioOS AI - Member 3: BOQ Agent (Bill of Quantities / Material List)
Tech Stack: Python, Anthropic (Claude) / Groq fallback, LangGraph

Role & Responsibility:
1. Design Agent (Member 1) ka output (design_concept) state se lena.
2. Claude se prompt pochna: "is design ke liye materials ki list banao (paint, tiles, furniture) with quantity".
3. Response ko LangGraph State mein save karna:
   - state["boq_markdown"]: Formatted Markdown BOQ table for display.
   - state["items"]: Structured item list for Member 2 (Cost Agent).
"""

import os
import re
import json
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def parse_boq_response(response_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parses LLM response to separate Markdown table and structured items JSON.
    Returns (boq_markdown, structured_items).
    """
    items = []
    markdown_content = response_text

    # Extract JSON code block if present
    json_match = re.search(r"```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```", response_text, re.DOTALL)
    if json_match:
        try:
            items = json.loads(json_match.group(1))
            # Remove the JSON code block from markdown display for clean UI
            markdown_content = response_text[:json_match.start()].strip()
            after_json = response_text[json_match.end():].strip()
            if after_json:
                markdown_content += f"\n\n{after_json}"
        except Exception:
            pass

    # Fallback parser if JSON block was not strictly formatted
    if not items:
        # Search for any raw JSON array
        bracket_match = re.search(r"(\[\s*\{\s*\"name\".*?\}\s*\])", response_text, re.DOTALL)
        if bracket_match:
            try:
                items = json.loads(bracket_match.group(1))
            except Exception:
                pass

    # Normalize item structures
    normalized_items = []
    for it in items:
        if isinstance(it, dict) and "name" in it:
            try:
                qty = float(it.get("quantity", 1))
            except (ValueError, TypeError):
                qty = 1.0
            normalized_items.append({
                "name": str(it.get("name", "")).strip(),
                "quantity": qty,
                "unit": str(it.get("unit", "pcs")).strip(),
                "category": str(it.get("category", "General")).strip()
            })

    return markdown_content.strip(), normalized_items


def query_claude(prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Queries Anthropic Claude API."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    messages_payload: Any = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=model,
        max_tokens=3000,
        system=system_prompt,
        messages=messages_payload
    )
    text_parts = [getattr(block, "text", "") for block in response.content]
    return "".join(text_parts).strip()


def query_groq_fallback(prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Fallback query to Groq when Claude key is unavailable."""
    from groq import Groq
    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        model=model,
        temperature=0.3,
        max_tokens=3000,
    )
    raw_text = chat_completion.choices[0].message.content or ""
    return raw_text.strip()


def boq_agent(state: Any) -> Any:
    """
    Member 3 - BOQ Agent Node:
    1. Extracts design_concept from state.
    2. Sends prompt to Claude: 'is design ke liye materials ki list banao (paint, tiles, furniture) with quantity'.
    3. Saves generated BOQ table and structured items into LangGraph state.
    """
    # 1. Design ka output lena
    design_concept = (
        state.get("design_concept") or
        state.get("user_requirement") or
        state.get("requirement") or
        ""
    )

    if not design_concept.strip():
        state["boq_status"] = "failed"
        state["error"] = "No design concept or requirement found in state to generate BOQ."
        return state

    # System Prompt for Bill of Quantities Specialist
    system_prompt = (
        "You are an expert Interior Design Quantity Surveyor & BOQ (Bill of Quantities) Specialist for InterioOS AI.\n"
        "Your role is to analyze the interior design concept and produce a comprehensive, realistic material & item list.\n\n"
        "Format your response in TWO parts:\n\n"
        "PART 1: A structured Markdown Table with columns:\n"
        "| Category | Item Name | Quantity | Unit | Specifications & Notes |\n"
        "Include all required materials: paint, tiles/flooring, carpentry/furniture, lighting, false ceiling, decor, and hardware.\n\n"
        "PART 2: At the very end of your response, provide a valid JSON code block with structured items for downstream cost calculation:\n"
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
        "```\n"
        "Ensure item names match standard interior items (Paint, Flooring, Bed, Wardrobe, Side Table, LED Light, Curtain, Sofa, False Ceiling, Wallpaper, Kitchen Cabinet)."
    )

    # Required Prompt as specified by Member 3 task:
    user_prompt = (
        f"is design ke liye materials ki list banao (paint, tiles, furniture) with quantity:\n\n"
        f"--- DESIGN CONCEPT ---\n"
        f"{design_concept}\n"
        f"--- END DESIGN CONCEPT ---"
    )

    # API credentials check: Claude (Primary) with Groq (Fallback)
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    response_text = ""
    llm_provider = ""

    try:
        if anthropic_api_key:
            llm_provider = "Claude"
            model = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            response_text = query_claude(user_prompt, system_prompt, model, anthropic_api_key)
        elif groq_api_key:
            llm_provider = "Groq (Fallback)"
            model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
            response_text = query_groq_fallback(user_prompt, system_prompt, model, groq_api_key)
        else:
            state["boq_status"] = "failed"
            state["error"] = "Neither ANTHROPIC_API_KEY nor GROQ_API_KEY is configured in .env."
            return state

        # Parse response into markdown display and structured items
        boq_md, parsed_items = parse_boq_response(response_text)

        # 3. Response state mein save karna
        state["boq_markdown"] = boq_md
        state["items"] = parsed_items
        state["boq_status"] = "completed"
        state["boq_engine"] = llm_provider
        state["error"] = None

    except Exception as e:
        state["boq_status"] = "failed"
        state["error"] = f"BOQ generation failed via {llm_provider or 'LLM'}: {str(e)}"

    return state


def boq_agent_node(state: Any) -> Any:
    """LangGraph node alias for boq_agent."""
    return boq_agent(state)


if __name__ == "__main__":
    print("--- InterioOS AI: Member 3 - BOQ Agent (Material List) ---")
    mock_concept = (
        "Design Concept for Master Bedroom (Rs. 8 Lakh):\n"
        "- Wall Finishes: Neutral off-white paint (approx 200 sqft) with accent textured wall.\n"
        "- Flooring: Premium wooden laminate flooring (168 sqft).\n"
        "- Furniture: King size upholstered bed with hydraulic storage, 2 matching side tables, 4-door wardrobe in matte laminate.\n"
        "- Lighting: 8 warm-white recessed LED ceiling downlights and ambient strip lights.\n"
        "- Furnishing: Blackout double-layer pleated curtains."
    )

    test_state = {"design_concept": mock_concept, "budget": 800000}
    result_state = boq_agent(test_state)

    if result_state.get("error"):
        print(f"[ERROR]: {result_state.get('error')}")
    else:
        print(f"[SUCCESS] BOQ generated via {result_state.get('boq_engine')}!")
        print("\n--- BOQ Table ---")
        print((result_state.get("boq_markdown") or "")[:400] + "...")
        print(f"\nExtracted Items ({len(result_state.get('items', []))} items):")
        for item in result_state.get("items", [])[:5]:
            print(f" - {item['name']}: {item['quantity']} {item.get('unit', '')}")
