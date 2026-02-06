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

#### 1. Clone this repository
```bash
git clone https://github.com/tentaclequing/AUDISTO-MCP.git
cd AUDISTO-MCP
```

#### 2. Create a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS (Bash/Zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set up credentials

Copy the example environment file and add your credentials:
```bash
cp .env.example .env
```

Then edit `.env` with your Audisto API credentials:
```
AUDISTO_API_KEY=your_api_key_here
AUDISTO_PASSWORD=your_password_here
```

**Get your API credentials from:**

- Web: <https://audisto.com/accounts/api>
- Documentation: <https://audisto.com/help/api/>

**Windows (PowerShell):** Load environment variables
```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

**Linux / macOS (Bash/Zsh):** Load environment variables
```bash
export $(cat .env | xargs)
```

Or simply export them manually:
```bash
export AUDISTO_API_KEY=your_api_key_here
export AUDISTO_PASSWORD=your_password_here
```

#### 5. Run the server

**Windows (PowerShell):**
```powershell
python server.py
```

**Linux / macOS (Bash/Zsh):**
```bash
python3 server.py
```

You should see:
```
INFO - Validating startup credentials...
INFO - Credentials validated successfully
INFO - MCP Server initialized
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

## Supported AI Clients

AUDISTO-MCP works with any MCP-compatible AI client. Here's how to set it up for each major platform:

### Claude Desktop
The easiest way to use Claude with MCP servers on your desktop.

1. Find your `claude_desktop_config.json`:
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. Add this MCP server to the `mcpServers` section:

   **Windows (use backslashes or forward slashes):**
   ```json
   {
     "mcpServers": {
       "audisto": {
         "command": "python",
         "args": ["C:\\Users\\YourUsername\\Documents\\GitHub\\AUDISTO-MCP\\server.py"],
         "env": {
           "AUDISTO_API_KEY": "your_api_key_here",
           "AUDISTO_PASSWORD": "your_password_here"
         }
       }
     }
   }
   ```

   **macOS / Linux:**
   ```json
   {
     "mcpServers": {
       "audisto": {
         "command": "python3",
         "args": ["/Users/YourUsername/path/to/AUDISTO-MCP/server.py"],
         "env": {
           "AUDISTO_API_KEY": "your_api_key_here",
           "AUDISTO_PASSWORD": "your_password_here"
         }
       }
     }
   }
   ```

3. Restart Claude Desktop
4. Ask Claude questions like: "What crawls do I have?" or "Show me crawl 12345"

### Claude CLI
Use Claude directly from your terminal.

#### Prerequisites
- Claude CLI installed: https://github.com/anthropics/claude-cli

#### Setup

**Windows (PowerShell):**
```powershell
# Set the path to your server
$serverPath = "C:\Users\YourUsername\Documents\GitHub\AUDISTO-MCP\server.py"

# Add MCP server
claude mcp add audisto "python $serverPath"

# Verify
claude mcp list
```

**macOS / Linux (Bash/Zsh):**
```bash
# Set the path to your server
SERVER_PATH="$HOME/path/to/AUDISTO-MCP/server.py"

# Add MCP server
claude mcp add audisto "python3 $SERVER_PATH"

# Verify
claude mcp list
```

#### Set credentials

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("AUDISTO_API_KEY", "your_api_key_here", "User")
[Environment]::SetEnvironmentVariable("AUDISTO_PASSWORD", "your_password_here", "User")
```

**macOS / Linux (Bash/Zsh):**
```bash
export AUDISTO_API_KEY="your_api_key_here"
export AUDISTO_PASSWORD="your_password_here"
```

#### Usage
```bash
claude "What crawls do I have?"
claude "Show me crawl 12345"
```

### Gemini CLI
Use Gemini directly from your terminal.

#### Prerequisites
- Gemini CLI installed: `npm install -g @google/generative-ai-cli` or follow official docs

#### Setup (all platforms)

First, make sure your virtual environment is activated and Python can find the server:

**Windows (PowerShell):**
```powershell
# Store full path to server.py
$serverPath = "C:\Users\YourUsername\Documents\GitHub\AUDISTO-MCP\server.py"

# Add MCP server
gemini mcp add audisto "python $serverPath" --scope user

# Enable it
gemini mcp enable audisto

# Verify
gemini mcp list
```

**macOS / Linux (Bash/Zsh):**
```bash
# Store full path to server.py
SERVER_PATH="$HOME/path/to/AUDISTO-MCP/server.py"

# Add MCP server
gemini mcp add audisto "python3 $SERVER_PATH" --scope user

# Enable it
gemini mcp enable audisto

# Verify
gemini mcp list
```

### Set credentials

After adding the server, set environment variables:

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("AUDISTO_API_KEY", "your_api_key_here", "User")
[Environment]::SetEnvironmentVariable("AUDISTO_PASSWORD", "your_password_here", "User")
```

**macOS / Linux (Bash/Zsh):**
```bash
# Add to ~/.bashrc, ~/.zshrc, or ~/.profile
export AUDISTO_API_KEY="your_api_key_here"
export AUDISTO_PASSWORD="your_password_here"

# Then reload
source ~/.bashrc  # or ~/.zshrc
```

### Remove the server (if needed)

**All platforms:**
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
