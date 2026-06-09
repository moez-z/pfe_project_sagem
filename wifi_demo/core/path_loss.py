"""
Parses the path_loss.csv file and provides a lookup method.

Expected CSV format (no header row):
    freq_mhz, loss_ant1, loss_ant2, loss_ant3, loss_ant4

Example:
    2512,21.4,21.5,21.5,21.6,
    2537,21.5,21.6,21.5,21.6,
    5500,3.1,3.2,3.1,3.3,

Usage:
    table = PathLossTable.load("path_loss.csv")
    loss  = table.get_loss(freq_mhz=2512, antenna="ANT3")   # → 21.5
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional
import shutil
from datetime import datetime


# Mapping from antenna string to column index (0-based, after the freq column)
_ANT_INDEX = {
    "ANT1": 0,
    "ANT2": 1,
    "ANT3": 2,
    "ANT4": 3,
}


class PathLossTable:
    """
    In-memory lookup table for cable / path-loss values.

    Each entry maps a frequency (MHz) → list of per-antenna losses [ANT1..ANT4].
    """

    def __init__(self) -> None:
        # { freq_mhz (int): [loss_ant1, loss_ant2, loss_ant3, loss_ant4] }
        self._table: dict[int, list[Optional[float]]] = {}
        self.source_path: str = ""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, filepath: str | Path) -> "PathLossTable":
        """
        Parse a path-loss CSV file and return a populated PathLossTable.

        Silently skips blank lines and lines whose first column is not
        a valid integer frequency.

        Parameters
        ----------
        filepath : str | Path
            Path to the CSV file.

        Returns
        -------
        PathLossTable
        """
        table = cls()
        table.source_path = str(filepath)
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Path-loss file not found: {filepath}")

        with filepath.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            for lineno, row in enumerate(reader, start=1):
                # Strip whitespace from every cell; drop empty trailing cells
                row = [cell.strip() for cell in row if cell.strip() != ""]
                if not row:
                    continue

                # First column must be an integer frequency
                try:
                    freq = int(row[0])
                except ValueError:
                    # Might be a header row or comment — skip silently
                    continue

                # Parse up to 4 antenna loss values
                losses: list[Optional[float]] = []
                for i in range(1, 5):
                    if i < len(row):
                        try:
                            losses.append(float(row[i]))
                        except ValueError:
                            losses.append(None)
                    else:
                        losses.append(None)

                table._table[freq] = losses

        return table

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_loss(
        self,
        freq_mhz: int,
        antenna: str,
        *,
        nearest: bool = True,
    ) -> Optional[float]:
        """
        Return the path-loss (dB) for a given frequency and antenna.

        Parameters
        ----------
        freq_mhz : int
            Carrier frequency in MHz (e.g. 2412, 5500).
        antenna : str
            Antenna label, e.g. "ANT1", "ANT2", "ANT3", "ANT4".
        nearest : bool
            If True and an exact frequency match is not found, return the
            loss for the nearest frequency in the table.
            If False, return None when no exact match exists.

        Returns
        -------
        float or None
            Path-loss in dB, or None if the antenna is unknown or no
            suitable entry was found.
        """
        ant_idx = _ANT_INDEX.get(antenna.upper())
        if ant_idx is None:
            return None

        # Try exact match first
        if freq_mhz in self._table:
            return self._table[freq_mhz][ant_idx]

        if not nearest or not self._table:
            return None

        # Find nearest frequency
        closest = min(self._table.keys(), key=lambda f: abs(f - freq_mhz))
        return self._table[closest][ant_idx]
    
    def apply_correction(
        self,
        freq_mhz: int,
        antenna: str,
        correction_db: float,
    ) -> float:
        """
        Apply correction directly to the in-memory table.

        Returns
        -------
        float
            The updated loss value.
        """
        ant_idx = _ANT_INDEX.get(antenna.upper())

        if ant_idx is None:
            raise ValueError(f"Unknown antenna: {antenna}")

        if freq_mhz not in self._table:
            raise KeyError(f"Frequency not found: {freq_mhz}")

        current = self._table[freq_mhz][ant_idx]

        if current is None:
            raise ValueError(
                f"No path-loss value for {freq_mhz} / {antenna}"
            )

        updated = round(current + correction_db, 2)

        self._table[freq_mhz][ant_idx] = updated

        return updated
    
    def save(self, filepath: str | Path | None = None) -> None:
        """
        Save the current table back to CSV.
        """
        path = Path(filepath or self.source_path)

        tmp_path = path.with_suffix(".tmp")

        with tmp_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)

            for freq in sorted(self._table.keys()):
                losses = self._table[freq]

                row = [freq]

                for value in losses:
                    if value is None:
                        row.append("")
                    else:
                        row.append(f"{value:.2f}")

                writer.writerow(row)

        tmp_path.replace(path)

    def backup(self) -> Path:
        """
        Create timestamped backup of the source CSV.

        Returns
        -------
        Path
            Backup file path.
        """
        source = Path(self.source_path)

        backup_dir = source.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = (
            backup_dir /
            f"{source.stem}_{timestamp}{source.suffix}"
        )

        shutil.copy2(source, backup_path)

        return backup_path

    def has_freq(self, freq_mhz: int) -> bool:
        """Return True if the table has an exact entry for *freq_mhz*."""
        return freq_mhz in self._table

    def frequencies(self) -> list[int]:
        """Return all frequencies (MHz) present in the table, sorted."""
        return sorted(self._table.keys())

    def all_losses(self) -> dict[int, list[Optional[float]]]:
        """Return a copy of the internal table (freq → [ant1..ant4])."""
        return dict(self._table)

    def __len__(self) -> int:
        return len(self._table)

    def __repr__(self) -> str:
        return (
            f"PathLossTable(source={self.source_path!r}, "
            f"entries={len(self._table)})"
        )
