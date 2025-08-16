# Testing Documentation

This document describes the comprehensive testing setup for TcpSocketMCP.

## 🎯 Test Coverage Goals

- **Target Coverage**: 80% minimum (currently achieving **85%**)
- **Test Count**: 80+ comprehensive tests
- **Quality Gates**: Automated quality validation
- **CI Integration**: Full CI/CD pipeline integration

## 🧪 Test Suite Overview

### Unit Tests (80 tests)

#### TCPConnection Tests (31 tests)
Located in `tests/unit/test_connection.py`

- **Connection Lifecycle**: Connect, disconnect, error handling
- **Buffer Operations**: Read, write, clear, chunked data
- **Trigger System**: Pattern matching, auto-responses
- **Error Scenarios**: Network failures, invalid operations
- **Integration Workflows**: Complete connection lifecycles

#### TCPSocketServer Tests (33 tests)
Located in `tests/unit/test_server.py`

- **MCP Tool Handlers**: All 11 TCP socket tools
- **Encoding Support**: UTF-8, hex, base64 encoding/decoding
- **Error Handling**: Connection failures, invalid inputs
- **Pre-registration**: Trigger setup before connection
- **Integration Workflows**: Complex server operations

#### Coverage Enhancement Tests (14 tests)
Located in `tests/unit/test_server_coverage.py`

- **Error Paths**: Edge cases and failure scenarios
- **Connection Management**: Duplicate IDs, not found errors
- **Tool Validation**: Input validation and error responses

#### Entry Point Tests (2 tests)
Located in `tests/unit/test_main.py`

- **Module Import**: Package structure validation
- **CLI Entry Point**: Main execution path testing

### Integration Test Framework
Located in `tests/integration/`

- **TCP Server Helpers**: Real TCP server simulation
- **Test Fixtures**: Reusable test components in `conftest.py`
- **End-to-End Scenarios**: Complete workflow testing

## 🚀 Running Tests

### Local Development

```bash
# Run all tests with coverage
uv run pytest tests/ --cov=src/TcpSocketMCP --cov-report=term-missing

# Run specific test categories
uv run pytest tests/unit/test_connection.py -v
uv run pytest tests/unit/test_server.py -v

# Run with coverage enforcement
uv run pytest tests/ --cov=src/TcpSocketMCP --cov-fail-under=80

# Generate HTML coverage report
uv run pytest tests/ --cov=src/TcpSocketMCP --cov-report=html:htmlcov
```

### Using pytest.ini Configuration

The project includes `pytest.ini` with optimized settings:

```ini
[tool:pytest]
testpaths = tests
addopts = 
    --verbose
    --tb=short
    --cov=src/TcpSocketMCP
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
    --asyncio-mode=auto
```

Simply run: `uv run pytest`

## 🔄 CI/CD Integration

### Automated Testing Pipeline

The CI pipeline (`/.github/workflows/ci.yml`) includes:

1. **Lint & Type Check**
   - Ruff code formatting and linting
   - MyPy type checking
   - Enforced code quality standards

2. **Comprehensive Testing**
   - Matrix testing across Python 3.10, 3.11, 3.12
   - Cross-platform testing (Ubuntu, Windows, macOS)
   - 80-test suite execution with coverage enforcement
   - Test result artifacts and reporting

3. **Quality Gates**
   - 80% coverage minimum enforcement
   - Security vulnerability scanning
   - Code complexity analysis
   - Maintainability scoring

4. **Package Testing**
   - Build validation
   - Installation testing
   - CLI functionality verification

### Quality Gates Workflow

The quality gates (`/.github/workflows/quality-gates.yml`) validate:

- **Test Coverage**: ≥80% required
- **Code Complexity**: <6.0 average complexity
- **Maintainability**: >8.0 maintainability index
- **Security**: Zero high-severity issues
- **Dependencies**: No known vulnerabilities

### Test Status Monitoring

- **Automated Badge Updates**: Test and coverage status badges
- **PR Comments**: Quality reports on pull requests
- **Daily Quality Checks**: Scheduled quality validation
- **Codecov Integration**: Coverage tracking and reporting

