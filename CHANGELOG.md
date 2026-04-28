# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Documented tagged GitHub releases as the canonical (and only
  supported) install path. Neither PyPI nor the official conda-forge
  channel is used as a distribution channel for this package; the
  conda-forge staged-recipes submission was withdrawn on 2026-04-28.
  Consumers (including the upstream `miyake-ken/GAUSSIAN_repo` Pixi
  workspace) install via
  `git+https://github.com/miyake-ken/gaussian-results-py.git@v0.1.0`.

### Fixed

- Declare `polars>=1.0` as a runtime dependency. The package's
  `_json_safe` module imports polars internally; pip-only installs would
  previously fail at import time.

## [0.1.0] - 2026-04-28

### Added

- Initial release. Carried over from the `gaussian_job_results` package
  in `miyake-ken/GAUSSIAN_repo` via `git filter-repo`. Public surface:
  `GaussianResult`, `GaussianRunMetadata`, `parse_log`, `result_to_mol2`,
  `export_mol2`, `NotConvergedError`.
- Tripos `.mol2` export of the optimized Gaussian geometry via OpenBabel
  with optional ESP / Mulliken partial charges.
- `gaussian_job_results.fixtures` submodule exposing `replica_dir()` and
  `replica_log_path()` for downstream test suites.
- `[fixtures]` extras that bundles the `replica/` test fixture into the wheel
  so consumers can declare `gaussian_job_results[fixtures]` instead of
  reaching into a workspace-relative path.
