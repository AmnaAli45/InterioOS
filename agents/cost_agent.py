import csv
import os

from dotenv import load_dotenv
from groq import Groq


# Load environment variables
load_dotenv()


# =========================================================
# 1. LOAD PRICING DATA
# =========================================================

DEFAULT_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pricing_data.csv")

def load_prices(filename="data/pricing_data.csv"):

    prices = {}

    target_file = filename if os.path.exists(filename) else DEFAULT_CSV_PATH
    with open(target_file, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            prices[row["item"].lower()] = {
                "category": row["category"],
                "unit": row["unit"],
                "unit_price": float(row["unit_price"])
            }

    return prices


# =========================================================
# 2. CALCULATE INDIVIDUAL ITEM COST
# =========================================================

def calculate_item_cost(item, quantity, prices):

    item_key = item.lower()

    if item_key not in prices:

        return {
            "item": item,
            "quantity": quantity,
            "unit_price": 0,
            "total": 0,
            "status": "Price not available"
        }

    unit_price = prices[item_key]["unit_price"]

    total = quantity * unit_price

    return {
        "item": item,
        "quantity": quantity,
        "unit": prices[item_key]["unit"],
        "unit_price": unit_price,
        "total": total,
        "status": "OK"
    }


# =========================================================
# 3. CALCULATE TOTAL PROJECT COST
# =========================================================

def calculate_total(items, prices):

    results = []

    total_cost = 0

    for item in items:

        result = calculate_item_cost(
            item["name"],
            item["quantity"],
            prices
        )

        results.append(result)

        total_cost += result["total"]

    return results, total_cost


# =========================================================
# 4. CHECK BUDGET
# =========================================================

def check_budget(budget, estimated_cost):

    difference = budget - estimated_cost

    if difference >= 0:

        status = "Within Budget"

    else:

        status = "Over Budget"

    return {
        "budget": budget,
        "estimated_cost": estimated_cost,
        "remaining": difference,
        "status": status
    }


# =========================================================
# 5. TRACK ACTUAL SPENDING
# =========================================================

def track_actual_budget(
    budget,
    estimated_cost,
    actual_cost
):

    remaining_budget = budget - actual_cost

    estimated_difference = estimated_cost - actual_cost

    if remaining_budget >= 0:

        status = "Within Budget"

    else:

        status = "Budget Exceeded"

    return {

        "budget": budget,

        "estimated_cost": estimated_cost,

        "actual_cost": actual_cost,

        "remaining_budget": remaining_budget,

        "estimated_vs_actual": estimated_difference,

        "status": status
    }


# =========================================================
# 6. GROQ AI TEST / PROJECT ANALYSIS
# =========================================================

def ask_groq(requirement):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:

        return "Groq API key not found."

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(

        model="openai/gpt-oss-120b",

        messages=[

            {
                "role": "system",
                "content": (
                    "You are an interior design cost assistant. "
                    "Give a short and practical analysis of the "
                    "user's interior design requirement."
                )
            },

            {
                "role": "user",
                "content": requirement
            }
        ],

        temperature=0.2
    )

    return response.choices[0].message.content


# =========================================================
# 7. MAIN COST AGENT
# =========================================================

def cost_agent(state):

    prices = load_prices()

    items = state.get("items", [])

    budget = state.get("budget", 0)

    requirement = state.get(
        "requirement",
        ""
    )

    # Calculate costs using Python
    item_results, estimated_cost = calculate_total(
        items,
        prices
    )

    # Check budget
    budget_result = check_budget(
        budget,
        estimated_cost
    )

    # Groq analysis
    ai_analysis = ""

    if requirement:

        ai_analysis = ask_groq(
            requirement
        )

    # Store result in shared state
    state["cost"] = {

        "items": item_results,

        "estimated_cost": estimated_cost,

        "budget": budget_result["budget"],

        "remaining_budget": budget_result["remaining"],

        "status": budget_result["status"],

        "ai_analysis": ai_analysis
    }

    return state