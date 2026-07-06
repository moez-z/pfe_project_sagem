from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

class Severity:
    ERROR   = "ERROR"    # Blocks loading
    WARNING = "WARNING"  # Shown but does not block


@dataclass
class ValidationIssue:
    severity: str        # Severity.ERROR | Severity.WARNING
    code: str            # Short machine-readable code
    message: str         # Human-readable description


class PathLossValidationError(Exception):
    """
    Raised when one or more ERROR-level issues are found.
    The .issues list contains all ValidationIssue objects (errors + warnings).
    """
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        errors   = [i for i in issues if i.severity == Severity.ERROR]
        warnings = [i for i in issues if i.severity == Severity.WARNING]

        lines = ["Path-loss file validation failed — file was not loaded.\n"]
        if errors:
            lines.append(f"  ✖  {len(errors)} error(s):")
            for i in errors:
                lines.append(f"      • {i.message}")
        if warnings:
            lines.append(f"\n  ⚠  {len(warnings)} warning(s):")
            for i in warnings:
                lines.append(f"      • {i.message}")

        super().__init__("\n".join(lines))


# ---------------------------------------------------------------------------
# Tunable thresholds — FORMAT ONLY, no data-plausibility limits here.
# ---------------------------------------------------------------------------

MIN_VALID_ROWS = 1   # at least 1 usable freq,ant1..ant4 row required


class PathLossValidator:
    """
    Static validation entry point — mirrors LogValidator's shape.

    Checks structure/format only:
      - file exists and is readable
      - file is not empty
      - contains at least one row shaped like 'freq,ant1,ant2,ant3,ant4'
      - the frequency column parses as an integer
      - antenna columns parse as numbers (or are blank/missing)

    Does NOT check:
      - whether frequency values fall in a "normal" WiFi range
      - whether loss values fall in a "plausible" dB range
      - whether values look like outliers compared to other antennas
    Non-standard data is allowed through; only structural problems block.
    """

    @staticmethod
    def validate_file(filepath: str | Path) -> list[ValidationIssue]:
        """
        Validate a path_loss.csv file before it is loaded for real use.

        Raises PathLossValidationError if any ERROR-level issue is found.
        Returns the list of WARNING-level issues on success (may be empty).
        """
        filepath = Path(filepath)
        issues: list[ValidationIssue] = []

        # ── File existence / extension ──────────────────────────────────────
        if not filepath.exists():
            raise PathLossValidationError([ValidationIssue(
                Severity.ERROR, "FILE_NOT_FOUND",
                f"File not found: {filepath}",
            )])

        if filepath.suffix.lower() != ".csv":
            issues.append(ValidationIssue(
                Severity.WARNING, "WRONG_EXTENSION",
                f"File does not have a .csv extension: {filepath.name}",
            ))

        # ── Read file ────────────────────────────────────────────────────────
        try:
            raw_text = filepath.read_text(encoding="utf-8-sig")
        except Exception as exc:
            raise PathLossValidationError([ValidationIssue(
                Severity.ERROR, "READ_ERROR",
                f"Could not read file: {exc}",
            )])

        if not raw_text.strip():
            raise PathLossValidationError([ValidationIssue(
                Severity.ERROR, "EMPTY_FILE",
                "The file is completely empty.",
            )])

        # ── Parse rows — format check only ──────────────────────────────────
        valid_rows: list[dict] = []
        malformed_lines: list[tuple[int, str]] = []
        seen_freqs: dict[int, int] = {}   # freq -> first line number seen

        reader = csv.reader(raw_text.splitlines())
        any_content_line = False

        for lineno, raw in enumerate(reader, start=1):
            row = [c.strip() for c in raw]
            while row and row[-1] == "":
                row.pop()
            if not row:
                continue                       # blank line, ignore
            if row[0].startswith("#"):
                continue                       # comment line, ignore

            any_content_line = True

            # First column must be an integer frequency
            try:
                freq = int(row[0])
            except ValueError:
                # Could be a header row (e.g. "freq_mhz,ant1,...") — only
                # tolerate this on line 1; anywhere else it's a real problem.
                if lineno == 1:
                    continue
                malformed_lines.append((lineno, ",".join(row)))
                continue

            if len(row) < 2:
                # No antenna columns at all — not a usable row
                malformed_lines.append((lineno, ",".join(row)))
                continue

            # Parse up to 4 antenna loss values — numeric format only,
            # no range/plausibility judgement on the value itself.
            losses: list[Optional[float]] = []
            bad_cells: list[str] = []
            for i in range(1, 5):
                if i < len(row) and row[i] != "":
                    try:
                        losses.append(float(row[i].replace(",", ".")))
                    except ValueError:
                        losses.append(None)
                        bad_cells.append(row[i])
                else:
                    losses.append(None)

            if all(v is None for v in losses):
                malformed_lines.append((lineno, ",".join(row)))
                continue

            if bad_cells:
                issues.append(ValidationIssue(
                    Severity.WARNING, "UNPARSEABLE_CELL",
                    f"Line {lineno} (freq {row[0]}): could not parse value(s) "
                    f"{bad_cells} as a number — treated as missing.",
                ))

            if freq in seen_freqs:
                issues.append(ValidationIssue(
                    Severity.WARNING, "DUPLICATE_FREQ",
                    f"Frequency {freq} MHz appears more than once "
                    f"(line {seen_freqs[freq]} and line {lineno}); "
                    f"the later row will overwrite the earlier one.",
                ))
            else:
                seen_freqs[freq] = lineno

            valid_rows.append({
                "lineno": lineno,
                "freq": freq,
                "losses": losses,
            })

        # ── No usable content at all ────────────────────────────────────────
        if not any_content_line:
            raise PathLossValidationError([ValidationIssue(
                Severity.ERROR, "NO_DATA_ROWS",
                "The file contains no data rows (only blank lines or comments).",
            )])

        # ── Malformed lines ──────────────────────────────────────────────────
        if malformed_lines:
            preview = "; ".join(
                f"line {n}: \"{txt}\"" for n, txt in malformed_lines[:5]
            )
            more = f" (+{len(malformed_lines) - 5} more)" if len(malformed_lines) > 5 else ""
            issues.append(ValidationIssue(
                Severity.ERROR, "MALFORMED_ROWS",
                f"{len(malformed_lines)} row(s) could not be parsed — "
                f"expected 'freq,ant1,ant2,ant3,ant4'. {preview}{more}",
            ))

        # ── No valid rows survived ───────────────────────────────────────────
        if len(valid_rows) < MIN_VALID_ROWS:
            raise PathLossValidationError(issues + [ValidationIssue(
                Severity.ERROR, "NO_VALID_ROWS",
                "No valid frequency/loss rows were found in the file. "
                "The file may be empty, corrupted, or in the wrong format. "
                "Expected format: freq_mhz,loss_ant1,loss_ant2,loss_ant3,loss_ant4",
            )])

        # ── Missing antenna data (format note, not a value judgement) ───────
        rows_missing_some = [
            r for r in valid_rows
            if any(v is None for v in r["losses"]) and not all(v is None for v in r["losses"])
        ]
        if rows_missing_some:
            issues.append(ValidationIssue(
                Severity.WARNING, "PARTIAL_ANTENNA_DATA",
                f"{len(rows_missing_some)} row(s) have at least one missing "
                f"antenna value (e.g. {rows_missing_some[0]['freq']} MHz).",
            ))

        # ── Raise if any ERROR-level issue was collected ────────────────────
        errors = [i for i in issues if i.severity == Severity.ERROR]
        if errors:
            raise PathLossValidationError(issues)

        return issues