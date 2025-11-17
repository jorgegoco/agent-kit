
"""
Time Server - Provides time and date related tools
"""
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
from typing import Optional

mcp = FastMCP("time")


@mcp.tool()
def get_current_time() -> str:
    """
    Get the current time in HH:MM:SS format.
    
    Returns:
        Current time as string
    """
    return datetime.now().strftime("%H:%M:%S")


@mcp.tool()
def get_current_date() -> str:
    """
    Get the current date in YYYY-MM-DD format.
    
    Returns:
        Current date as string
    """
    return datetime.now().strftime("%Y-%m-%d")


@mcp.tool()
def get_datetime() -> str:
    """
    Get the current date and time.
    
    Returns:
        Current datetime as string
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def add_days(date: str, days: int) -> str:
    """
    Add a number of days to a given date.
    
    Args:
        date: Date in YYYY-MM-DD format
        days: Number of days to add (can be negative)
    
    Returns:
        New date as string
    """
    dt = datetime.strptime(date, "%Y-%m-%d")
    new_dt = dt + timedelta(days=days)
    return new_dt.strftime("%Y-%m-%d")


@mcp.tool()
def days_between(start_date: str, end_date: str) -> int:
    """
    Calculate the number of days between two dates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Number of days between the dates
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = end - start
    return delta.days


if __name__ == "__main__":
    mcp.run(transport='stdio')
