"""Tests for gaussian_job_results.partial_charges (self-parser for charge
blocks cclib does not expose for our G16 logs)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gaussian_job_results.partial_charges import (
    parse_partial_charges_from_log,
    parse_partial_charges_from_text,
)


def test_parse_esp_from_real_log_picks_last_block(replica_log_path: Path) -> None:
    """The fixture has three `ESP charges:` blocks; we must take the last."""
    charges = parse_partial_charges_from_log(replica_log_path)
    assert "esp" in charges
    esp = charges["esp"]
    assert len(esp) == 11
    assert esp[0] == pytest.approx(-0.099950, abs=1e-6)
    assert esp[-1] == pytest.approx(0.310012, abs=1e-6)


def test_parse_text_returns_empty_when_no_blocks() -> None:
    text = "no charges here\nat all\n"
    assert parse_partial_charges_from_text(text) == {}


def test_parse_text_picks_last_esp_block_when_multiple() -> None:
    text = (
        " ESP charges:\n"
        "               1\n"
        "     1  N    1.000000\n"
        "     2  C   -1.000000\n"
        " Sum of ESP charges =   0.00000\n"
        " ESP charges:\n"
        "               1\n"
        "     1  N   -0.500000\n"
        "     2  C    0.500000\n"
        " Sum of ESP charges =   0.00000\n"
    )
    charges = parse_partial_charges_from_text(text)
    assert charges == {"esp": (-0.5, 0.5)}


def test_parse_text_ignores_with_hydrogens_summed_variant() -> None:
    """`ESP charges with hydrogens summed into heavy atoms:` is a different
    aggregate block (heavy-atom-only) and must not be confused with the
    per-atom `ESP charges:` block.
    """
    text = (
        " ESP charges:\n"
        "               1\n"
        "     1  N   -0.100000\n"
        "     2  C    0.100000\n"
        " Sum of ESP charges =   0.00000\n"
        " ESP charges with hydrogens summed into heavy atoms:\n"
        "               1\n"
        "     1  N    0.000000\n"
    )
    charges = parse_partial_charges_from_text(text)
    assert charges == {"esp": (-0.1, 0.1)}


def test_parse_log_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_partial_charges_from_log(tmp_path / "nope.out")


def test_parse_text_handles_two_letter_element_symbols() -> None:
    text = (
        " ESP charges:\n"
        "               1\n"
        "     1  Cl  -0.250000\n"
        "     2  Na   0.250000\n"
        " Sum of ESP charges =   0.00000\n"
    )
    charges = parse_partial_charges_from_text(text)
    assert charges == {"esp": (-0.25, 0.25)}
