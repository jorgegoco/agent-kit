"""
Hybrid Agent: Combining AISuite Local Tools with MCP Server Tools

This implementation shows how to use both local tools (executed directly)
and remote tools (accessed via MCP servers) in the same agent.
"""

import aisuite as ai
import asyncio
import json
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, List, Any, Optional

# ==================== LOCAL TOOLS (AISuite) ====================

def get_current_time() -> str:
    """
    Returns the current time as a string.
    This is a local tool that executes immediately.
    """
    return datetime.now().strftime("%H:%M:%S")


def calculate_sum(a: float, b: float) -> float:
    """
    Calculate the sum of two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The sum of a and b
    """
    return a + b


def create_greeting(name: str, formal: bool = False) -> str:
    """
    Create a personalized greeting.
    
    Args:
        name: Person's name
        formal: Whether to use formal greeting (default: False)
    
    Returns:
        A greeting message
    """
    if formal:
        return f"Good day, {name}. How may I assist you?"
    return f"Hey {name}! What's up?"


# ==================== MCP TOOLS CONNECTOR ====================

class MCPConnector:
    """Manages connections to MCP servers and tool execution"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}  # tool_name -> tool_info
        self.tool_to_server: Dict[str, str] = {}  # tool_name -> server_name
    
    async def add_server(self, server_name: str, command: str, args: List[str]) -> List[str]:
        """
        Connect to an MCP server and fetch its tools.
        
        Args:
            server_name: Name to identify this server
            command: Command to run the server (e.g., "uv")
            args: Arguments for the command (e.g., ["run", "server.py"])
        
        Returns:
            List of tool names from this server
        """
        print(f"🔌 Connecting to {server_name} server...")
        
        server_params = StdioServerParameters(command=command, args=args)
        
        # Create streams for communication
        async with stdio_client(server_params) as (read, write):
            session = ClientSession(read, write)
            await session.__aenter__()
            await session.initialize()
            
            # Get available tools from the server
            response = await session.list_tools()
            tool_names = []
            
            for tool in response.tools:
                tool_name = tool.name
                tool_names.append(tool_name)
                
                # Store tool information
                self.tools[tool_name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                self.tool_to_server[tool_name] = server_name
            
            # Store the session
            self.sessions[server_name] = session
            
            print(f"✅ Connected to {server_name} with tools: {tool_names}")
            return tool_names
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on its respective MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool
        
        Returns:
            Tool execution result as string
        """
        if tool_name not in self.tool_to_server:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        server_name = self.tool_to_server[tool_name]
        session = self.sessions[server_name]
        
        print(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")
        result = await session.call_tool(tool_name, arguments=arguments)
        
        # Extract content from the result
        if hasattr(result, 'content'):
            if isinstance(result.content, list):
                return str([c.text if hasattr(c, 'text') else str(c) for c in result.content])
            return str(result.content)
        return str(result)
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas in AISuite format"""
        return list(self.tools.values())


# ==================== HYBRID AGENT ====================

class HybridAgent:
    """
    Agent that combines local AISuite tools with remote MCP tools.
    """
    
    def __init__(self):
        self.ai_client = ai.Client()
        self.mcp = MCPConnector()
        self.local_tools = []
        self.local_tool_map = {}
    
    def add_local_tool(self, func):
        """
        Add a local tool (Python function).
        
        Args:
            func: Python function with proper docstring
        """
        self.local_tools.append(func)
        self.local_tool_map[func.__name__] = func
        print(f"✅ Added local tool: {func.__name__}")
    
    async def add_mcp_server(self, server_name: str, command: str, args: List[str]):
        """
        Connect to an MCP server.
        
        Args:
            server_name: Name to identify the server
            command: Command to run (e.g., "uv", "python")
            args: Command arguments (e.g., ["run", "server.py"])
        """
        await self.mcp.add_server(server_name, command, args)
    
    async def process_query(self, query: str, model: str = "openai:gpt-4o-mini", 
                          max_turns: int = 5) -> str:
        """
        Process a user query using both local and remote tools.
        
        Args:
            query: User's question or request
            model: LLM model to use
            max_turns: Maximum number of tool-calling turns
        
        Returns:
            Final response from the agent
        """
        print(f"\n💭 Processing query: {query}\n")
        
        # Combine all tools
        all_tools = self.local_tools.copy()
        mcp_tool_schemas = self.mcp.get_tool_schemas()
        all_tools.extend(mcp_tool_schemas)
        
        messages = [{"role": "user", "content": query}]
        
        for turn in range(max_turns):
            print(f"📍 Turn {turn + 1}/{max_turns}")
            
            # Get response from LLM
            response = self.ai_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=all_tools,
                max_turns=0  # We handle turns manually
            )
            
            message = response.choices[0].message
            
            # If no tool calls, we're done
            if not hasattr(message, 'tool_calls') or not message.tool_calls:
                print("✨ Final response generated\n")
                return message.content
            
            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            })
            
            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"  🔧 Tool call: {tool_name}({tool_args})")
                
                # Determine if local or remote tool
                if tool_name in self.local_tool_map:
                    # Execute local tool
                    result = self.local_tool_map[tool_name](**tool_args)
                    print(f"  ✅ Local tool result: {result}")
                else:
                    # Execute MCP tool
                    result = await self.mcp.call_tool(tool_name, tool_args)
                    print(f"  ✅ MCP tool result: {result}")
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
        
        print("⚠️ Reached maximum turns")
        return "I've reached the maximum number of tool calls. Please try again."
    
    async def chat_loop(self, model: str = "openai:gpt-4o-mini"):
        """
        Run an interactive chat loop.
        
        Args:
            model: LLM model to use
        """
        print("\n" + "="*60)
        print("🤖 Hybrid Agent Started!")
        print("="*60)
        print(f"📊 Local tools: {list(self.local_tool_map.keys())}")
        print(f"🌐 MCP tools: {list(self.mcp.tools.keys())}")
        print("\nType 'quit' to exit, 'help' for commands")
        print("="*60 + "\n")
        
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
                    print("  • tools - List all available tools")
                    print()
                    continue
                
                if user_input.lower() == 'tools':
                    print(f"\n🔧 Local tools: {list(self.local_tool_map.keys())}")
                    print(f"🌐 MCP tools: {list(self.mcp.tools.keys())}\n")
                    continue
                
                if not user_input:
                    continue
                
                response = await self.process_query(user_input, model)
                print(f"\n🤖 Agent: {response}\n")
                print("-" * 60 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


# ==================== EXAMPLE USAGE ====================

async def main():
    """Example usage of the Hybrid Agent"""
    
    # Initialize the agent
    agent = HybridAgent()
    
    # Add local tools
    agent.add_local_tool(get_current_time)
    agent.add_local_tool(calculate_sum)
    agent.add_local_tool(create_greeting)
    
    # Add MCP servers
    # Example: If you have a research server
    # await agent.add_mcp_server("research", "uv", ["run", "research_server.py"])
    
    # Example queries
    print("\n" + "="*60)
    print("🧪 Testing Hybrid Agent")
    print("="*60 + "\n")
    
    # Test local tool
    result = await agent.process_query("What time is it?")
    print(f"Result: {result}\n")
    
    # Test multiple tools
    result = await agent.process_query(
        "Calculate the sum of 42 and 58, then create a greeting for Alice"
    )
    print(f"Result: {result}\n")
    
    # Start interactive chat (uncomment to use)
    # await agent.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
