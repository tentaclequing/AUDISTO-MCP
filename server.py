"""AUDISTO MCP SERVER
Author: Gianna Brachetti-Truskawa
License: MIT
Description: A Model Context Protocol server for connecting AI agents to Audisto technical SEO data.

Read-only: This MCP acts only as a read-only adapter to Audisto's API. It does not provide any tools to start, stop, or modify crawls.
"""

import logging
import os
import sys
from typing import Any, List, Tuple

import requests
from fastmcp import FastMCP

from audisto_client import AudistoClient
from models import CrawlStatusResponse, CrawlSummary

# Check Python version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the MCP Server
mcp = FastMCP("Audisto SEO Agent")

# Constants
MAX_CRAWLS_DISPLAYED = 5

# --- Helper Functions ---

def handle_api_error(e: Exception, context: str = "") -> str:
    """Centralized error message formatter for consistent error handling.

    Args:
        e: The exception that was raised
        context: Context string describing where the error occurred

    Returns:
        User-friendly error message string
    """
    if isinstance(e, requests.exceptions.Timeout):
        logger.error(f"{context} - Timeout: {str(e)}")
        return "Error: Request timeout. Audisto API is not responding."
    elif isinstance(e, requests.exceptions.HTTPError):
        status = getattr(e.response, 'status_code', None)
        logger.error(f"{context} - HTTP {status}: {str(e)}")
        if status == 404:
            return "Error: Resource not found."
        elif status == 429:
            return "Error: Rate limit exceeded. Please wait and try again."
        return f"Error: Audisto API returned status {status}"
    elif isinstance(e, requests.exceptions.RequestException):
        logger.error(f"{context} - Request error: {str(e)}")
        return "Error: Failed to connect to Audisto API"
    elif isinstance(e, ValueError):
        logger.error(f"{context} - Validation error: {str(e)}")
        return "Error: Missing or invalid credentials"
    else:
        logger.exception(f"{context} - Unexpected error: {str(e)}")
        return "Error: An unexpected error occurred"
def get_auth() -> Tuple[str, str]:
    """Retrieves credentials safely from environment variables.

    Returns:
        Tuple[str, str]: (api_key, password) for Basic Auth

    Raises:
        ValueError: If AUDISTO_API_KEY or AUDISTO_PASSWORD are not set
    """
    api_key = os.getenv("AUDISTO_API_KEY")
    password = os.getenv("AUDISTO_PASSWORD")  # Audisto uses this as the 'password' in Basic Auth

    if not api_key or not password:
        logger.error("Missing required environment variables: AUDISTO_API_KEY and/or AUDISTO_PASSWORD")
        raise ValueError("Missing Credentials! Please set AUDISTO_API_KEY and AUDISTO_PASSWORD in your environment.")

    return (api_key, password)


def get_client() -> AudistoClient:
    """Construct an AudistoClient using current environment credentials."""
    api_key, password = get_auth()
    return AudistoClient(api_key=api_key, password=password)

# --- The Tools ---

@mcp.tool()
def get_help() -> str:
    """
    Display available commands and usage examples for the Audisto MCP server.
    Use this if you're unsure what queries you can send.
    """
    help_text = """
Available Audisto MCP Commands:

1. get_crawl_status()
   - Lists the 5 most recent Audisto crawls
   - Shows: Crawl ID, domain, status (finished or in progress)
   - Example: "Show me my recent crawls"
   - Example: "What crawls do I have?"

2. get_crawl_summary(crawl_id)
   - Retrieves details for a specific crawl
   - Shows: pages crawled, max depth, start time, domain
   - Parameter: crawl_id (numeric ID from get_crawl_status)
   - Example: "Get me the summary for crawl 12345"
   - Example: "How many pages were crawled in crawl 67890?"

Example Usage Flow:
  1. Ask: "Show me my recent Audisto crawls"
  2. System responds with crawl list and IDs
  3. Ask: "Get the summary for crawl [ID]"
  4. System responds with detailed crawl info

Tips:
- Use get_crawl_status() first to find crawl IDs
- Then use get_crawl_summary() with a specific crawl ID
- All data comes from Audisto API v2.0
"""
    return help_text.strip()

@mcp.tool()
def get_crawl_status() -> str:
    """
    Check the status of recent Audisto crawls.
    Returns the ID, status, and domain of the last 5 crawls.
    """
    try:
        client = get_client()
        response = client.get_crawl_status_v2()

        # Handle both Pydantic model and raw dict responses
        crawls: List[Any] = []
        if isinstance(response, CrawlStatusResponse):
            # CrawlStatusResponse Pydantic model
            crawls = response.items[:MAX_CRAWLS_DISPLAYED]
        else:
            # Raw dict with 'items' key
            items = response.get('items', [])
            crawls = items[:MAX_CRAWLS_DISPLAYED] if isinstance(items, list) else []

        if not crawls:
            logger.info("No recent crawls found in Audisto")
            return "No recent crawls found."

        summary = [f"Here are the latest {MAX_CRAWLS_DISPLAYED} Audisto crawls:"]
        for crawl in crawls:
            # Handle both Pydantic models and dicts
            if hasattr(crawl, 'id'):
                # Pydantic model
                crawl_id = crawl.id
                domain = crawl.domain
                status = crawl.status
            else:
                # Dict
                crawl_id = crawl.get('id') if isinstance(crawl, dict) else None
                domain = crawl.get('domain') if isinstance(crawl, dict) else None
                status = crawl.get('status') if isinstance(crawl, dict) else None

            status_icon = "✓" if status == 'finished' else "⋯"
            summary.append(f"[{status_icon}] ID: {crawl_id} | Domain: {domain} | Status: {status}")

        logger.info("Successfully retrieved crawls from Audisto API")
        return "\n".join(summary)

    except Exception as e:
        return handle_api_error(e, "get_crawl_status")


@mcp.tool()
def get_crawl_summary(crawl_id: int) -> str:
    """
    Get the high-level summary of a specific crawl.
    Use this to see how many pages were crawled vs. ignored.
    Args:
        crawl_id: The numeric ID of the crawl (found via get_crawl_status)
    """
    try:
        client = get_client()
        data = client.get_crawl_summary_v2(crawl_id)

        # Data is always a CrawlSummary Pydantic model
        summary = (f"Crawl Summary for ID {crawl_id}:\n"
                   f"- Domain: {data.domain or 'N/A'}\n"
                   f"- Pages Crawled: {data.crawled_pages or 'N/A'}\n"
                   f"- Max Depth Reached: {data.max_depth or 'N/A'}\n"
                   f"- Start Time: {data.start_time or 'N/A'}")

        logger.info(f"Successfully retrieved summary for crawl {crawl_id}")
        return summary

    except Exception as e:
        # Special handling for 404 errors
        if isinstance(e, requests.exceptions.HTTPError):
            status = getattr(e.response, 'status_code', None)
            if status == 404:
                logger.warning(f"Crawl ID {crawl_id} not found")
                return f"Error: Crawl ID {crawl_id} not found."
        return handle_api_error(e, f"get_crawl_summary(crawl_id={crawl_id})")


def validate_startup_credentials() -> bool:
    """Validate credentials are available at startup.

    Returns:
        bool: True if credentials are valid, False otherwise
    """
    try:
        get_auth()
        logger.info("Credentials validated successfully at startup")
        return True
    except ValueError as e:
        logger.critical(f"Startup validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting AUDISTO MCP Server...")
    if not validate_startup_credentials():
        logger.critical("Cannot start server without valid credentials")
        sys.exit(1)
    mcp.run()
