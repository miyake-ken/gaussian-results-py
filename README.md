# gaussian_job_results

Parse a finished GAUSSIAN job's `.out` log into a small, opinionated, frozen
dataclass that JSON-serializes cleanly.

This package wraps [`cclib`](https://cclib.github.io) with a curated subset of
attributes (success flag, final energy, final geometry, vibrational
frequencies, thermochemistry) that downstream scripts and notebooks in this
workspace actually consume. The full `cclib.parser.data.ccData` object is
retained on `result.raw` as an escape hatch.

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
print(result.success, result.package, result.natom)
print(result.final_energy_eV, result.freeenergy_hartree)
print(len(result.vibfreqs_cm1 or ()))

# Parse the canonical log inside a compound directory.
result = parse_compound(Path("examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O"))

# Serialize to JSON. The `raw` ccData object is excluded.
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

## Parsed fields

Every numeric field is present only when the corresponding section is in the
log; absent sections become `None`. See `GaussianResult` in `result.py` for
the full list with units.

| Field | Units |
|---|---|
| `final_energy_eV` | eV (last `scfenergies`) |
| `final_geometry_angstrom` | Angstrom |
| `vibfreqs_cm1` | cm⁻¹ |
| `vibirs_km_per_mol` | km/mol |
| `zpve_hartree`, `enthalpy_hartree`, `freeenergy_hartree` | Hartree |
| `entropy_hartree_per_K` | Hartree · K⁻¹ (cclib's native unit; multiply by 6.275·10⁵ to get cal · mol⁻¹ · K⁻¹) |
| `temperature_K`, `pressure_atm` | Kelvin, atm |

## Tests

```bash
pytest packages/gaussian_job_results \
    --cov=gaussian_job_results \
    --cov-report=term-missing
```

See the design spec at
`docs/superpowers/specs/2026-04-25-gaussian-job-results-design.md`.
