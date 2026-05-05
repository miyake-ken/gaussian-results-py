"""gaussian_job_results: cclib-based parser for GAUSSIAN job outputs."""

from .discovery import find_log_in_compound_dir
from .exporter import NotConvergedError, export_mol2, result_to_mol2
from .mol2_reader import Mol2Atom, Mol2ParseError, read_mol2
from .parser import parse_compound, parse_log
from .result import GaussianResult, GaussianRunMetadata
from .serializer import to_json, write_json

__all__ = [
    "GaussianResult",
    "GaussianRunMetadata",
    "Mol2Atom",
    "Mol2ParseError",
    "NotConvergedError",
    "export_mol2",
    "find_log_in_compound_dir",
    "parse_compound",
    "parse_log",
    "read_mol2",
    "result_to_mol2",
    "to_json",
    "write_json",
]
