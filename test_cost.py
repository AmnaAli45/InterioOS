from agents.cost_agent import cost_agent


state = {

    "requirement":
        "Design a modern bedroom for a client "
        "within a budget of Rs. 8 lakh.",

    "budget": 800000,

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


result = cost_agent(state)


print("\n========================================")
print("       AI INTERIOR DESIGN MANAGER")
print("========================================")

print("\n========== COST ESTIMATION ==========\n")


for item in result["cost"]["items"]:

    print(

        f"{item['item']}: "
        f"{item['quantity']} × "
        f"Rs. {item['unit_price']:,.0f} = "
        f"Rs. {item['total']:,.0f}"

    )


print("\n----------------------------------------")


print(
    f"Estimated Cost: "
    f"Rs. {result['cost']['estimated_cost']:,.0f}"
)


print(
    f"Budget: "
    f"Rs. {result['cost']['budget']:,.0f}"
)


print(
    f"Remaining Budget: "
    f"Rs. {result['cost']['remaining_budget']:,.0f}"
)


print(
    f"Status: "
    f"{result['cost']['status']}"
)


print("\n========== GROQ ANALYSIS ==========\n")

print(
    result["cost"]["ai_analysis"]
)


print("\n========================================")