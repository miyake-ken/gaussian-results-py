"""pytest fixtures for gaussian_job_results tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def replica_compound_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "replica" / "ROSDSFDQCJNGOL-UHFFFAOYSA-O"


@pytest.fixture(scope="session")
def replica_log_path(replica_compound_dir: Path) -> Path:
    return replica_compound_dir / "main.out"


@pytest.fixture(scope="session")
def replica_gjf_path(replica_compound_dir: Path) -> Path:
    return replica_compound_dir / "main.gjf"
