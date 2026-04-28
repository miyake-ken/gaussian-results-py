"""pytest fixtures for gaussian_job_results tests."""

from __future__ import annotations

from pathlib import Path

import pytest

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def replica_compound_dir() -> Path:
    return _FIXTURES_DIR / "replica" / "ROSDSFDQCJNGOL-UHFFFAOYSA-O"


@pytest.fixture(scope="session")
def replica_log_path(replica_compound_dir: Path) -> Path:
    return replica_compound_dir / "main.out"


@pytest.fixture(scope="session")
def replica_gjf_path(replica_compound_dir: Path) -> Path:
    return replica_compound_dir / "main.gjf"


@pytest.fixture(scope="session")
def replica_result(replica_log_path: Path):
    """Cached ``parse_log(replica_log_path)`` shared across tests.

    Treat as read-only -- session scope means mutating state leaks across
    tests. For tests that need a fresh parse (e.g. isolation tests like
    ``test_metadata_is_a_fresh_dict``), call ``parse_log`` directly.

    Why: under coverage instrumentation cclib's per-line ``extract`` loop
    triggers ~10 s of tracer overhead per ``parse_log`` call (~2.3 k calls
    of ``cclib.parser.gaussianparser.extract`` get traced). Parsing the
    fixture once at session scope drops the cumulative cost from minutes
    to seconds.
    """
    from gaussian_job_results import parse_log

    return parse_log(replica_log_path)
