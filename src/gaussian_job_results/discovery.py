"""Locate the canonical GAUSSIAN log inside a compound directory."""

from __future__ import annotations

from pathlib import Path

_DEFAULT_PREFERRED = ("main.out",)


def find_log_in_compound_dir(
    compound_dir: Path,
    *,
    log_glob: str = "*.out",
    preferred_basenames: tuple[str, ...] = _DEFAULT_PREFERRED,
) -> Path:
    """Return the canonical ``.out`` log under ``compound_dir``.

    Resolution order:

    1. The first preferred basename that exists (e.g. ``main.out``).
    2. The single match of ``log_glob`` if exactly one is present.

    Raises:
        FileNotFoundError: if ``compound_dir`` does not exist or is not a
            directory.
        ValueError: if zero matches, or more than one ``log_glob`` match
            without any preferred basename present.
    """
    compound_dir = Path(compound_dir)
    if not compound_dir.exists():
        raise FileNotFoundError(f"compound dir not found: {compound_dir}")
    if not compound_dir.is_dir():
        raise FileNotFoundError(f"not a directory: {compound_dir}")

    for basename in preferred_basenames:
        candidate = compound_dir / basename
        if candidate.is_file():
            return candidate

    matches = sorted(
        p for p in compound_dir.glob(log_glob) if p.is_file()
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(
            f"no log matching {log_glob!r} or {list(preferred_basenames)} "
            f"under {compound_dir}"
        )
    raise ValueError(
        f"ambiguous log discovery under {compound_dir}: {len(matches)} "
        f"matches for {log_glob!r} and no preferred basename present "
        f"(found {[m.name for m in matches]})"
    )
