# API Reference

Complete API documentation for AgentKit.

## Agents

### HybridAgent

The `HybridAgent` combines local (AISuite) tools with remote (MCP) tools in a single agent.

#### Constructor

```python
from src.agents.hybrid_agent import HybridAgent

agent = HybridAgent()
```

#### Methods

##### `add_local_tool(func)`

Add a local Python function as a tool.

**Parameters:**
- `func` (callable): Python function with proper docstring and type hints

**Example:**
```python
def greet(name: str) -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

agent.add_local_tool(greet)
```

##### `add_mcp_server(server_name, command, args)` (async)

Connect to an MCP server.

**Parameters:**
- `server_name` (str): Identifier for the server
- `command` (str): Command to run the server (e.g., "uv", "python")
- `args` (List[str]): Command arguments (e.g., ["run", "server.py"])

**Returns:** List of tool names from the server

**Example:**
```python
await agent.add_mcp_server(
    "time",
    "uv",
    ["run", "src/servers/time_server.py"]
)
```

##### `process_query(query, model, max_turns)` (async)

Process a user query using available tools.

**Parameters:**
- `query` (str): User's question or request
- `model` (str, optional): LLM model to use. Default: "openai:gpt-4o-mini"
- `max_turns` (int, optional): Maximum tool-calling turns. Default: 5

**Returns:** str - Final response from the agent

**Example:**
```python
result = await agent.process_query(
    "What time is it?",
    model="openai:gpt-4o",
    max_turns=10
)
print(result)
```

##### `chat_loop(model)` (async)

Start an interactive chat session.

**Parameters:**
- `model` (str, optional): LLM model to use. Default: "openai:gpt-4o-mini"

**Example:**
```python
await agent.chat_loop()
```

**Special commands in chat:**
- `quit` - Exit the chat
- `help` - Show available commands
- `tools` - List all available tools

---

### MultiServerAgent

The `MultiServerAgent` uses only MCP servers (pure MCP architecture).

#### Constructor

```python
from src.agents.multi_server_agent import MultiServerAgent

agent = MultiServerAgent(api_key=None)
```

**Parameters:**
- `api_key` (str, optional): Anthropic API key. If not provided, uses `ANTHROPIC_API_KEY` from environment.

#### Methods

##### `add_server(config)` (async)

Add an MCP server to the agent.

**Parameters:**
- `config` (ServerConfig): Server configuration object

**Example:**
```python
from src.agents.multi_server_agent import ServerConfig

await agent.add_server(ServerConfig(
    name="time",
    command="uv",
    args=["run", "src/servers/time_server.py"],
    description="Time utilities"
))
```

##### `process_query(query, model, max_tokens)` (async)

Process a user query using tools from all connected servers.

**Parameters:**
- `query` (str): User's question or request
- `model` (str, optional): Claude model to use. Default: "claude-3-5-sonnet-20241022"
- `max_tokens` (int, optional): Maximum tokens in response. Default: 2048

**Returns:** str - Final response from the agent

**Example:**
```python
result = await agent.process_query(
    "Calculate 42 * 58 and tell me the time",
    model="claude-3-5-sonnet-20241022"
)
```

##### `chat_loop(model)` (async)

Start an interactive chat session.

**Parameters:**
- `model` (str, optional): Claude model to use

**Example:**
```python
await agent.chat_loop()
```

**Special commands:**
- `quit` - Exit the chat
- `help` - Show available commands
- `servers` - Show connected servers and their tools
- `clear` - Clear conversation history

---

## Data Classes

### ServerConfig

Configuration for an MCP server.

```python
from src.agents.multi_server_agent import ServerConfig

config = ServerConfig(
    name="my-server",
    command="uv",
    args=["run", "server.py"],
    description="Server description"
)
```

**Attributes:**
- `name` (str): Unique identifier for the server
- `command` (str): Command to execute
- `args` (List[str]): Command arguments
- `description` (str, optional): Human-readable description

---

