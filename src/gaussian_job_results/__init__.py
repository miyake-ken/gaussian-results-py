"""gaussian_job_results: cclib-based parser for GAUSSIAN job outputs."""

from .discovery import find_log_in_compound_dir
from .parser import parse_compound, parse_log
from .result import GaussianResult, GaussianRunInfo, GaussianRunSetup
from .serializer import to_json, write_json

__all__ = [
    "GaussianResult",
    "GaussianRunInfo",
    "GaussianRunSetup",
    "find_log_in_compound_dir",
    "parse_compound",
    "parse_log",
    "to_json",
    "write_json",
]
