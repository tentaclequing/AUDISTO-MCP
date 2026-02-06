# Changelog

All notable changes to AUDISTO-MCP are documented in this file.

## [1.2.0] - 2026-02-06

### 🔒 Security

- **CRITICAL: Updated `requests` dependency** from `2.31.0` to `>=2.32.0,<3.0.0` to fix CVE-2024-35195 (Proxy-Authorization header leakage)
- **Added explicit `urllib3` dependency** (`>=2.0.0,<3.0.0`) with suppressed debug logging to prevent auth header exposure
- **Python version enforcement**: Added runtime check for Python 3.8+ at server startup

### ✨ Added

- **Pydantic Model Validation**: Full implementation of Pydantic models (`CrawlStatus`, `CrawlStatusResponse`, `CrawlSummary`) for type-safe API response validation
- **Comprehensive Logging**: Added structured logging throughout `audisto_client.py` with debug, info, and warning levels
- **Centralized Error Handling**: New `handle_api_error()` helper function in `server.py` for consistent error messages
- **Code Quality Tools**:
  - `mypy` for static type checking with `mypy.ini` configuration
  - `ruff` for fast Python linting with `ruff.toml` configuration
  - Type stubs for external libraries (`types-requests`)
- **Documentation Files**:
  - `.env.example` template with correct Audisto API URLs
  - `CONTRIBUTING.md` with full contributor guide and development workflow
  - `mypy.ini` for type checking configuration
  - `ruff.toml` for linting rules
- **Comprehensive Test Coverage**: Added error path tests for:
  - 404 Not Found errors
  - 429 Rate limit errors
  - Invalid crawl IDs (negative, non-integer)
  - Invalid chunk sizes (0, >10,000)
  - Unexpected response formats
- **Configurable API Version**: API version now configurable via `AUDISTO_API_VERSION` environment variable (defaults to "2.0")

### 🔧 Changed

- **Updated all dependencies** with proper version constraints (`<3.0.0` style) to prevent breaking changes
- **Enhanced CI/CD Pipeline**: Added `ruff check` and `mypy` type checking to GitHub Actions workflow
- **Improved Error Messages**: Added specific handling for 429 rate limit errors
- **Better Status Icons**: Changed status icons in `get_crawl_status()` from text to Unicode symbols (✓ and ⋯)
- **Type Safety**: Added `Union` types and proper type hints throughout codebase
- **Magic Numbers Extraction**: Extracted `MAX_CRAWLS_DISPLAYED = 5` constant in `server.py`

### 📝 Documentation

- **Updated README.md**:
  - Fixed GitHub clone URL (tentaclequing/AUDISTO-MCP)
  - Added reference to `.env.example` in setup instructions
  - Properly formatted API credential URLs as markdown links
- **Enhanced ARCHITECTURE.md**: Documentation now reflects Pydantic model usage and logging additions

### 🐛 Fixed

- **Type checker compatibility**: Fixed type errors in `get_crawl_status()` for Pydantic model handling
- **Proper Pydantic model usage**: `audisto_client.py` now returns validated models instead of raw dicts
- **Fallback handling**: Graceful degradation to raw dicts if Pydantic validation fails

### 🧪 Testing

- **Expanded test suite** from 2 to 12 tests covering both success and error paths
- **Test organization**: Descriptive test names with docstrings explaining each test case
- **Better mocking**: Enhanced `responses` mock usage for realistic API simulation

### 🔄 Development

- **Version pinning**: All dependencies now have upper bounds to prevent unexpected breakage
- **Updated dev dependencies**:
  - `pytest>=8.0.0,<9.0.0` (was `7.4.0`)
  - `responses>=0.25.0,<1.0.0` (was `0.25.8`)
  - `pip-audit>=2.7.0,<3.0.0` (was `2.6.0`)
  - Added `mypy>=1.0.0,<2.0.0`
  - Added `ruff>=0.1.0,<1.0.0`
  - Added `python-dotenv>=1.0.0,<2.0.0`

