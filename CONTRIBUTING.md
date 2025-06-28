# Contributing to Panther

Thank you for your interest in contributing to Panther! This document provides guidelines and instructions for setting up the development environment and contributing to the project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Getting Help](#getting-help)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** (Panther requires Python 3.10 or higher)
- **Git** for version control
- **Docker**  for running test dependencies
- **pip** for package management

## Development Setup

Follow these steps to set up your development environment:

### 1. Clone the Repository

```bash
git clone https://github.com/AliRn76/panther.git
cd panther
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt

# Install Panther in development mode
pip install -e .
```

## Running Tests

### Prerequisites

Before running tests, you need to start the required services using Docker:

```bash
# Start MongoDB (required for database tests)
docker run --rm -p 27017:27017 -d --name mongo mongo

# Start Redis (required for caching tests)
docker run --rm -p 6379:6379 -d --name redis redis
```

**Note:** Make sure Docker is running on your system before executing these commands.

### Running Tests

```bash
# Run all tests
python tests

# Run specific test file
python -m pytest tests/test_specific_file.py

# Run tests with specific markers
python tests --mongodb      # Run only MongoDB tests
python tests --not_mongodb  # Don't run MongoDB tests
python tests --slow         # Run only slow tests
python tests --not_slow     # Don't run slow tests
```

### Test Coverage

```bash
# Run tests with coverage
coverage run tests

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in your browser to view the report
```

## Development Workflow

### Making Changes

1. **Create a new branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```

2. **Make your changes** in the source code located in the `panther/` directory.

3. **Test your changes**:
   ```bash
   # Run tests to ensure nothing is broken
   python tests
   
   # Run linting
   ruff check .
   ```

4. **Reinstall Panther** after making changes to see them immediately:
   ```bash
   pip install -e .
   ```

### Code Style

Panther uses [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting. The configuration is in `ruff.toml`.

```bash
# Format code
ruff format .

# Check for linting issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Testing Your Changes

You can test your changes in real-time by:

1. **Modifying the installed package** (for quick testing):
   - Edit files in `.venv/lib/python3.11/site-packages/panther/`
   - Changes are immediately available for testing
   - **Important:** Remember to copy your changes back to the source files before committing

2. **Using development installation**:
   - Make changes in the `panther/` directory
   - Reinstall: `pip install -e .`
   - Test your changes

## Submitting Changes

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   python tests
   ```

2. **Check code style**:
   ```bash
   ruff check .
   ruff format .
   ```

3. **Update documentation** if your changes affect public APIs or behavior.

### Creating a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub with:
   - Clear description of the changes
   - Reference to any related issues
   - Screenshots or examples if applicable

3. **Wait for review** and address any feedback from maintainers.

## Getting Help

- **Documentation**: [PantherPy.GitHub.io](https://pantherpy.github.io)
- **Issues**: [GitHub Issues](https://github.com/AliRn76/panther/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AliRn76/panther/discussions)

## Additional Resources

- **Project Structure**: Explore the `panther/` directory to understand the codebase
- **Examples**: Check the `example/` directory for usage examples
- **Benchmarks**: Review `benchmark.txt` for performance data

---

Thank you for contributing to Panther! 🐾
