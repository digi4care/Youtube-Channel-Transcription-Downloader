# Contributing Guide

We welcome contributions! This guide covers development setup and contribution guidelines.

## Development Setup

This project uses pre-commit hooks to maintain code quality and consistency. These hooks automatically check your code for style issues, formatting, and potential bugs before each commit.

### Why Use Pre-commit Hooks?

Pre-commit hooks help you:

- Catch errors before they're committed
- Maintain consistent code style across the project
- Automatically format your code
- Prevent common issues like trailing whitespace or large files
- Ensure type safety with static type checking

### Prerequisites

- Python 3.11+
- `uv` package manager (recommended)
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/digi4care/Youtube-Channel-Transcription-Downloader.git
   cd Youtube-Channel-Transcription-Downloader
   ```

2. **Install pre-commit using uv**

   ```bash
   uv pip install pre-commit
   ```

3. **Install the git hooks**

   ```bash
   uv run pre-commit install
   ```

   This sets up the hooks to run automatically on every `git commit`.

4. **Run the hooks manually** (optional)

   ```bash
   uv run pre-commit run --all-files
   ```

   This will run all checks on your entire codebase.

### What Each Hook Does

- **Black**: Automatically formats your Python code to be consistent
- **isort**: Sorts your Python imports in a standard way
- **Ruff**: A fast linter that catches common errors and style issues
- **mypy**: Static type checker that helps catch type-related bugs
- **File validators**: Check YAML, JSON, and TOML files for syntax errors
- **Basic checks**: Ensure consistent line endings, no trailing whitespace, etc.

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Run pre-commit hooks: `uv run pre-commit run --all-files`

### 3. Test Your Changes

```bash
# Test with various scenarios
uv run python Youtube_Transcribe.py --help
uv run python Youtube_Transcribe.py --create-config
uv run python Youtube_Transcribe.py https://youtube.com/watch?v=test -t en
```

### 4. Update Documentation

- Update CHANGELOG.md for new features
- Update relevant documentation files
- Ensure all new features are documented

### 5. Commit Changes

```bash
git add .
uv run pre-commit run  # Run hooks before committing
git commit -m "feat: Add your feature description"
```

### 6. Create Pull Request

```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## Code Style Guidelines

### Python Code

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write descriptive docstrings
- Keep functions focused on single responsibilities
- Use meaningful variable and function names

### Documentation

- Write clear, concise documentation
- Use consistent formatting in markdown files
- Include code examples where helpful
- Keep language professional and inclusive

### Git Commits

- Use conventional commit format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Keep commit messages concise but descriptive

## Testing

### Manual Testing

Test your changes with:

- Different YouTube URL formats
- Various language options
- Configuration file variations
- Error conditions and edge cases

### Code Quality

- All pre-commit hooks must pass
- No linting errors
- Type checking passes
- Documentation builds successfully

## Reporting Issues

When reporting bugs or requesting features:

1. **Check existing issues** first
2. **Use issue templates** when available
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)
   - Configuration used
4. **Include error messages** and stack traces
5. **Suggest solutions** if you have ideas

## Feature Requests

We love hearing new ideas! When requesting features:

1. **Describe the problem** you're trying to solve
2. **Explain why** it's important
3. **Consider alternatives** you've thought about
4. **Be open to discussion** about implementation details

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing!** 🎉

---

**← Back to [README.md](../README.md)**
