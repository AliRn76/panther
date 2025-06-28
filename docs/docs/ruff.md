# Auto-Reformatting with Ruff

Panther supports automatic code reformatting using [Ruff](https://docs.astral.sh/ruff/), a fast Python linter and formatter written in Rust.

## Quick Setup

To enable automatic code reformatting, set `AUTO_REFORMAT` to `True` in your configuration:

```python
AUTO_REFORMAT = True  # Default is False
```

## How It Works

When `AUTO_REFORMAT` is enabled, Panther will automatically reformat your code:

- **On every application run** - Code is reformatted when you start your application.
- **With `--reload` flag** - Code is reformatted on every file change during development

This ensures your codebase maintains consistent formatting standards automatically.

## Installation

The auto-reformatting feature requires the Ruff package. Install it using pip:

```bash
pip install ruff
```

## Configuration

You can create a custom `ruff.toml` file in your project root to configure formatting rules:

```toml title="ruff.toml" linenums="1"
# Set the maximum line length
line-length = 120

# Set the indentation style
indent-width = 4

# Enable/disable specific rules
select = ["E", "F", "I"]
ignore = ["E501"]

[format]
# Formatting options
quote-style = "single"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

## Benefits

- **Consistent Code Style**: Automatic formatting ensures all code follows the same style
- **Time Saving**: No need to manually format code or run formatters separately
- **Team Collaboration**: Everyone on the team gets consistent formatting automatically
- **Fast Performance**: Ruff is extremely fast, making the formatting process seamless

## References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Formatter Configuration](https://docs.astral.sh/ruff/formatter/)
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/)
