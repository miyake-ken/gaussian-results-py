"""Self-parser for Gaussian charge blocks cclib does not expose.

cclib 1.8.x maps only ``mulliken``/``apt`` (and their ``*_sum`` aggregates)
into ``ccData.atomcharges`` for our G16 fixture; the ``ESP charges:`` block
produced by ``Pop=MK`` is dropped. OpenBabel's own G16 reader does see it
and emits a ``USER_CHARGES`` mol2, so we mirror that behavior by recovering
the ESP block ourselves and merging it into ``data.atomcharges`` after
``cclib.io.ccread`` runs (see ``parser.parse_log``).

Only the ``ESP charges:`` block is parsed. Mulliken stays under cclib's
control because the ``mulliken`` key is already populated. Note: when the
log was run with ``Pop=MBS`` cclib's ``mulliken`` is the MBS variant, not
the standard Mulliken -- that is a documented cclib quirk and we do not
override it here.
"""

from __future__ import annotations

import re
from pathlib import Path

_ATOM_LINE_RE = re.compile(
    r"^\s*\d+\s+[A-Z][a-z]?\s+(-?\d+\.\d+)\s*$"
)

_HEADERS: dict[str, str] = {
    "ESP charges:": "esp",
}


def parse_partial_charges_from_log(
    path: Path | str,
) -> dict[str, tuple[float, ...]]:
    """Read ``path`` and return the recognised charge blocks (last wins).

    Raises:
        FileNotFoundError: ``path`` does not exist.
    """
    log_path = Path(path)
    if not log_path.exists():
        raise FileNotFoundError(f"log file not found: {log_path}")
    return parse_partial_charges_from_text(log_path.read_text())


def parse_partial_charges_from_text(text: str) -> dict[str, tuple[float, ...]]:
    """Extract recognised charge blocks from raw log text (last wins)."""
    lines = text.splitlines()
    result: dict[str, tuple[float, ...]] = {}
    for header_line, key in _HEADERS.items():
        block = _find_last_block(lines, header_line)
        if block is not None:
            result[key] = block
    return result


def _find_last_block(lines: list[str], header: str) -> tuple[float, ...] | None:
    last_index: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            last_index = i
    if last_index is None:
        return None

    charges: list[float] = []
    for j in range(last_index + 1, len(lines)):
        match = _ATOM_LINE_RE.match(lines[j])
        if match is not None:
            charges.append(float(match.group(1)))
        elif charges:
            break
    return tuple(charges) if charges else None
