"""
Hybrid Agent Example - Combining local and MCP tools
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.hybrid_agent import HybridAgent


def greeting(name: str) -> str:
    """Create a friendly greeting"""
    return f"Hello, {name}! Nice to meet you!"


async def main():
    print("\n" + "="*60)
    print("Hybrid Agent Example")
    print("="*60 + "\n")

    # Use async context manager for automatic cleanup
    async with HybridAgent() as agent:
        # Add local tool
        agent.add_local_tool(greeting)

        # Add MCP server (make sure time_server.py exists)
        try:
            await agent.add_mcp_server(
                "time",
                "uv",
                ["run", "src/servers/time_server.py"]
            )
        except Exception as e:
            print(f"Note: Could not connect to time server: {e}")
            print("That's okay - you can still test with local tools!\n")

        # Test query
        result = await agent.process_query(
            "Greet Bob and tell me what time it is"
        )

        print(f"\nFinal Result: {result}\n")

    # Cleanup happens automatically


if __name__ == "__main__":
    asyncio.run(main())
