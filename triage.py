import json
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an IT help desk triage assistant.
Read the support ticket and respond with ONLY a JSON object, with no other text, in this exact format:
{
  "category": one of "Account Access", "Hardware", "Software", "Network", "Other",
  "priority": one of "High", "Medium", "Low",
  "summary": a one-sentence summary of the problem,
  "suggested_reply": a short, friendly first reply to the user
}"""


def triage_ticket(ticket):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": ticket}],
    )
    text = message.content[0].text
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


result = triage_ticket("The printer on the 3rd floor is printing kind of faded. Not urgent, just letting you know.")

print("Category:", result["category"])
print("Priority:", result["priority"])
print("Summary:", result["summary"])
print("Suggested reply:", result["suggested_reply"])