## [1.1.1] - 2026-02-06

### Fixed
- **Pydantic dependency conflict**: Updated `pydantic==1.10.12` to `pydantic>=2.0.0` to resolve compatibility issue with `fastmcp>=0.1.0` (which requires `pydantic>=2.5.3`)
- **Installation issues**: Loosened version constraints to allow pip to use pre-built wheels instead of requiring Rust compilation

### Added
- **OS-specific installation instructions**: Detailed setup guides for Windows (PowerShell), macOS, and Linux (Bash/Zsh)
- **Claude CLI support**: Full integration instructions for using AUDISTO-MCP with Claude CLI (in addition to Claude Desktop and Gemini CLI)
- **Reorganized documentation**: New "Supported AI Clients" section in README consolidating all client setup instructions

### Documentation
- **README.md**: Added platform-specific virtual environment activation, credential loading, and server startup commands
- **README.md**: Added Claude CLI prerequisites and setup workflow for all operating systems

## [1.1.0] - 2026-02-06

### Added
- **Centralized API Client** (`audisto_client.py`): Replaces direct HTTP calls with a robust, reusable client that handles authentication, retries, and session pooling
- **Request Queueing**: Threading lock ensures Audisto's "1 request per API key at a time" limit is respected within a single MCP instance
- **Automatic Retries**: Exponential backoff (3 retries) on timeout and server errors (429, 5xx)
- **Chunk Size Validation**: Validates chunk sizes (max 10,000 items) before sending requests to prevent API errors
- **Pydantic Models** (`models.py`): Response validation and structured data handling
- **Unit Tests** (`tests/test_audisto_client.py`): Mocked tests for the client with pytest
- **CI/CD Pipeline** (`.github/workflows/ci.yml`): Automated testing and security scanning (pip-audit) on every push/PR
- **Help Tool** (`get_help()`): Displays available commands and usage examples for users
- **Development Dependencies** (`requirements-dev.txt`): pytest, responses, pip-audit for local testing
- **API Documentation** (`docs/audisto_endpoints.json`): Canonical reference of Audisto API v2.0 endpoints
- **Gemini CLI Support**: Full integration instructions for Gemini CLI (in addition to Claude Desktop)
- **Security Hardening**:
  - Startup credential validation (fails fast if credentials missing)
  - `.gitignore` entries for `.env`, virtual environments, and build artifacts
  - Credential validation via threading lock (prevents accidental logging)
  - Security checklist in README for users publishing this tool

### Changed
- **Server refactoring**: `server.py` now uses `AudistoClient` instead of direct `requests` calls
- **Error handling**: Specific exception types (Timeout, HTTPError, RequestException, ValueError) instead of bare `Exception`
- **Logging**: Structured logging with appropriate levels (info, warning, error, critical)
- **API version**: Explicitly set to v2.0 (previously v1.0)

### Fixed
- **Consistent status code handling**: Standardized `getattr(e.response, 'status_code', None)` across error handlers
- **Removed redundant logging**: Consolidated startup messages
- **Proper exit code**: Changed `exit(1)` to `sys.exit(1)` for production standards

### Documentation
- **README.md**: Added usage limits, security checklist, Gemini CLI setup, and help tool docs
- **Copilot Instructions**: Simplified for local AI agent development
- **Module docstrings**: Clear explanations of purpose, features, and constraints

## [1.0.0] - 2026-02-05

### Added
- **Initial Release**: Basic MCP server for Audisto integration
- **Three MCP Tools**:
  - `get_crawl_status()`: Lists recent crawls
  - `get_crawl_summary(crawl_id)`: Retrieves crawl details
  - `get_help()`: Displays help text
- **Basic Error Handling**: Try-catch blocks for API calls
- **CLI Integration**: Claude Desktop configuration support
- **MIT License**: Open-source, permissive licensing
