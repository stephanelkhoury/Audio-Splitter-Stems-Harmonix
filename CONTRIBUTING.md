# Contributing to Harmonix Audio Splitter

Thank you for considering contributing to Harmonix! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and collaborative.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Python version
   - OS and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs/errors

### Suggesting Features

1. Check existing feature requests
2. Clearly describe the use case
3. Explain why it would be useful
4. Consider implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation
4. **Test your changes**
   ```bash
   pytest
   black src/
   flake8 src/
   ```
5. **Commit with clear messages**
   ```bash
   git commit -m "Add amazing feature: description"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest
```

## Code Style

- Follow PEP 8
- Use Black for formatting (line length 100)
- Use type hints where applicable
- Write docstrings for all public functions/classes

Example:
```python
def separate_audio(
    audio_path: Path,
    quality: QualityMode = QualityMode.BALANCED
) -> Dict[str, StemOutput]:
    """
    Separate audio file into stems.
    
    Args:
        audio_path: Path to input audio file
        quality: Quality mode for separation
        
    Returns:
        Dictionary mapping stem name to StemOutput
        
    Raises:
        FileNotFoundError: If audio file doesn't exist
    """
    pass
```

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use pytest fixtures for common setup
- Mark integration tests appropriately

```python
@pytest.mark.integration
def test_full_pipeline():
    # Test code
    pass
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings for all public APIs
- Update CHANGELOG.md
- Include examples where helpful

## Commit Messages

Format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat: Add per-instrument separation mode

- Implement instrument-specific models
- Add detection routing logic
- Update API endpoints

Closes #123
```

## Questions?

Open an issue or reach out to stephan@harmonix.dev
