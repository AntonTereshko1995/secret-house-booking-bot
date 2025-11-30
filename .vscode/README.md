# VS Code Configuration

This directory contains VS Code configuration for the Secret House Booking Bot project.

## Files

### [settings.json](settings.json)
Project-specific settings for Python and testing:
- **Python Analysis**: Extra paths for imports (db, alembic)
- **Pytest Configuration**: Enabled with auto-discovery
- **Test Arguments**: Verbose mode with short traceback

### [launch.json](launch.json)
Debug configurations for running and testing:

#### Application Configurations:
- **🐍 Debug Mode** - Run bot in debug mode (`ENV=debug`)
- **🚀 Production Mode** - Run bot in production mode (`ENV=production`)

#### Test Configurations:
- **🧪 Run All Tests** - Execute all tests with verbose output
- **🧪 Run Unit Tests** - Run only unit tests (marked with `@pytest.mark.unit`)
- **🧪 Run Tests with Coverage** - Generate coverage report
- **🧪 Debug Current Test File** - Debug the currently open test file

### [tasks.json](tasks.json)
Quick tasks for testing:

Access via: `Cmd+Shift+P` → "Tasks: Run Task"

Available tasks:
- **Run All Tests** - Default test task (`Cmd+Shift+B`)
- **Run Unit Tests** - Fast unit tests only
- **Run Integration Tests** - Integration tests only
- **Run Tests with Coverage** - Generate HTML coverage report
- **Run Fast Tests** - Quick unit tests (exclude slow)
- **Open Coverage Report** - Open coverage HTML in browser
- **Clean Test Artifacts** - Remove test cache and coverage files

## Quick Start

### Running Tests

#### Method 1: Using the Testing Panel
1. Open Testing panel: `Cmd+Shift+T` (or click beaker icon)
2. Tests will auto-discover
3. Click play button to run individual tests or all tests
4. See results inline with green/red indicators

#### Method 2: Using Debug Panel
1. Open Debug panel: `Cmd+Shift+D`
2. Select a test configuration from dropdown
3. Press `F5` to run
4. View output in integrated terminal

#### Method 3: Using Tasks
1. Press `Cmd+Shift+P`
2. Type "Tasks: Run Task"
3. Select desired test task
4. View output in new terminal

#### Method 4: Keyboard Shortcuts
- `Cmd+Shift+B` - Run default test task (all tests)

### Debugging Tests

1. Open test file (e.g., `tests/test_string_helper.py`)
2. Set breakpoints by clicking left of line numbers
3. Open Debug panel (`Cmd+Shift+D`)
4. Select "🧪 Debug Current Test File"
5. Press `F5` to start debugging
6. Use debug controls to step through code

### Viewing Coverage

After running tests with coverage:

```bash
# Using task
Cmd+Shift+P → "Tasks: Run Task" → "Run Tests with Coverage"

# Then open report
Cmd+Shift+P → "Tasks: Run Task" → "Open Coverage Report"
```

Or manually:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Test Discovery

Tests are automatically discovered when you:
- Open VS Code
- Save a test file
- Refresh the Testing panel

### Discovery Rules:
- Test files: `tests/test_*.py`
- Test classes: `class Test*`
- Test functions: `def test_*`

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Shift+T` | Open Testing panel |
| `Cmd+Shift+D` | Open Debug panel |
| `Cmd+Shift+B` | Run default test task |
| `F5` | Start debugging |
| `Shift+F5` | Stop debugging |
| `F10` | Step over |
| `F11` | Step into |
| `Shift+F11` | Step out |

## Tips

### Run Specific Test
1. Open Testing panel
2. Navigate to specific test
3. Click play icon next to test name

### Run Tests in File
1. Open test file
2. Click "Run Tests" in file header
3. Or use "Debug Current Test File" configuration

### Auto-Run on Save
Tests auto-discover on save. To auto-run:
1. Install extension: "Test Explorer UI"
2. Enable auto-run in extension settings

### Filter Tests by Marker
Use pytest markers in test arguments:
```json
"python.testing.pytestArgs": [
    "tests",
    "-m",
    "unit",  // Only unit tests
    "-v"
]
```

## Troubleshooting

### Tests Not Discovered
1. Check Python interpreter is correct
2. Ensure pytest is installed: `pip install pytest`
3. Refresh: Click refresh icon in Testing panel
4. Check Output panel → Python Test Log

### Import Errors in Tests
1. Check `python.analysis.extraPaths` in settings.json
2. Ensure test files use correct sys.path manipulation
3. Verify working directory is project root

### Debug Not Working
1. Ensure `debugpy` is installed: `pip install debugpy`
2. Check launch.json configuration
3. Verify Python interpreter path

### Coverage Not Generated
1. Install pytest-cov: `pip install pytest-cov`
2. Run with coverage configuration
3. Check for .coverage file in project root

## Extensions Recommended

For best testing experience, install:
- **Python** (ms-python.python) - Required
- **Pylance** (ms-python.vscode-pylance) - Enhanced IntelliSense
- **Test Explorer UI** (hbenl.vscode-test-explorer) - Enhanced test UI
- **Coverage Gutters** (ryanluker.vscode-coverage-gutters) - Inline coverage

## Resources

- [VS Code Python Testing](https://code.visualstudio.com/docs/python/testing)
- [Pytest Documentation](https://docs.pytest.org/)
- [Project Testing README](../tests/README.md)
