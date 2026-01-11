# Contributing to Image Organizer

Thank you for your interest in contributing to Image Organizer! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Your Python version and operating system
- Any relevant error messages or logs

### Suggesting Features

Feature suggestions are welcome! Please open an issue to discuss:
- The problem the feature would solve
- Your proposed solution
- Any alternatives you've considered

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
   - Follow existing code style
   - Add docstrings for new functions/classes
   - Add comments for complex logic
   - Update documentation if needed
4. **Test your changes**
   - Test with various image formats (JPEG, PNG, HEIC)
   - Test with different dataset sizes
   - Ensure error handling works correctly
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
   - Use clear, descriptive commit messages
6. **Push to your branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Keep functions focused and modular
- Add comments for complex algorithms

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/image-organizer.git
   cd image-organizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For HEIC support on Linux:
   ```bash
   sudo apt-get install libheif-dev
   ```

## Testing

Before submitting a pull request:
- Test with sample photos of different formats
- Test with small and large datasets
- Test edge cases (corrupted files, missing EXIF data, etc.)
- Ensure the code runs on your platform

## Areas for Contribution

- Additional image format support
- Performance optimizations
- Improved duplicate detection algorithms
- Better filename recognition patterns
- Documentation improvements
- Bug fixes

## Questions?

Feel free to open an issue with questions or reach out to discuss contributions!
