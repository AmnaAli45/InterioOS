from typing import TypedDict, cast, Any

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from agents.cost_agent import cost_agent


# =========================================================
# PROJECT STATE
# =========================================================

class ProjectState(TypedDict, total=False):

    requirement: str

    budget: float

    items: list

    cost: dict


# =========================================================
# CREATE GRAPH
# =========================================================

graph = StateGraph(ProjectState)


# Add Cost Agent
graph.add_node(
    "cost",
    cost_agent
)


# Connect nodes
graph.add_edge(
    START,
    "cost"
)

graph.add_edge(
    "cost",
    END
)


# Compile graph
app = graph.compile()


# =========================================================
# TEST INPUT
# =========================================================

initial_state: ProjectState = {

    "requirement":
        "Modern bedroom 12x14 feet",

    "budget":
        800000,

    "items": [

        {
            "name": "Paint",
            "quantity": 200
        },

        {
            "name": "Flooring",
            "quantity": 168
        },

        {
            "name": "Bed",
            "quantity": 1
        },

        {
            "name": "Wardrobe",
            "quantity": 1
        },

        {
            "name": "Side Table",
            "quantity": 2
        },

        {
            "name": "LED Light",
            "quantity": 8
        },

        {
            "name": "Curtain",
            "quantity": 1
        }
    ]
}


# Run LangGraph
result: Any = app.invoke(
    initial_state
)


# =========================================================
# OUTPUT
# =========================================================

print("\n========================================")
print("       MEMBER 2 - COST AGENT")
print("========================================")

print("\nProject:")

print(
    result["requirement"]
)


print("\nBudget:")

print(
    f"Rs. {result['budget']:,.0f}"
)


print("\nEstimated Cost:")

print(
    f"Rs. {result['cost']['estimated_cost']:,.0f}"
)


print("\nRemaining Budget:")

print(
    f"Rs. {result['cost']['remaining_budget']:,.0f}"
)


print("\nBudget Status:")

print(
    result["cost"]["status"]
)


print("\n========================================")