import os

from dotenv import load_dotenv
from groq import Groq


# Load .env
load_dotenv()


# Get API key
api_key = os.getenv("GROQ_API_KEY")


if not api_key:

    print("ERROR: GROQ_API_KEY not found.")

    print(
        "Please check that your .env file "
        "contains GROQ_API_KEY."
    )

    exit()


print("API Key found successfully!")


# Create Groq client
client = Groq(
    api_key=api_key
)


# Send request
response = client.chat.completions.create(

    model="openai/gpt-oss-120b",

    messages=[

        {
            "role": "user",

            "content": (
                "Explain interior design budgeting "
                "in one simple sentence."
            )
        }
    ],

    temperature=0.2
)


print("\n================================")
print("          GROQ AI TEST")
print("================================")

print("\nGroq Response:")

print(
    response.choices[0].message.content
)

print("\n================================")
print("Groq connection successful!")
print("================================")