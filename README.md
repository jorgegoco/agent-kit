# AgentKit

A flexible agent framework that seamlessly combines **AISuite** (local tools) and **Model Context Protocol (MCP)** (remote tool servers) for powerful, modular AI agent development.

## ✨ Features

- 🔧 **Hybrid Architecture** - Use both local tools (AISuite) and remote tools (MCP servers) in the same agent
- 🌐 **Multi-Server Support** - Connect to multiple MCP servers simultaneously
- 🚀 **Easy to Extend** - Add new tools with minimal code
- 📦 **Production Ready** - Clean architecture with proper separation of concerns
- ⚡ **Fast Setup** - Managed with `uv` for lightning-fast dependency management

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url> agent-kit
cd agent-kit

# Install dependencies
uv sync

# Configure environment
cp .env.template .env
# Edit .env and add your API keys
```

### Basic Usage

```python
from src.agents.hybrid_agent import HybridAgent
import asyncio

async def main():
    agent = HybridAgent()
    
    # Add a local tool
    def greet(name: str) -> str:
        """Say hello to someone"""
        return f"Hello, {name}!"
    
    agent.add_local_tool(greet)
    
    # Add an MCP server
    await agent.add_mcp_server(
        "time",
        "uv",
        ["run", "src/servers/time_server.py"]
    )
    
    # Use both types of tools seamlessly
    result = await agent.process_query(
        "Greet Alice and tell me what time it is"
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📁 Project Structure

```
agent-kit/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── hybrid_agent.py      # Combines local + MCP tools
│   │   └── multi_server_agent.py # Pure MCP architecture
│   ├── servers/             # MCP server implementations
│   │   ├── time_server.py
│   │   ├── math_server.py
│   │   └── text_server.py
│   └── utils/               # Shared utilities
├── examples/                # Usage examples
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## 📚 Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)** - Detailed setup and usage instructions
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Design patterns and architecture decisions
- **[API Reference](docs/API.md)** - Detailed API documentation

## 🎯 Use Cases

### Hybrid Agent (Recommended)
Best for most projects - combines local tools for simple operations with MCP servers for complex, reusable functionality:

```python
agent = HybridAgent()
agent.add_local_tool(quick_calculation)  # Fast, simple
await agent.add_mcp_server("research", ...)  # Complex, reusable
```

### Multi-Server Agent
Ideal for production systems with multiple specialized services:

```python
agent = MultiServerAgent()
await agent.add_server(ServerConfig("research", ...))
await agent.add_server(ServerConfig("database", ...))
await agent.add_server(ServerConfig("analytics", ...))
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
pytest

# Format code
black src/ tests/ examples/

# Lint code
ruff check src/ tests/ examples/
```

### Creating a New MCP Server

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_function(arg: str) -> str:
    """Description of what this tool does"""
    return f"Processed: {arg}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built on [Anthropic's Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [AISuite](https://github.com/andrewyng/aisuite) for flexible LLM interactions
- Managed with [uv](https://github.com/astral-sh/uv) for fast dependency management

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-username/agent-kit/issues)
- 💬 [Discussions](https://github.com/your-username/agent-kit/discussions)

---

**Built with ❤️ for the AI agent community**