## MCP Server Development

### FastMCP Basics

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
def my_function(arg: str) -> str:
    """Tool description"""
    return f"Result: {arg}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### Tool Decorator

The `@mcp.tool()` decorator converts a function into an MCP tool.

**Requirements:**
- Function must have a docstring
- Use type hints for parameters
- Document parameters in docstring (optional but recommended)

**Example:**
```python
@mcp.tool()
def process_data(
    data: str,
    uppercase: bool = False,
    max_length: int = 100
) -> str:
    """
    Process data with optional transformations.
    
    Args:
        data: The data to process
        uppercase: Convert to uppercase (default: False)
        max_length: Maximum length of output (default: 100)
    
    Returns:
        Processed data string
    """
    result = data[:max_length]
    if uppercase:
        result = result.upper()
    return result
```

### Running MCP Servers

**Standalone:**
```bash
uv run src/servers/my_server.py
```

**With Inspector (for debugging):**
```bash
npx @modelcontextprotocol/inspector uv run src/servers/my_server.py
```

---

## Type Definitions

### Tool Function Signature

Local tools should follow this pattern:

```python
def tool_name(
    required_arg: str,
    optional_arg: int = 0,
    flag: bool = False
) -> str:
    """
    Clear description of what the tool does.
    
    Args:
        required_arg: Description
        optional_arg: Description (default: 0)
        flag: Description (default: False)
    
    Returns:
        Description of return value
    """
    # Implementation
    return "result"
```

**Supported types:**
- str, int, float, bool
- List[type]
- Dict[str, type]
- Optional[type]

---

## Error Handling

### Agent Errors

```python
try:
    result = await agent.process_query("...")
except Exception as e:
    print(f"Error: {e}")
```

### MCP Connection Errors

```python
try:
    await agent.add_mcp_server("name", "command", ["args"])
except Exception as e:
    print(f"Failed to connect to server: {e}")
```

### Tool Execution Errors

Tools should handle errors gracefully and return error messages:

```python
@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide two numbers"""
    try:
        result = a / b
        return str(result)
    except ZeroDivisionError:
        return "Error: Cannot divide by zero"
    except Exception as e:
        return f"Error: {str(e)}"
```

---

## Examples

### Complete Hybrid Agent Example

```python
import asyncio
from src.agents.hybrid_agent import HybridAgent

# Local tools
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

async def main():
    # Initialize agent
    agent = HybridAgent()
    
    # Add local tools
    agent.add_local_tool(add)
    agent.add_local_tool(multiply)
    
    # Add MCP servers
    await agent.add_mcp_server(
        "time",
        "uv",
        ["run", "src/servers/time_server.py"]
    )
    
    # Process query
    result = await agent.process_query(
        "Add 10 and 20, then multiply by 2. Also tell me the time."
    )
    print(result)
    
    # Or start interactive chat
    await agent.chat_loop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Complete Multi-Server Example

```python
import asyncio
from src.agents.multi_server_agent import MultiServerAgent, ServerConfig

async def main():
    agent = MultiServerAgent()
    
    # Connect multiple servers
    servers = [
        ServerConfig("time", "uv", ["run", "src/servers/time_server.py"]),
        ServerConfig("math", "uv", ["run", "src/servers/math_server.py"]),
        ServerConfig("text", "uv", ["run", "src/servers/text_server.py"]),
    ]
    
    for server in servers:
        await agent.add_server(server)
    
    # Process query
    result = await agent.process_query(
        "What time is it? Calculate 15 * 23. Count words in this sentence."
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

1. **Always use type hints** - Helps with tool schema generation
2. **Write clear docstrings** - LLMs use these to understand tools
3. **Handle errors gracefully** - Return error messages, don't raise exceptions
4. **Keep tools focused** - One tool, one responsibility
5. **Test servers independently** - Before integrating with agents
6. **Use descriptive names** - For tools, parameters, and servers

---

For more examples, see the `examples/` directory in the repository.
