
"""
Math Server - Provides mathematical calculation tools
"""
from mcp.server.fastmcp import FastMCP
import math
from typing import List

mcp = FastMCP("math")


@mcp.tool()
def calculate(expression: str) -> float:
    """
    Evaluate a mathematical expression safely.
    
    Args:
        expression: Mathematical expression (e.g., "2 + 2 * 3")
    
    Returns:
        Result of the calculation
    """
    # Only allow safe mathematical operations
    allowed_names = {
        'abs': abs, 'round': round,
        'min': min, 'max': max,
        'sum': sum, 'pow': pow,
        'sqrt': math.sqrt, 'pi': math.pi,
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    }
    
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return float(result)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def add(a: float, b: float) -> float:
    """
    Add two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Product of a and b
    """
    return a * b


@mcp.tool()
def average(numbers: List[float]) -> float:
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers
    
    Returns:
        Average value
    """
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


@mcp.tool()
def factorial(n: int) -> int:
    """
    Calculate the factorial of a number.
    
    Args:
        n: Non-negative integer
    
    Returns:
        Factorial of n
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    return math.factorial(n)


if __name__ == "__main__":
    mcp.run(transport='stdio')
