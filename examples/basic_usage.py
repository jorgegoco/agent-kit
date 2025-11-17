"""
Basic usage example - Simple local tools with AISuite
"""
import aisuite as ai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def get_time() -> str:
    """Get the current time"""
    return datetime.now().strftime("%H:%M:%S")


def main():
    print("\n" + "="*60)
    print("Basic Usage Example - Local Tools")
    print("="*60 + "\n")
    
    # Initialize client
    client = ai.Client()
    
    # Use the tool
    response = client.chat.completions.create(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "What time is it?"}],
        tools=[get_time],
        max_turns=5
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print()


if __name__ == "__main__":
    main()
