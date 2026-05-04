from pathlib import Path

import pytest

from gaussian_job_results.mol2_reader import (
    Mol2Atom,
    Mol2ParseError,
    read_mol2,
)


_METHANE_MOL2 = """\
@<TRIPOS>MOLECULE
methane
    5     4     0     0     0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
      1 C       0.0000    0.0000    0.0000 C.3
      2 H       1.0890    0.0000    0.0000 H
      3 H      -0.3630    1.0267    0.0000 H
      4 H      -0.3630   -0.5134   -0.8892 H
      5 H      -0.3630   -0.5134    0.8892 H
@<TRIPOS>BOND
     1     1     2 1
     2     1     3 1
     3     1     4 1
     4     1     5 1
"""


_SINGLE_ATOM_MOL2 = """\
@<TRIPOS>MOLECULE
just_argon
    1     0     0     0     0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
      1 Ar      0.0000    0.0000    0.0000 Ar
"""


def test_mol2_atom_is_frozen_dataclass():
    a = Mol2Atom(atom_id=1, name="C1", x=0.0, y=0.0, z=0.0, symbol="C")
    with pytest.raises((AttributeError, TypeError)):
        a.x = 1.0


def test_read_mol2_single_atom(tmp_path: Path):
    p = tmp_path / "argon.mol2"
    p.write_text(_SINGLE_ATOM_MOL2)
    atoms = read_mol2(p)
    assert len(atoms) == 1
    assert atoms[0] == Mol2Atom(
        atom_id=1, name="Ar", x=0.0, y=0.0, z=0.0, symbol="Ar"
    )


def test_read_mol2_methane_5_atoms(tmp_path: Path):
    p = tmp_path / "methane.mol2"
    p.write_text(_METHANE_MOL2)
    atoms = read_mol2(p)
    assert len(atoms) == 5
    assert atoms[0].symbol == "C"      # C.3 → "C"
    assert atoms[1].symbol == "H"      # already "H"
    assert atoms[0].atom_id == 1
    assert atoms[4].atom_id == 5
    assert atoms[0].x == 0.0
    assert abs(atoms[1].x - 1.089) < 1e-6


def test_read_mol2_atom_type_without_dot(tmp_path: Path):
    p = tmp_path / "h.mol2"
    p.write_text("""\
@<TRIPOS>MOLECULE
hyd
    1     0     0     0     0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
      1 H       0.0000    0.0000    0.0000 H
""")
    atoms = read_mol2(p)
    assert atoms[0].symbol == "H"


def test_read_mol2_returns_tuple(tmp_path: Path):
    p = tmp_path / "methane.mol2"
    p.write_text(_METHANE_MOL2)
    atoms = read_mol2(p)
    assert isinstance(atoms, tuple)


def test_read_mol2_missing_atom_section_raises(tmp_path: Path):
    p = tmp_path / "no_atom.mol2"
    p.write_text("""\
@<TRIPOS>MOLECULE
empty
    0     0     0     0     0
SMALL
NO_CHARGES
""")
    with pytest.raises(Mol2ParseError, match="no @<TRIPOS>ATOM section"):
        read_mol2(p)


def test_read_mol2_malformed_field_count_raises(tmp_path: Path):
    p = tmp_path / "short.mol2"
    p.write_text("""\
@<TRIPOS>MOLECULE
short
    1     0     0     0     0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
      1 C       0.0000    0.0000
""")
    with pytest.raises(Mol2ParseError, match="line 7"):
        read_mol2(p)


def test_read_mol2_non_numeric_xyz_raises(tmp_path: Path):
    p = tmp_path / "bad_xyz.mol2"
    p.write_text("""\
@<TRIPOS>MOLECULE
bad
    1     0     0     0     0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
      1 C       NaNzz     0.0000    0.0000 C.3
""")
    with pytest.raises(Mol2ParseError, match="line 7"):
        read_mol2(p)


def test_read_mol2_multi_molecule_raises(tmp_path: Path):
    p = tmp_path / "multi.mol2"
    p.write_text("""\
@<TRIPOS>MOLECULE
mol_a
    1     0     0     0     0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
      1 C       0.0000    0.0000    0.0000 C.3
@<TRIPOS>MOLECULE
mol_b
    1     0     0     0     0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
      1 N       1.0000    0.0000    0.0000 N.3
""")
    with pytest.raises(Mol2ParseError, match="multi-molecule"):
        read_mol2(p)


def test_read_mol2_nonexistent_path_raises_filenotfound(tmp_path: Path):
    p = tmp_path / "does_not_exist.mol2"
    with pytest.raises(FileNotFoundError):
        read_mol2(p)


def test_read_mol2_unreadable_path_raises_permissionerror(tmp_path: Path):
    import os, stat
    p = tmp_path / "locked.mol2"
    p.write_text("@<TRIPOS>MOLECULE\nx\n0 0 0 0 0\nSMALL\nNO_CHARGES\n")
    os.chmod(p, 0)
    try:
        with pytest.raises(PermissionError):
            read_mol2(p)
    finally:
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
