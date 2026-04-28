"""Public path helpers for the bundled replica fixture.

Consumer test suites (e.g. ``gaussian_job_cli``, ``gaussian_job_runtime``)
import these helpers instead of walking workspace-relative paths.
"""

from importlib.resources import files
from pathlib import Path


def replica_dir() -> Path:
    """Return the on-disk path of the bundled ``replica/`` fixture tree."""
    return Path(str(files("gaussian_job_results") / "_fixtures" / "replica"))


def replica_log_path() -> Path:
    """Return the path of ``main.out`` inside the bundled replica fixture.

    The replica fixture contains a single sub-directory keyed by InChIKey.
    Walk into it once to reach the actual ``main.out`` log.
    """
    base = replica_dir()
    candidates = [d for d in base.iterdir() if d.is_dir()]
    if len(candidates) != 1:
        raise RuntimeError(
            f"replica fixture layout changed: expected exactly one sub-dir, found {candidates}"
        )
    return candidates[0] / "main.out"
