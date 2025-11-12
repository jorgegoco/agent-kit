# Integrating AISuite, MCP Servers, and MCP Clients
## A Comprehensive Architecture Guide

## 🔍 Understanding the Three Pieces

### 1. **AISuite (M3_UGL_1)** - Direct Tool Calling
- **What it does**: Converts Python functions directly into LLM tools
- **Where tools run**: Locally in the same process
- **Communication**: Direct function calls
- **Best for**: Simple, single-application scenarios

```python
# AISuite Pattern
import aisuite as ai

def my_function():
    """Tool description"""
    return "result"

client = ai.Client()
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[{"role": "user", "content": "Use my tool"}],
    tools=[my_function],  # Pass function directly
    max_turns=5
)
```

### 2. **MCP Server (L4)** - Standardized Tool Service
- **What it does**: Exposes tools through a standardized protocol
- **Where tools run**: Separate process (server)
- **Communication**: MCP protocol via stdio/HTTP
- **Best for**: Sharing tools across applications, modular architecture

```python
# MCP Server Pattern (FastMCP)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_function():
    """Tool description"""
    return "result"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### 3. **MCP Client (L5)** - Connecting to Tool Services
- **What it does**: Connects to MCP servers to access their tools
- **Where it runs**: Your application
- **Communication**: MCP protocol
- **Best for**: Using tools from remote/separate services

```python
# MCP Client Pattern
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_mcp_tools():
    server_params = StdioServerParameters(command="uv", args=["run", "server.py"])
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("my_function", arguments={})
```

---

## 🏗️ **Three Integration Architectures**

### Architecture 1: **Hybrid Approach** (Recommended for Flexibility)
Use AISuite for local tools + MCP Client for remote tools

```
┌─────────────────────────────────────────┐
│         Your Application                │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      AISuite Client              │  │
│  │                                  │  │
│  │  Local Tools (direct)            │  │
│  │  • get_current_time()            │  │
│  │  • calculate_metrics()           │  │
│  │                                  │  │
│  │  Remote Tools (via MCP Client)   │  │
│  │  • search_papers()               │  │
│  │  • fetch_database()              │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                 │
                 │ MCP Protocol
                 ▼
        ┌──────────────────┐
        │   MCP Server     │
        │                  │
        │  @mcp.tool()     │
        │  search_papers() │
        │  extract_info()  │
        └──────────────────┘
```

**When to use**: You have some simple tools that don't need isolation, and some complex tools that benefit from being in a separate service.

---

### Architecture 2: **Pure MCP Architecture** (Best for Production)
Everything goes through MCP servers

```
┌─────────────────────────────────────────┐
│         Your Application                │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      MCP Client                  │  │
│  │                                  │  │
│  │  Connects to multiple servers    │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
            │          │           │
            │          │           │
    ┌───────┘          │           └────────┐
    │                  │                    │
    ▼                  ▼                    ▼
┌──────────┐    ┌──────────┐       ┌──────────┐
│ Research │    │   Time   │       │  File    │
│  Server  │    │  Server  │       │  Server  │
│          │    │          │       │          │
│ arxiv    │    │ datetime │       │  write   │
│ tools    │    │  tools   │       │  read    │
└──────────┘    └──────────┘       └──────────┘
```

**When to use**: Production systems, need scalability, team collaboration, want to reuse tools across different applications.

---

### Architecture 3: **AISuite with MCP Bridge** (Easiest Migration)
Convert MCP tools to AISuite-compatible functions

```
┌─────────────────────────────────────────┐
│         Your Application                │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      AISuite Client              │  │
│  │                                  │  │
│  │  tools=[                         │  │
│  │    local_tool,                   │  │
│  │    mcp_wrapper(server_tool)      │  │
│  │  ]                               │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                 │
                 │ (Behind the scenes)
                 ▼
        ┌──────────────────┐
        │   MCP Server     │
        └──────────────────┘
```

**When to use**: You want to keep using AISuite but also want to access MCP tools.

---

## 💡 **Practical Implementation Examples**

### Example 1: Hybrid Approach Implementation

```python
import aisuite as ai
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime

# Local tool (AISuite)
def get_current_time():
    """Returns the current time"""
    return datetime.now().strftime("%H:%M:%S")

# MCP tools wrapper
class MCPToolsWrapper:
    def __init__(self):
        self.session = None
        self.tools = []
    
    async def connect(self, server_command, server_args):
        """Connect to MCP server and fetch tools"""
        server_params = StdioServerParameters(
            command=server_command,
            args=server_args
        )
        
        read, write = await stdio_client(server_params).__aenter__()
        self.session = await ClientSession(read, write).__aenter__()
        await self.session.initialize()
        
        response = await self.session.list_tools()
        self.tools = response.tools
        return self.tools
    
    async def call_tool(self, name, arguments):
        """Call a tool on the MCP server"""
        if not self.session:
            raise Exception("Not connected to server")
        result = await self.session.call_tool(name, arguments)
        return result.content

