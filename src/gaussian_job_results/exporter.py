"""Export a parsed Gaussian result as a Tripos mol2 file via OpenBabel."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openbabel import openbabel as ob
from openbabel import pybel

from .parser import parse_log
from .result import GaussianResult


class NotConvergedError(ValueError):
    """Raised when a Gaussian opt run did not converge and the caller did
    not pass ``allow_incomplete=True``."""


def result_to_mol2(
    result: GaussianResult,
    output_path: Path | str,
    *,
    allow_incomplete: bool = False,
    overwrite: bool = False,
) -> Path:
    raise NotImplementedError


def export_mol2(
    log_path: Path | str,
    output_path: Path | str,
    *,
    allow_incomplete: bool = False,
    overwrite: bool = False,
) -> Path:
    raise NotImplementedError
