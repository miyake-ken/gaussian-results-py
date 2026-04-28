# Repository Guidelines

## Project Structure & Module Organization
- Source lives under `src/gaussian_job_results`; keep data parsing, export helpers, and fixtures there.
- Tests under `tests/` mirror package behavior; regression fixtures are bundled at `tests/fixtures/replica` for hatch builds.
- Root docs (`README.md`, `CHANGELOG.md`, `LICENSE`) track user guidance and release history aligned with the exported API.

## Build, Test, and Development Commands
- `python -m hatch build` – produces wheel/sdist artifacts that include the parser and fixture bundle; run before tagging releases.
- `pytest tests --cov=gaussian_job_results --cov-report=term-missing` – verifies parser/exporter functionality and reports coverage for the package namespace.
- `ruff check src tests` – enforces the formatting and typing rules configured in `pyproject.toml` (`target-version=py312`, `line-length=100`).

## Coding Style & Naming Conventions
- Follow Python 3.12 idioms: 4-space indentation, explicit typing, and descriptive names; avoid single-letter identifiers except in very short comprehensions.
- Keep public API identifiers snake_case to match downstream expectations; document dataclasses (e.g., `GaussianRunMetadata`, `GaussianResult`) clearly.
- Use Ruff to catch formatting, unused imports, and typing issues before committing.

## Testing Guidelines
- Keep fixtures inside `tests/fixtures/replica`; reuse them for new tests targeting parsing or exporter helpers.
- Name test files `test_*` and pick descriptive functions such as `test_parse_compound_dir_returns_run_info`.
- Rerun the coverage command after modifications to parsing/exporter logic.

## Commit & Pull Request Guidelines
- Commit messages follow the `scope: subject` pattern (`docs: clarify install path`, `fix: require polars>=1.0`); keep the scope concise and subject imperative.
- Pull requests should summarize what changed, link related issues if available, and state how reviewers can verify the work (commands, fixtures, regressions).

## Security & Configuration Tips
- OpenBabel is a runtime dependency installed separately (e.g., `conda install -c conda-forge openbabel`); ensure it exists before running exporter helpers.
- Pin Python to 3.12 and cclib to ≥1.8 to match expected parser behavior.
