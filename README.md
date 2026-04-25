# gaussian_job_results

Parse a finished GAUSSIAN job's `.out` log into a small, opinionated, frozen
dataclass that JSON-serializes cleanly.

This package wraps [`cclib`](https://cclib.github.io) with two curated
namespaces — **run identity** and **calculation setup** — and keeps the full
`cclib.parser.data.ccData` object on `result.raw` as the canonical source of
computed quantities (final energy, geometry, vibrational frequencies,
thermochemistry).

The user-facing CLI lives in the sibling [`gaussian_job_cli`](../gaussian_job_cli)
package as the `gaussian-parse-results` console script (also available as
`python -m gaussian_job_cli parse-results`).

## Install

From the repository root:

```bash
pixi install
```

The package is registered as a path-dep in the workspace `pixi.toml`.

## Usage (Python API)

```python
from pathlib import Path

from gaussian_job_results import parse_log, parse_compound, to_json

# Parse a single .out file.
result = parse_log(Path("examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O/main.out"))

# Curated views.
print(result.run_info.success, result.run_info.package)
print(result.run_setup.natom, result.run_setup.basis_set)
print(result.run_setup.temperature, result.run_setup.pressure)

# Computed outputs come from the cclib ccData on `raw`.
print(result.raw.scfenergies[-1])      # final SCF energy in eV
print(result.raw.atomcoords[-1])       # optimized geometry (Å, numpy array)
print(len(result.raw.vibfreqs))        # number of vibrational modes

# Parse the canonical log inside a compound directory.
result = parse_compound(Path("examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O"))

# Serialize the curated namespaces to JSON. `raw` is excluded.
print(to_json(result))
```

## Usage (CLI)

```bash
# Single .out file.
gaussian-parse-results --input examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O/main.out --no-write

# Compound directory.
gaussian-parse-results --input examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O --no-write

# TOML-driven: writes to <PathResolver.target_dir(compound_id)>/result.json.
gaussian-parse-results --config /abs/path/to/gaussian_batch.toml
```

## Curated namespaces

### `run_info` — `GaussianRunInfo`

| Field | Source |
|---|---|
| `source_path` | The parsed log's path. |
| `package` | `metadata['package']`, e.g. `"Gaussian"`. |
| `package_version` | `metadata['package_version']`, e.g. `"2016+C.02"`. |
| `success` | `metadata['success']` (Normal vs Error termination). |
| `methods` | `metadata['methods']`. |
| `optdone` | `data.optdone`. |

### `run_setup` — `GaussianRunSetup`

Names match cclib's own attribute names so callers can move freely between
the curated view and `raw`.

| Field | Source / units |
|---|---|
| `basis_set` | `metadata['basis_set']`. |
| `natom` | `data.natom`. |
| `charge` | `data.charge`. |
| `mult` | `data.mult` (spin multiplicity). |
| `gbasis` | `data.gbasis` — per-atom basis function definitions. `None` when cclib did not emit the basis section. |
| `scannames` | `data.scannames` — relaxed-scan parameter names. `None` for non-scan jobs. |
| `temperature` | `data.temperature` (K). |
| `pressure` | `data.pressure` (atm). |

### Computed outputs (accessed via `result.raw`)

| cclib attribute | Description / units |
|---|---|
| `scfenergies` | SCF energies per step in eV. `result.raw.scfenergies[-1]` is the final energy. |
| `atomcoords` | Geometry trajectory in Å. `result.raw.atomcoords[-1]` is the optimized geometry. |
| `atomnos` | Atomic numbers (length `natom`). |
| `vibfreqs` | Vibrational frequencies in cm⁻¹. |
| `vibirs` | IR intensities in km · mol⁻¹. |
| `zpve` | Zero-point vibrational energy (Hartree). |
| `enthalpy`, `freeenergy` | Thermochemistry totals (Hartree). |
| `entropy` | Entropy in Hartree · K⁻¹ (multiply by ~6.275·10⁵ for cal · mol⁻¹ · K⁻¹). |

`raw` is excluded from `to_json` output. Consumers that need energies or
geometries in JSON should either read `result.raw.scfenergies` etc. directly
or layer their own serializer on top.

## Tests

```bash
pytest packages/gaussian_job_results \
    --cov=gaussian_job_results \
    --cov-report=term-missing
```

See the design spec at
`docs/superpowers/specs/2026-04-25-gaussian-job-results-design.md`.
