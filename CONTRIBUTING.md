# Contributing to AUDISTO-MCP

Thank you for your interest in contributing to AUDISTO-MCP! This guide will help you get started.

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/AUDISTO-MCP.git
cd AUDISTO-MCP
```

### 2. Create Virtual Environment

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

### 3. Install Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Configure Credentials

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Audisto API credentials
# Get credentials from: https://audisto.com/accounts/api
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_audisto_client.py

# Run specific test
pytest tests/test_audisto_client.py::test_get_crawl_summary_v2_success
```

### Code Quality Checks

```bash
# Run linter
ruff check .

# Run type checker
mypy server.py audisto_client.py models.py --strict --allow-untyped-calls

# Run security audit
pip-audit --progress=off
```

### Running All Checks (like CI)

```bash
# Run the full CI pipeline locally
ruff check . && \
mypy server.py audisto_client.py models.py --strict --allow-untyped-calls && \
pip-audit --progress=off && \
pytest -v
```

## Code Style Guidelines

### Python Style
- Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable names

### Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstring format
- Update README.md when adding new features
- Update CHANGELOG.md for all user-facing changes

### Testing
- Write tests for all new features
- Include both success and error path tests
- Use descriptive test names: `test_<function>_<scenario>`
- Mock external API calls using `responses` library

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, well-documented code
- Add or update tests
- Ensure all tests pass
- Run code quality checks

### 3. Commit Your Changes

```bash
git add .
git commit -m "Add feature: brief description"
```

Use clear, descriptive commit messages:
- `Add feature: <description>` for new features
- `Fix: <description>` for bug fixes
- `Update: <description>` for improvements
- `Docs: <description>` for documentation changes

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Screenshots (if UI changes)
- Test results

## Adding New Features

### Adding a New MCP Tool

1. **Add client method in `audisto_client.py`:**
   ```python
   def get_my_data(self, param: int) -> MyModel:
       """Fetch my data from Audisto API."""
       url = self._url("/my/endpoint")
       logger.debug(f"Fetching my data from {url}")
       with self._lock:
           resp = self.session.get(url, auth=self.auth, timeout=self.timeout)
       resp.raise_for_status()
       data = resp.json()
       logger.info("Successfully fetched my data")
       return MyModel(**data)
   ```

2. **Add Pydantic model in `models.py`:**
   ```python
   class MyModel(BaseModel):
       """My data model."""
       field1: Optional[str] = None
       field2: Optional[int] = None
   ```

3. **Add MCP tool in `server.py`:**
   ```python
   @mcp.tool()
   def my_tool(param: int) -> str:
       """User-facing description of what this tool does."""
       try:
           client = get_client()
           data = client.get_my_data(param)
           return f"Result: {data.field1}"
       except Exception as e:
           return handle_api_error(e, "my_tool")
   ```

4. **Add tests in `tests/test_audisto_client.py`:**
   ```python
   def test_get_my_data_success():
       """Test successful data retrieval."""
       client = AudistoClient(api_key="k", password="p")
       # ... add test implementation
   ```

5. **Update documentation:**
   - Update `README.md` with tool usage
   - Update `CHANGELOG.md` with version and changes
   - Update `docs/ARCHITECTURE.md` if needed

## Pull Request Guidelines

### Before Submitting
- [ ] All tests pass (`pytest -v`)
- [ ] Code passes linting (`ruff check .`)
- [ ] Type checking passes (`mypy ...`)
- [ ] Security audit passes (`pip-audit`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Reporting Issues

### Bug Reports
Include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative approaches considered

## Questions?

- Check [ARCHITECTURE.md](docs/ARCHITECTURE.md) for design details
- Open an issue for questions
- Tag with `question` label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
