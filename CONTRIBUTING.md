# Contributing to Vortex

Thank you for your interest in contributing to Vortex! We welcome contributions from the community to help make this lightweight, MySQL client-compatible database even better. This document outlines the process and guidelines for contributing.

## How to Contribute

### Reporting Issues
- Check the [issue tracker](https://github.com/vhyran/vortex/issues) to see if your issue already exists.
- If not, open a new issue with:
  - A clear title and description
  - Steps to reproduce (if applicable)
  - Expected and actual behavior
  - Environment details (Python version, OS, etc.)

### Suggesting Features
- Use the [issue tracker](https://github.com/vhyran/vortex/issues) to propose new features.
- Provide a detailed explanation of the feature and its use case.
- Tag the issue with `enhancement`.

### Submitting Code
1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/vortex.git
   cd vortex
   ```

2. **Set Up Development Environment**
   ```bash
   pip install -e .[dev]
   ```

3. **Create a Branch**
   - Use a descriptive branch name (e.g., `feature/add-index-support`, `fix/bug-in-query-parser`)
   ```bash
   git checkout -b your-branch-name
   ```

4. **Make Changes**
   - Follow the coding guidelines below.
   - Keep changes focused on a single purpose.

5. **Test Your Changes**
   ```bash
   pytest
   ```
   - Add new tests if introducing new functionality.

6. **Commit Changes**
   - Use clear, concise commit messages.
   - Example: `Add support for CREATE INDEX statements`
   ```bash
   git add .
   git commit -m "Your commit message"
   ```

7. **Push and Create a Pull Request**
   ```bash
   git push origin your-branch-name
   ```
   - Go to the [repository](https://github.com/vhyran/vortex) and create a pull request.
   - Link any related issues in the PR description.

8. **Review Process**
   - Respond to feedback from maintainers.
   - Make requested changes if needed.

## Coding Guidelines

- **Python Version**: Target Python 3.8+ compatibility.
- **Style**: Follow PEP 8, enforced via `black` and `flake8`.
  - Run `black .` and `flake8` before committing.
- **Type Hints**: Use type annotations where possible (checked with `mypy`).
- **Documentation**: 
  - Add docstrings for public classes, methods, and functions.
  - Update `README.md` if your change affects usage.
- **Tests**: 
  - Add unit tests in `tests/` for new features or bug fixes.
  - Aim for good test coverage (checked with `pytest-cov`).
- **Dependencies**: 
  - Keep external dependencies minimal.
  - Discuss new dependencies with maintainers first.

## Development Setup

- **Clone the repo**: `git clone https://github.com/vhyran/vortex.git`
- **Install dev dependencies**: `pip install -e .[dev]`
- **Run tests**: `pytest`
- **Check formatting**: `black --check .`
- **Check linting**: `flake8`
- **Check types**: `mypy .`

## Code of Conduct

- Be respectful and inclusive in all interactions.
- Focus on constructive feedback and collaboration.
- Avoid personal attacks or offensive language.

## Areas for Contribution

- Bug fixes for SQL parsing or execution
- Performance optimizations
- Additional MySQL-compatible features (e.g., specific query types)
- Improved error handling and documentation
- CLI enhancements
- Test coverage expansion

## Questions?

Feel free to:
- Open an issue with your question
- Email [yasouo@proton.me](mailto:yasouo@proton.me)
- Reach out via GitHub Discussions (if enabled)

---

We appreciate your contributions to making Vortex a robust, lightweight database solution! Happy coding!
