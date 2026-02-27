# Contributing to OpenCoulomb

Thank you for your interest in contributing to OpenCoulomb.

## Development Setup

```bash
git clone https://github.com/opencoulomb/opencoulomb
cd opencoulomb
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -q                    # All tests
pytest tests/unit/ -q               # Unit tests only
pytest tests/ --cov=src/opencoulomb # With coverage
ruff check src/ tests/              # Lint
```

## Code Style

- **Linting**: ruff (auto-fixable with `ruff check --fix`)
- **Type checking**: mypy strict mode
- **Line length**: 100 characters
- **Imports**: sorted by ruff (isort rules)
- **Data model**: Frozen dataclasses for all domain types
- **Type annotations**: Use `TYPE_CHECKING` blocks for type-only imports

## Commit Convention

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

Scopes: `core`, `types`, `io`, `viz`, `cli`, `docs`

## Project Structure

```
src/opencoulomb/
├── types/    # Domain data model (frozen dataclasses)
├── core/     # Pure computation (Okada, stress, CFS, pipeline)
├── io/       # .inp parser, output writers
├── viz/      # Matplotlib visualization
└── cli/      # Click CLI commands
```

## Testing Guidelines

- Unit tests in `tests/unit/`, integration in `tests/integration/`
- Use `pytest.approx()` for floating-point comparisons
- Use `hypothesis` for property-based testing of numerical code
- Coverage target: ≥90% overall

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
