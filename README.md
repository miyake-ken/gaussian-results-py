# gaussian_job_results

Parse a finished GAUSSIAN job's `.out` log into a small, opinionated, frozen
dataclass that JSON-serializes cleanly.

This package wraps [`cclib`](https://cclib.github.io) with a single curated
namespace — `GaussianRunMetadata`, accessible via `result.run_info` — that
mirrors cclib's full `data.metadata` dict verbatim under a `metadata` field
and exposes the cclib `ccData` attributes that aren't already in `metadata`.
The full `cclib.parser.data.ccData` object stays on `result.raw` as the
canonical source of computed quantities (final energy, geometry, vibrational
frequencies, thermochemistry).

The user-facing CLI lives in the sibling
[`gaussian_job_runtime`](../gaussian_job_runtime) package and is reached
via `python -m gaussian_job_runtime parse-results`. The legacy
`gaussian-parse-results` console script (previously shipped by
`gaussian_job_cli`) was removed in the 2026-04-27 inner-programs
refactor; the rendered SLURM batch templates already invoke the new
path.

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

info = result.run_info

# Identity / termination details mirror cclib metadata verbatim.
print(info.metadata["package"], info.metadata["package_version"])
print(info.metadata["success"])
print(info.metadata["basis_set"])

# ccData-derived attributes stay as direct fields.
print(info.natom, info.charge, info.mult)
print(info.temperature, info.pressure)
print(info.optdone)

# Computed outputs come from the cclib ccData on `raw`.
print(result.raw.scfenergies[-1])      # final SCF energy in eV
print(result.raw.atomcoords[-1])       # optimized geometry (Å, numpy array)
print(len(result.raw.vibfreqs))        # number of vibrational modes

# Parse the canonical log inside a compound directory.
result = parse_compound(Path("examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O"))

# Serialize the curated namespace to JSON. `raw` is excluded.
print(to_json(result))
```

## Usage (CLI)

```bash
# Single .out file.
python -m gaussian_job_runtime parse-results \
    --input examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O/main.out --no-write

# Compound directory.
python -m gaussian_job_runtime parse-results \
    --input examples/replica/ROSDSFDQCJNGOL-UHFFFAOYSA-O --no-write

# TOML-driven: writes to <PathResolver.target_dir(compound_id)>/result.json.
python -m gaussian_job_runtime parse-results \
    --config /abs/path/to/gaussian_batch.toml
```

## `GaussianRunMetadata`

Single curated namespace, accessed as `result.run_info`.

| Field | Source |
|---|---|
| `source_path` | The parsed log's path. |
| `metadata` | cclib's full `data.metadata` dict, recursively coerced to JSON-safe primitives by `_json_safe.to_json_safe`. Includes `package`, `package_version`, `success`, `methods`, `basis_set`, `cpu_time`, `wall_time`, and any other key cclib populates (e.g. `functional`, `keywords`, `coord_type`, `comments`). `datetime.timedelta` values become ISO 8601 duration strings (`"PT…"`). |
| `optdone` | `data.optdone`. |
| `natom` | `data.natom`. |
| `charge` | `data.charge`. |
| `mult` | `data.mult` (spin multiplicity). |
| `gbasis` | `data.gbasis` — per-atom basis function definitions. `None` when cclib did not emit the basis section. |
| `scannames` | `data.scannames` — relaxed-scan parameter names. `None` for non-scan jobs. |
| `temperature` | `data.temperature` (K). |
| `pressure` | `data.pressure` (atm). |

## Computed outputs (accessed via `result.raw`)

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

See the design specs at
`docs/superpowers/specs/2026-04-25-gaussian-job-results-design.md` (original
package design) and
`docs/superpowers/specs/2026-04-25-gaussian-run-info-setup-merge-design.md`
(this single-namespace refactor).

## Exporter

`gaussian_job_results.exporter` writes a parsed result as a Tripos `.mol2`
geometry file via OpenBabel. The library exposes two entry points:

```python
from gaussian_job_results import export_mol2, parse_log, result_to_mol2

# One-shot from a path
export_mol2("/abs/path/to/main.out", "/abs/path/to/main.mol2")

# Reuse an already-parsed GaussianResult
result = parse_log("/abs/path/to/main.out")
result_to_mol2(result, "/abs/path/to/main.mol2")
```

Both write the **last recorded geometry** (`atomcoords[-1]`) with
OpenBabel-perceived bonds. Pass `allow_incomplete=True` to write
non-converged opts; `overwrite=True` to replace an existing file.

If the run did not converge and `allow_incomplete=False` (default), the
functions raise `gaussian_job_results.NotConvergedError` (a `ValueError`
subclass).

### Partial charges (`charge_source`)

Both entry points accept a `charge_source` kwarg controlling the
partial-charge column of the Tripos `<TRIPOS>ATOM` block:

| Value | Behavior | mol2 charge_type |
|---|---|---|
| `"auto"` (default) | ESP if present in the log, else Mulliken, else fall through to OpenBabel's perceived charges. | `USER_CHARGES` (when ESP/Mulliken found) or `GASTEIGER` |
| `"esp"` | Require the `ESP charges:` block from `Pop=MK`. Raises `ValueError` if missing. | `USER_CHARGES` (label: `"ESP"`) |
| `"mulliken"` | Use cclib's `atomcharges["mulliken"]`. Raises if missing. | `USER_CHARGES` (label: `"Mulliken"`) |
| `"none"` | Never inject; OpenBabel emits its default Gasteiger charges. | `GASTEIGER` |

```python
result_to_mol2(result, "/abs/path/to/main.mol2", charge_source="esp")
```

**ESP, NOT RESP.** `"esp"` is the Merz-Kollman ESP fit produced by Gaussian
(`Pop=MK`). Restrained ESP (RESP, Bayly et al.) is a separate two-stage
fit performed by AmberTools `antechamber -c resp` / `resp` on top of
Gaussian's ESP grid; it is not produced by Gaussian alone and is out of
scope for this exporter (see `docs/todos.md` for the trigger condition).

**Two cclib quirks worth noting:**

1. cclib 1.8.x silently drops the `ESP charges:` block for G16 logs; we
   recover it via the in-package self-parser
   `gaussian_job_results.partial_charges` and inject it into
   `data.atomcharges["esp"]` at parse time.
2. When the route line includes `Pop=MBS`, cclib's
   `atomcharges["mulliken"]` is the MBS-Mulliken variant (modified basis
   set), not the standard Mulliken. We do not override cclib's choice.

The total charge / multiplicity, molecule title, and orientation knob are
still deferred — see `docs/todos.md` ("Pre-implementation notes — out →
mol2 export") for the trigger conditions.
