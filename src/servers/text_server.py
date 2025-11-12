
"""
Text Server - Provides text manipulation tools
"""
from mcp.server.fastmcp import FastMCP
import os
import json

mcp = FastMCP("text", description="Text manipulation and file operations")


@mcp.tool()
def count_words(text: str) -> int:
    """
    Count the number of words in text.
    
    Args:
        text: Input text
    
    Returns:
        Number of words
    """
    return len(text.split())


@mcp.tool()
def count_characters(text: str, include_spaces: bool = True) -> int:
    """
    Count the number of characters in text.
    
    Args:
        text: Input text
        include_spaces: Whether to count spaces (default: True)
    
    Returns:
        Number of characters
    """
    if include_spaces:
        return len(text)
    return len(text.replace(" ", ""))


@mcp.tool()
def to_uppercase(text: str) -> str:
    """
    Convert text to uppercase.
    
    Args:
        text: Input text
    
    Returns:
        Uppercased text
    """
    return text.upper()


@mcp.tool()
def to_lowercase(text: str) -> str:
    """
    Convert text to lowercase.
    
    Args:
        text: Input text
    
    Returns:
        Lowercased text
    """
    return text.lower()


@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    Write content to a text file.
    
    Args:
        filename: Name of the file to write
        content: Content to write
    
    Returns:
        Success message
    """
    try:
        with open(filename, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read content from a text file.
    
    Args:
        filename: Name of the file to read
    
    Returns:
        File content or error message
    """
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def reverse_text(text: str) -> str:
    """
    Reverse the text.
    
    Args:
        text: Input text
    
    Returns:
        Reversed text
    """
    return text[::-1]


if __name__ == "__main__":
    mcp.run(transport='stdio')