## 📊 Coverage Details

### Current Coverage by Module

| Module | Coverage | Lines | Missing |
|--------|----------|-------|---------|
| `__init__.py` | 100% | 1 | 0 |
| `connection.py` | 94% | 114 | 7 |
| `server.py` | 81% | 259 | 48 |
| `__main__.py` | 67% | 3 | 1 |
| **Total** | **85%** | **377** | **56** |

### Key Testing Areas

✅ **Fully Covered**:
- All MCP tool handlers
- Connection lifecycle management
- Buffer operations and data handling
- Trigger system functionality
- Error handling and validation
- Encoding/decoding (UTF-8, hex, base64)

📈 **High Coverage (80%+)**:
- TCP connection management
- Server tool routing
- Pre-registration workflows
- Integration scenarios

## 🛠️ Testing Tools & Dependencies

### Core Testing Stack
- **pytest**: Test framework with async support
- **pytest-asyncio**: Async testing capabilities
- **pytest-cov**: Coverage measurement and reporting
- **unittest.mock**: Mocking and test isolation

### Quality Assurance Tools
- **ruff**: Code formatting and linting
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **safety**: Dependency vulnerability checking
- **radon**: Code complexity and maintainability analysis

### CI/CD Tools
- **GitHub Actions**: Automated testing pipeline
- **Codecov**: Coverage tracking and reporting
- **pre-commit**: Local quality checks

## 🔧 Local Development Setup

### Install Testing Dependencies

```bash
# Install all dependencies including test tools
uv pip install -e .
uv pip install pytest pytest-asyncio pytest-cov

# Install quality tools
uv pip install ruff mypy bandit safety radon

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### IDE Integration

#### VS Code
Recommended extensions:
- Python Test Explorer
- Coverage Gutters
- Python Docstring Generator

#### PyCharm
- Built-in pytest integration
- Coverage display in editor
- Test debugging capabilities

## 📈 Test Performance

### Benchmarks
- **Test Execution Time**: ~0.2 seconds (80 tests)
- **Coverage Analysis**: ~0.1 seconds additional
- **Memory Usage**: <50MB peak during testing
- **Parallel Execution**: Supports pytest-xdist for faster runs

### Performance Optimization
- **AsyncMock Usage**: Proper async test isolation
- **Fixture Reuse**: Shared setup via conftest.py
- **Selective Testing**: Test markers for targeted runs
- **Caching**: uv caching for faster dependency resolution

## 🎯 Quality Metrics

### Code Quality Standards
- **Test Coverage**: ≥80% (achieving 85%)
- **Code Complexity**: <6.0 average cyclomatic complexity
- **Maintainability Index**: >8.0
- **Security Issues**: Zero high-severity vulnerabilities
- **Type Coverage**: 100% type annotation coverage

### Testing Best Practices
- **Test Isolation**: Each test is independent
- **Descriptive Names**: Clear test purpose from name
- **AAA Pattern**: Arrange, Act, Assert structure
- **Mock Usage**: Proper isolation of external dependencies
- **Error Testing**: Comprehensive error scenario coverage

## 🚨 Troubleshooting

### Common Issues

#### Tests Failing Locally
```bash
# Check Python version compatibility
python --version

# Verify dependencies
uv pip list

# Run specific failing test
uv run pytest tests/unit/test_connection.py::test_name -v
```

#### Coverage Below Threshold
```bash
# Generate detailed coverage report
uv run pytest --cov=src/TcpSocketMCP --cov-report=html:htmlcov

# Open htmlcov/index.html to see line-by-line coverage
```

#### AsyncMock Issues
- Ensure proper await handling in tests
- Use `AsyncMock()` for async methods
- Use `Mock()` for synchronous methods

### Getting Help

1. **Check CI Logs**: Detailed error information in GitHub Actions
2. **Coverage Reports**: HTML reports show exact missing lines
3. **Test Output**: Verbose mode provides detailed failure information
4. **Documentation**: This file and inline code documentation

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Guide](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

*This testing setup ensures TcpSocketMCP maintains high quality and reliability through comprehensive automated testing and quality gates.*