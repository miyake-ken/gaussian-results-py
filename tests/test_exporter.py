"""Tests for gaussian_job_results.exporter."""

from __future__ import annotations


def test_exporter_module_exposes_public_symbols():
    from gaussian_job_results.exporter import (
        NotConvergedError,
        export_mol2,
        result_to_mol2,
    )

    assert issubclass(NotConvergedError, ValueError)
    assert callable(result_to_mol2)
    assert callable(export_mol2)
