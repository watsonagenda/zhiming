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
4. Ensure scripts are shellcheck-clean: `shellcheck scripts/*.sh`
5. Test on your local environment
6. Commit with a descriptive message
7. Push and open a PR

### Adding a New Scan Dimension

To add a new scan category:

1. Add detection logic to `scripts/scan-environment.sh` (in the Python block)
2. Add the corresponding output section to `scripts/update-tools.sh`
3. Update `references/detection-matrix.md` with detection methods
4. Update `SKILL.md` with the new dimension documentation
5. Add template placeholders to `assets/TOOLS-TEMPLATE.md`

### Adding a New Search Tool

1. Add the tool to the `search_tools` list in `scripts/scan-environment.sh`
2. Add the API key hint to `key_hints` in `scripts/update-tools.sh`
3. Update the priority table in `SKILL.md`
4. Add detection info to `references/detection-matrix.md`

## Code Style

- **Shell scripts**: Follow [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html). Use `set -euo pipefail`.
- **Python**: PEP 8. Keep inline Python in shell scripts minimal — extract to standalone `.py` files when logic exceeds ~50 lines.
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

# Run scan
bash scripts/scan-environment.sh > /tmp/scan-output.json

# Verify JSON is valid
python3 -c "import json; json.load(open('/tmp/scan-output.json')); print('OK')"

# Generate TOOLS.md
bash scripts/scan-environment.sh | bash scripts/update-tools.sh

# Verify TOOLS.md was created
head -20 ~/.openclaw/workspace/TOOLS.md
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
