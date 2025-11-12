# Getting Started with AgentKit

This guide will help you set up and start using AgentKit in minutes.

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- API keys for Anthropic and/or OpenAI

### Installing uv

```bash
# Using pip
pip install uv

# Or using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url> agent-kit
cd agent-kit
```

### 2. Install Dependencies

```bash
# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

### 3. Configure Environment

```bash
# Copy the environment template
cp .env.template .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Your `.env` file should look like:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx

DEFAULT_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
DEFAULT_OPENAI_MODEL=gpt-4o-mini
```

## Your First Agent

### Example 1: Local Tools Only (Simple)

Create a file `my_first_agent.py`:

```python
import aisuite as ai

def get_current_time():
    """Get the current time"""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

def main():
    client = ai.Client()

    response = client.chat.completions.create(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "What time is it?"}],
        tools=[get_current_time],
        max_turns=5
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
```

Run it:

```bash
uv run my_first_agent.py
```

### Example 2: Hybrid Agent (Recommended)

Create `my_hybrid_agent.py`:

```python
import asyncio
from src.agents.hybrid_agent import HybridAgent

def quick_math(a: int, b: int) -> int:
    """Add two numbers quickly"""
    return a + b

async def main():
    agent = HybridAgent()

    # Add local tool
    agent.add_local_tool(quick_math)

    # Add MCP server
    await agent.add_mcp_server(
        "time",
        "uv",
        ["run", "src/servers/time_server.py"]
    )

    # Use both types of tools
    result = await agent.process_query(
        "Add 42 and 58, then tell me what time it is"
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
uv run my_hybrid_agent.py
```

### Example 3: Multi-Server Agent (Production)

Create `my_multi_server.py`:

```python
import asyncio
from src.agents.multi_server_agent import MultiServerAgent, ServerConfig

async def main():
    agent = MultiServerAgent()

    # Connect to multiple servers
    await agent.add_server(ServerConfig(
        name="time",
        command="uv",
        args=["run", "src/servers/time_server.py"],
        description="Time and date utilities"
    ))

    await agent.add_server(ServerConfig(
        name="math",
        command="uv",
        args=["run", "src/servers/math_server.py"],
        description="Mathematical operations"
    ))

    # Start interactive chat
    await agent.chat_loop()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
uv run my_multi_server.py
```

## Creating Your First MCP Server

Create a file `src/servers/my_server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-custom-server")

@mcp.tool()
def process_text(text: str, uppercase: bool = False) -> str:
    """
    Process text with optional transformations.

    Args:
        text: The text to process
        uppercase: Convert to uppercase (default: False)

    Returns:
        Processed text
    """
    result = text.strip()
    if uppercase:
        result = result.upper()
    return result

@mcp.tool()
def count_words(text: str) -> int:
    """Count the number of words in text"""
    return len(text.split())

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

Test your server:

```bash
uv run src/servers/my_server.py
```

Use it in an agent:

```python
await agent.add_mcp_server(
    "custom",
    "uv",
    ["run", "src/servers/my_server.py"]
)
```

## Common Commands

### Development

```bash
# Install dev dependencies
uv sync --extra dev

# Format code
black src/ tests/ examples/

# Lint code
ruff check src/ tests/ examples/

# Run tests
pytest
```

## Project Structure

After setup, your project will look like:

```
agent-kit/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── hybrid_agent.py
│   │   └── multi_server_agent.py
│   ├── servers/
│   │   ├── __init__.py
│   │   ├── time_server.py
│   │   ├── math_server.py
│   │   └── text_server.py
│   └── utils/
│       └── __init__.py
├── examples/
│   ├── basic_usage.py
│   └── hybrid_example.py
├── tests/
│   └── __init__.py
├── docs/
│   ├── GETTING_STARTED.md (this file)
│   ├── ARCHITECTURE.md
│   └── API.md
├── .env
├── .env.template
├── .gitignore
├── pyproject.toml
└── README.md
```

## Troubleshooting

### "Module not found" errors

```bash
# Make sure dependencies are installed
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### MCP Server connection fails

```bash
# Test server individually
uv run src/servers/time_server.py

# Check that the path is correct
# Make sure uv is available when running
```

### Import errors from src

Add to the top of your script:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

## Next Steps

- Read the [Architecture Overview](ARCHITECTURE.md) to understand design choices
- Check out the [API Reference](API.md) for detailed documentation
- Explore the `examples/` directory for more use cases
- Build your own custom MCP servers
- Join the community and share your creations!

## Getting Help

- 📖 Check the [documentation](../docs/)
- 🐛 [Report issues](https://github.com/jorgegoco/agent-kit/issues)
- 💬 [Ask questions](https://github.com/jorgegoco/agent-kit/discussions)

Happy building! 🚀
