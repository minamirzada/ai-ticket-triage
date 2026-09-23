from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

ticket = "I can't log into my computer. It says my password expired and I have a court filing due at 11am!"

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    messages=[
        {
            "role": "user",
            "content": f"You are an IT help desk assistant. Read this support ticket and tell me its category, its priority (High, Medium, or Low), and a one-sentence summary.\n\nTicket: {ticket}",
        }
    ],
)

print(message.content[0].text)