"""
Pure MCP Architecture: Multi-Server Agent

This implementation shows how to build a production-ready architecture
where all tools are exposed via MCP servers and accessed through a unified client.
"""

import asyncio
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# ==================== SERVER MANAGER ====================

@dataclass
class ServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    description: str = ""


class ServerManager:
    """Manages multiple MCP server connections"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Any] = {}  # tool_name -> tool_schema
        self.tool_to_server: Dict[str, str] = {}  # tool_name -> server_name
        self.servers: Dict[str, ServerConfig] = {}
    
    async def connect_server(self, config: ServerConfig):
        """
        Connect to an MCP server.
        
        Args:
            config: ServerConfig with connection details
        """
        print(f"🔌 Connecting to {config.name} server...")
        print(f"   Command: {config.command} {' '.join(config.args)}")
        
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args
        )
        
        try:
            # Create streams
            async with stdio_client(server_params) as (read, write):
                session = ClientSession(read, write)
                await session.__aenter__()
                
                # Initialize connection
                await session.initialize()
                
                # Get available tools
                response = await session.list_tools()
                
                # Store tools
                tool_names = []
                for tool in response.tools:
                    tool_name = tool.name
                    tool_names.append(tool_name)
                    
                    self.tools[tool_name] = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    self.tool_to_server[tool_name] = config.name
                
                # Store session and config
                self.sessions[config.name] = session
                self.servers[config.name] = config
                
                print(f"✅ Connected to {config.name}")
                print(f"   Tools: {', '.join(tool_names)}")
                return tool_names
                
        except Exception as e:
            print(f"❌ Failed to connect to {config.name}: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on its respective server.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
        
        Returns:
            Tool result
        """
        if tool_name not in self.tool_to_server:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        server_name = self.tool_to_server[tool_name]
        session = self.sessions.get(server_name)
        
        if not session:
            raise RuntimeError(f"Not connected to server: {server_name}")
        
        print(f"  🔧 Calling {tool_name} on {server_name} server")
        result = await session.call_tool(tool_name, arguments=arguments)
        return result
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all servers in Claude-compatible format"""
        return list(self.tools.values())
    
    def get_server_info(self) -> Dict[str, List[str]]:
        """Get information about connected servers and their tools"""
        info = {}
        for tool_name, server_name in self.tool_to_server.items():
            if server_name not in info:
                info[server_name] = []
            info[server_name].append(tool_name)
        return info


# ==================== MULTI-SERVER AGENT ====================

class MultiServerAgent:
    """
    Agent that uses tools from multiple MCP servers.
    All tools are remote - pure MCP architecture.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.anthropic = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.server_manager = ServerManager()
        self.conversation_history = []
    
    async def add_server(self, config: ServerConfig):
        """
        Add an MCP server to the agent.
        
        Args:
            config: ServerConfig with connection details
        """
        await self.server_manager.connect_server(config)
    
    async def process_query(self, query: str, model: str = "claude-3-5-sonnet-20241022",
                          max_tokens: int = 2048) -> str:
        """
        Process a user query using tools from all connected servers.
        
        Args:
            query: User's question or request
            model: Claude model to use
            max_tokens: Maximum tokens in response
        
        Returns:
            Final response from the agent
        """
        print(f"\n💭 Processing: {query}\n")
        
        # Initialize conversation with the query
        messages = [{"role": "user", "content": query}]
        
        # Get all available tools
        tools = self.server_manager.get_all_tools()
        
        if not tools:
            print("⚠️ No tools available. Responding without tools.")
            response = self.anthropic.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages
            )
            return response.content[0].text
        
        # Initial request to Claude
        response = self.anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            tools=tools
        )
        
        # Tool use loop
        turn = 1
        while response.stop_reason == "tool_use":
            print(f"📍 Turn {turn}")
            
            # Extract assistant content
            assistant_content = []
            tool_uses = []
            
            for content in response.content:
                if content.type == "text":
                    print(f"  💬 Claude: {content.text}")
                    assistant_content.append(content)
                elif content.type == "tool_use":
                    print(f"  🔧 Tool requested: {content.name}")
                    print(f"     Arguments: {content.input}")
                    assistant_content.append(content)
                    tool_uses.append(content)
            
            # Add assistant message
            messages.append({"role": "assistant", "content": assistant_content})
            
            # Execute all tool calls
            tool_results = []
            for tool_use in tool_uses:
                try:
                    # Call the tool via MCP
                    result = await self.server_manager.call_tool(
                        tool_use.name,
                        tool_use.input
                    )
                    
                    # Extract content from result
                    if hasattr(result, 'content'):
                        if isinstance(result.content, list):
                            content_str = '\n'.join([
                                c.text if hasattr(c, 'text') else str(c) 
                                for c in result.content
                            ])
                        else:
                            content_str = str(result.content)
                    else:
                        content_str = str(result)
                    
                    print(f"  ✅ Result: {content_str[:100]}...")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": content_str
                    })
                    
                except Exception as e:
                    print(f"  ❌ Error calling {tool_use.name}: {str(e)}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Error: {str(e)}",
                        "is_error": True
                    })
            
            # Add tool results
            messages.append({"role": "user", "content": tool_results})
            
            # Get next response
            response = self.anthropic.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                tools=tools
            )
            
            turn += 1
        
        # Extract final response
        final_response = ""
        for content in response.content:
            if content.type == "text":
                final_response += content.text
        
        print(f"\n✨ Final response generated\n")
        return final_response
    
    async def chat_loop(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        Run an interactive chat loop.
        
        Args:
            model: Claude model to use
        """
        print("\n" + "="*70)
        print("🤖 Multi-Server MCP Agent Started!")
        print("="*70)
        
        # Show connected servers
        server_info = self.server_manager.get_server_info()
        for server_name, tools in server_info.items():
            print(f"🌐 {server_name}: {', '.join(tools)}")
        
        print("\nType 'quit' to exit, 'help' for commands, 'servers' to see servers")
        print("="*70 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    print("\n📚 Available Commands:")
                    print("  • quit - Exit the chat")
                    print("  • help - Show this message")
                    print("  • servers - Show connected servers and tools")
                    print("  • clear - Clear conversation history")
                    print()
                    continue
                
                if user_input.lower() == 'servers':
                    print("\n🌐 Connected Servers:")
                    server_info = self.server_manager.get_server_info()
                    for server_name, tools in server_info.items():
                        server_config = self.server_manager.servers[server_name]
                        print(f"\n  📦 {server_name}")
                        if server_config.description:
                            print(f"     {server_config.description}")
                        print(f"     Tools: {', '.join(tools)}")
                    print()
                    continue
                
                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("🗑️ Conversation history cleared\n")
                    continue
                
                if not user_input:
                    continue
                
                response = await self.process_query(user_input, model)
                print(f"\n🤖 Claude: {response}\n")
                print("-" * 70 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


# ==================== EXAMPLE SERVER CONFIGURATIONS ====================

# Example configurations - adjust paths and commands for your setup
EXAMPLE_SERVERS = [
    ServerConfig(
        name="research",
        command="uv",
        args=["run", "research_server.py"],
        description="ArXiv paper search and information extraction"
    ),
    # Add more servers as needed
    # ServerConfig(
    #     name="database",
    #     command="python",
    #     args=["database_server.py"],
    #     description="Database query and management tools"
    # ),
]


# ==================== EXAMPLE USAGE ====================

async def main():
    """Example usage of the Multi-Server Agent"""
    
    print("\n" + "="*70)
    print("🚀 Initializing Multi-Server MCP Agent")
    print("="*70 + "\n")
    
    # Initialize agent
    agent = MultiServerAgent()
    
    # Connect to servers
    # Uncomment and configure as needed
    # for server_config in EXAMPLE_SERVERS:
    #     try:
    #         await agent.add_server(server_config)
    #     except Exception as e:
    #         print(f"Could not connect to {server_config.name}: {e}")
    
    # Example: Add a single server
    # await agent.add_server(ServerConfig(
    #     name="research",
    #     command="uv",
    #     args=["run", "research_server.py"],
    #     description="Research tools"
    # ))
    
    print("\n⚠️ No servers configured. Please add server configurations above.")
    print("See EXAMPLE_SERVERS for configuration examples.\n")
    
    # Example query (uncomment when servers are configured)
    # result = await agent.process_query(
    #     "Search for papers about quantum computing"
    # )
    # print(f"Result: {result}")
    
    # Start interactive chat (uncomment when servers are configured)
    # await agent.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
