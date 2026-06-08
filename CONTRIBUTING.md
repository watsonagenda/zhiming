# Contributing to ZhiMing (知明)

Thank you for your interest in contributing! ZhiMing is a community-driven project aimed at solving AI agent session amnesia through environment self-awareness.

## Ways to Contribute

### Bug Reports

If you find a bug, please open an issue with:

- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, shell, Python version)

### Feature Requests

Have an idea for a new scan dimension or capability? Open an issue with the `enhancement` label and describe:

- What the feature would do
- Why it's useful
- How you imagine it working

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test on your local environment: `python3 zhiming.py --demo`
5. Commit with a descriptive message
6. Push and open a PR

### Adding a New Scan Dimension

To add a new scan category:

1. Add a `scan_<dimension>()` function to `zhiming.py`
2. Add the call to `scan_all()`
3. Add the corresponding render section in `render_tools_md()`
4. Update `references/detection-matrix.md` with detection methods
5. Update `SKILL.md` with the new dimension documentation

### Adding a New Search Tool

1. Add the tool to `SEARCH_TOOLS_DEF` and `KEY_HINTS` in `zhiming.py`
2. Update the priority table in `SKILL.md`
3. Add detection info to `references/detection-matrix.md`

## Code Style

- **Python**: PEP 8. Each scan dimension is an independent function. Keep functions focused and testable.
- **Markdown**: Use reference-style links where possible. Keep lines under 120 characters.

## Security Guidelines

- **Never** log or output API key values
- **Never** read `.env` files or credential files
- **Never** scan `.ssh`, `.aws`, `.kube`, or similar sensitive directories
- When adding environment variable checks, use the `skip_prefixes` pattern to exclude sensitive prefixes
- All paths in output should use `~` for home directory

## Testing

Before submitting a PR, test on a real environment:

```bash
# Clean test
rm -f ~/.openclaw/workspace/TOOLS.md

# Verify JSON output is valid
python3 zhiming.py --json | python3 -c "import sys,json; json.load(sys.stdin); print('OK')"

# Full scan + TOOLS.md write
python3 zhiming.py

# Verify TOOLS.md was created
head -20 ~/.openclaw/workspace/TOOLS.md

# Demo mode
python3 zhiming.py --demo
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
