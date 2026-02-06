"""AUDISTO MCP SERVER
Author: Gianna Brachetti-Truskawa
License: MIT
Description: A Model Context Protocol server for connecting AI agents to Audisto technical SEO data.

Read-only: This MCP acts only as a read-only adapter to Audisto's API. It does not provide any tools to start, stop, or modify crawls.
"""

from fastmcp import FastMCP
import requests
import os
import sys
import logging
from typing import Tuple
from audisto_client import AudistoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the MCP Server
mcp = FastMCP("Audisto SEO Agent")

# --- Helper Functions ---
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
        data = client.get_crawl_status_v2()

        # Format the output for the AI to read easily
        if not data:
            logger.info("No recent crawls found in Audisto")
            return "No recent crawls found."

        summary = ["Here are the latest 5 Audisto crawls:"]
        for crawl in (data[:5] if isinstance(data, list) else data.get('items', [])[:5]):
            status_icon = "OK" if crawl.get('status') == 'finished' else "IN_PROGRESS"
            summary.append(f"[{status_icon}] ID: {crawl.get('id')} | Domain: {crawl.get('domain')} | Status: {crawl.get('status')}")

        logger.info("Successfully retrieved crawls from Audisto API")
        return "\n".join(summary)

    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to Audisto API: {str(e)}")
        return "Error: Request timeout. Audisto API is not responding."
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        logger.error(f"HTTP error from Audisto API: {status} - {str(e)}")
        return f"Error: Audisto API returned status {status}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error connecting to Audisto API: {str(e)}")
        return f"Error: Failed to connect to Audisto API"
    except ValueError as e:
        logger.error(f"Authentication error: {str(e)}")
        return "Error: Missing or invalid credentials"
    except Exception as e:
        logger.exception(f"Unexpected error in get_crawl_status: {str(e)}")
        return "Error: An unexpected error occurred"


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

        if not isinstance(data, dict):
            logger.error(f"Expected dict response for crawl {crawl_id}, got {type(data)}")
            return "Error: Invalid crawl data format"

        summary = (f"Crawl Summary for ID {crawl_id}:\n"
                   f"- Domain: {data.get('domain', 'N/A')}\n"
                   f"- Pages Crawled: {data.get('crawled_pages', 'N/A')}\n"
                   f"- Max Depth Reached: {data.get('max_depth', 'N/A')}\n"
                   f"- Start Time: {data.get('start_time', 'N/A')}")
        logger.info(f"Successfully retrieved summary for crawl {crawl_id}")
        return summary

    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        if status == 404:
            logger.warning(f"Crawl ID {crawl_id} not found")
            return f"Error: Crawl ID {crawl_id} not found."
        logger.error(f"HTTP error from Audisto API for crawl {crawl_id}: {status}")
        return f"Error: Audisto API returned status {status}"
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout retrieving crawl {crawl_id}: {str(e)}")
        return "Error: Request timeout. Audisto API is not responding."
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error retrieving crawl {crawl_id}: {str(e)}")
        return f"Error: Failed to connect to Audisto API"
    except ValueError as e:
        logger.error(f"Authentication error: {str(e)}")
        return "Error: Missing or invalid credentials"
    except Exception as e:
        logger.exception(f"Unexpected error in get_crawl_summary for crawl {crawl_id}: {str(e)}")
        return "Error: An unexpected error occurred"


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