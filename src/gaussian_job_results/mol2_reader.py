from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Mol2Atom:
    """A single atom record from a Tripos mol2 ATOM block."""
    atom_id: int
    name:    str
    x:       float
    y:       float
    z:       float
    symbol:  str


class Mol2ParseError(ValueError):
    """Raised when a mol2 file is structurally invalid."""


def read_mol2(path: Path | str) -> tuple[Mol2Atom, ...]:
    """Read a Tripos mol2 file and return its ATOM block.

    Reads only the @<TRIPOS>ATOM section. Other sections are scanned for
    structural validity but not returned. Multi-molecule mol2 files are
    rejected.

    Raises:
      FileNotFoundError: path does not exist.
      Mol2ParseError:    structurally invalid file.
      OSError:           lower-level read errors.
    """
    p = Path(path)
    text = p.read_text()

    section: str | None = None
    molecule_count = 0
    atom_section_seen = False
    atoms: list[Mol2Atom] = []

    for lineno, raw in enumerate(text.splitlines(), start=2):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("@<TRIPOS>"):
            section = stripped[len("@<TRIPOS>"):]
            if section == "MOLECULE":
                molecule_count += 1
                if molecule_count > 1:
                    raise Mol2ParseError("multi-molecule mol2 not supported")
            elif section == "ATOM":
                atom_section_seen = True
            continue
        if section == "ATOM":
            fields = stripped.split()
            if len(fields) < 6:
                raise Mol2ParseError(
                    f"malformed atom record at line {lineno}: "
                    f"expected >=6 fields, got {len(fields)}"
                )
            try:
                atom_id   = int(fields[0])
                name      = fields[1]
                x         = float(fields[2])
                y         = float(fields[3])
                z         = float(fields[4])
                atom_type = fields[5]
            except ValueError as exc:
                raise Mol2ParseError(
                    f"malformed atom record at line {lineno}: {exc}"
                ) from exc
            symbol = atom_type.split(".", 1)[0]
            atoms.append(Mol2Atom(
                atom_id=atom_id, name=name,
                x=x, y=y, z=z, symbol=symbol,
            ))

    if not atom_section_seen:
        raise Mol2ParseError("no @<TRIPOS>ATOM section")
    if not atoms:
        raise Mol2ParseError("@<TRIPOS>ATOM section is empty")

    return tuple(atoms)
