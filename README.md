# AUDISTO-MCP
An Audisto MCP (Model Context Protocol) server for connecting AI agents to Audisto's technical SEO analysis platform.

## What is this?
AUDISTO-MCP is a bridge that lets AI agents (like Claude, via Claude Desktop) access your Audisto crawl data through a standardized interface. It exposes tools to list recent crawls and retrieve detailed crawl summaries.

**Read-only:** This MCP server is intentionally read-only — it does NOT expose any endpoints to start, stop, or modify Audisto crawls. It only retrieves and reports data from Audisto's API.

## API Usage Limits

Audisto's API enforces strict usage limits:
- **One request per API key at a time** — If a second request is sent while one is still executing, you'll receive a 429 (Too Many Requests) error. The MCP client includes automatic retries with backoff to handle this gracefully.
- **Chunk size limit** — Maximum 10,000 items per request. The client validates this automatically.
- **Important:** Only run **one MCP instance per API key** at a time. If you run Claude Desktop and Gemini CLI simultaneously with the same credentials, they may conflict and cause 429 errors.

## Quick Start

### Prerequisites
- Python 3.8 or later
- An Audisto account with API credentials

### Installation

1. **Clone this repository** (or download the files)
   ```bash
   git clone https://github.com/yourusername/AUDISTO-MCP.git
   cd AUDISTO-MCP
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up credentials**
   Create a `.env` file or set environment variables:
   ```bash
   export AUDISTO_API_KEY=your_api_key_here
   export AUDISTO_PASSWORD=your_password_here
   ```

4. **Run the server**
   ```bash
   python server.py
   ```

## Available Tools

### `get_help()`
Displays all available commands, usage examples, and workflow tips.
- Use this if you're unsure what to ask
- Example: "Help" or "What can I do with this?"

### `get_crawl_status()`
Lists the last 5 crawls from your Audisto account with:
- Crawl ID
- Domain
- Status (finished or in progress)

### `get_crawl_summary(crawl_id)`
Retrieves details about a specific crawl:
- Pages crawled
- Max depth reached
- Start time
- Domain info
- Domain info

## Usage with Claude Desktop

Configure Claude Desktop to use this MCP server by adding it to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "audisto": {
      "command": "python",
      "args": ["/path/to/AUDISTO-MCP/server.py"]
    }
  }
}
```

Then you can ask Claude questions like:
- "What crawls do I have in Audisto?"
- "Show me the summary for crawl 12345"
- "How many pages were crawled in my latest crawl?"

## Usage with Gemini CLI

Add the MCP server to Gemini CLI:

```bash
gemini mcp add audisto "python C:\path\to\AUDISTO-MCP\server.py"
```

Enable the server:

```bash
gemini mcp enable audisto
```

View all configured servers:

```bash
gemini mcp list
```

To remove the server:

```bash
gemini mcp remove audisto
```

## Asking Questions

You can now ask your AI agent questions like:
- "What crawls do I have in Audisto?"
- "Show me the summary for crawl 12345"
- "How many pages were crawled in my latest crawl?"
- "List all my Audisto crawls and their statuses"

## Security checklist

Follow these before publishing or sharing the repository:

- **Protect credentials**: Do not commit API keys or passwords. Use environment variables or a secrets manager.
- **.env handling**: If you use a `.env` file for local testing, add it to `.gitignore` and never commit it.
- **Supply-chain scan**: Run `pip-audit` or `safety` before releasing to check dependency vulnerabilities.
- **CI checks**: Add a CI job to run `pip-audit` and a linter (e.g., `flake8`) on PRs.
- **Least privilege**: Use an API key with only the necessary Audisto scopes.
- **Credential rotation**: Rotate API keys if they were accidentally exposed.
- **Limited exposure**: Prefer launching the MCP server via stdio (CLI integrations) instead of binding network sockets; if network binding is required, restrict to localhost and/or use firewall rules.
- **Logs**: Avoid logging sensitive data (API keys, full request/response bodies). Keep logs for diagnostics only.

If you'd like, I can add a small GitHub Actions workflow to run `pip-audit` automatically on PRs.

## License
MIT - see [LICENSE](LICENSE)