# Unified agent
class UnifiedAgent:
    def __init__(self):
        self.ai_client = ai.Client()
        self.mcp_wrapper = MCPToolsWrapper()
        self.local_tools = []
        self.remote_tools = []
    
    def add_local_tool(self, func):
        """Add a local AISuite tool"""
        self.local_tools.append(func)
    
    async def add_mcp_server(self, command, args):
        """Connect to an MCP server and add its tools"""
        tools = await self.mcp_wrapper.connect(command, args)
        self.remote_tools.extend(tools)
        print(f"Connected to MCP server with tools: {[t.name for t in tools]}")
    
    async def process_query(self, query):
        """Process a user query using both local and remote tools"""
        # Combine tool definitions
        all_tools = self.local_tools.copy()
        
        # Add MCP tools to the list (converted to AISuite format)
        for tool in self.remote_tools:
            all_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        
        # Make initial request
        messages = [{"role": "user", "content": query}]
        response = self.ai_client.chat.completions.create(
            model="openai:gpt-4o",
            messages=messages,
            tools=all_tools,
            max_turns=0  # Manual control
        )
        
        # Handle tool calls manually
        while response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            
            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Check if it's a local or remote tool
                if any(t['name'] == tool_name for t in self.remote_tools if isinstance(t, dict)):
                    # Call MCP tool
                    result = await self.mcp_wrapper.call_tool(tool_name, tool_args)
                else:
                    # Call local tool
                    local_func = next(f for f in self.local_tools if f.__name__ == tool_name)
                    result = local_func(**tool_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            
            response = self.ai_client.chat.completions.create(
                model="openai:gpt-4o",
                messages=messages,
                tools=all_tools,
                max_turns=0
            )
        
        return response.choices[0].message.content

# Usage
async def main():
    agent = UnifiedAgent()
    
    # Add local tools
    agent.add_local_tool(get_current_time)
    
    # Add MCP server tools
    await agent.add_mcp_server("uv", ["run", "research_server.py"])
    
    # Process queries
    result = await agent.process_query(
        "What time is it? Also search for papers on quantum computing"
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Example 2: Pure MCP Architecture

```python
# Create multiple specialized MCP servers

# time_server.py
from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("time")

@mcp.tool()
def get_current_time() -> str:
    """Returns the current time"""
    return datetime.now().strftime("%H:%M:%S")

@mcp.tool()
def get_current_date() -> str:
    """Returns the current date"""
    return datetime.now().strftime("%Y-%m-%d")

if __name__ == "__main__":
    mcp.run(transport='stdio')

# file_server.py
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("file")

@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """Write content to a file"""
    with open(filename, 'w') as f:
        f.write(content)
    return f"File {filename} written successfully"

@mcp.tool()
def read_file(filename: str) -> str:
    """Read content from a file"""
    with open(filename, 'r') as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport='stdio')

# Multi-server client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import anthropic

class MultiServerAgent:
    def __init__(self):
        self.anthropic = anthropic.Anthropic()
        self.sessions = {}
        self.all_tools = []
    
    async def add_server(self, name, command, args):
        """Connect to a new MCP server"""
        server_params = StdioServerParameters(command=command, args=args)
        
        read, write = await stdio_client(server_params).__aenter__()
        session = await ClientSession(read, write).__aenter__()
        await session.initialize()
        
        response = await session.list_tools()
        self.sessions[name] = session
        
        for tool in response.tools:
            tool_dict = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
                "server": name
            }
            self.all_tools.append(tool_dict)
        
        print(f"Connected to {name} server with {len(response.tools)} tools")
    
    async def process_query(self, query):
        """Process query using all available tools from all servers"""
        messages = [{"role": "user", "content": query}]
        
        # Create tool list without server info (for Claude)
        claude_tools = [{
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"]
        } for t in self.all_tools]
        
        response = self.anthropic.messages.create(
            model='claude-3-7-sonnet-20250219',
            max_tokens=2048,
            messages=messages,
            tools=claude_tools
        )
        
        while response.stop_reason == "tool_use":
            # Find and execute tool calls
            tool_results = []
            
            for content in response.content:
                if content.type == "tool_use":
                    # Find which server has this tool
                    tool_info = next(t for t in self.all_tools if t["name"] == content.name)
                    server_name = tool_info["server"]
                    
                    # Call the tool on the appropriate server
                    session = self.sessions[server_name]
                    result = await session.call_tool(content.name, arguments=content.input)
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    })
            
            # Continue conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            response = self.anthropic.messages.create(
                model='claude-3-7-sonnet-20250219',
                max_tokens=2048,
                messages=messages,
                tools=claude_tools
            )
        
        return response.content[0].text

# Usage
async def main():
    agent = MultiServerAgent()
    
    # Connect to multiple servers
    await agent.add_server("research", "uv", ["run", "research_server.py"])
    await agent.add_server("time", "uv", ["run", "time_server.py"])
    await agent.add_server("file", "uv", ["run", "file_server.py"])
    
    # Now you can use tools from all servers
    result = await agent.process_query(
        "What's the current time? Search for papers on MCP, "
        "and save the results to a file called 'research.txt'"
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 **Decision Guide: Which Architecture to Choose?**

### Choose **Hybrid Approach** if:
- ✅ Starting small with a few tools
- ✅ Have some simple tools that don't need isolation
- ✅ Want to gradually adopt MCP
- ✅ Need quick prototyping

### Choose **Pure MCP Architecture** if:
- ✅ Building production systems
- ✅ Multiple developers/teams working on different tools
- ✅ Want to share tools across different applications
- ✅ Need strong separation of concerns
- ✅ Want to distribute tools as separate services

### Choose **AISuite with MCP Bridge** if:
- ✅ Already invested heavily in AISuite
- ✅ Want to keep existing code structure
- ✅ Just need to access a few MCP tools occasionally

---

## 📚 **Key Takeaways**

1. **AISuite is simpler** but less flexible - tools live in your app
2. **MCP is more powerful** but requires more setup - tools are services
3. **You can mix both** approaches in the same application
4. **Start with Hybrid**, migrate to Pure MCP as you scale
5. **MCP servers can be shared** across multiple applications
6. **One MCP client can connect** to multiple MCP servers

---

## 🔄 **Migration Path**

```
Phase 1: Start with AISuite (All Local)
    ↓
Phase 2: Move some tools to MCP servers (Hybrid)
    ↓
Phase 3: Create multiple specialized MCP servers
    ↓
Phase 4: Pure MCP architecture (All Remote)
```
