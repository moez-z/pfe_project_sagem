"""
core/log_validator.py
---------------------
Pre-flight validation of parsed logs before running calibration.

Raises LogValidationError (a structured exception) listing every
problem found so the UI can display them clearly to the user.

Usage
-----
    from core.log_validator import LogValidator, LogValidationError

    try:
        LogValidator.validate(origin_log, dut_log)
    except LogValidationError as e:
        show_error(str(e))
        return
    # safe to proceed
"""

from dataclasses import dataclass, field
from typing import Optional
from .models import ParsedLog


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

class Severity:
    ERROR   = "ERROR"    # Blocks calibration
    WARNING = "WARNING"  # Shown but does not block


@dataclass
class ValidationIssue:
    severity: str        # Severity.ERROR | Severity.WARNING
    code: str            # Short machine-readable code
    message: str         # Human-readable description
    source: str = ""     # "origin" | "dut" | "both"


class LogValidationError(Exception):
    """
    Raised when one or more ERROR-level issues are found.
    The .issues list contains all ValidationIssue objects (errors + warnings).
    """
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        errors   = [i for i in issues if i.severity == Severity.ERROR]
        warnings = [i for i in issues if i.severity == Severity.WARNING]

        lines = ["Log validation failed — calibration cannot run.\n"]
        if errors:
            lines.append(f"  ✖  {len(errors)} error(s):")
            for i in errors:
                src = f" [{i.source}]" if i.source else ""
                lines.append(f"      • {i.message}{src}")
        if warnings:
            lines.append(f"\n  ⚠  {len(warnings)} warning(s):")
            for i in warnings:
                src = f" [{i.source}]" if i.source else ""
                lines.append(f"      • {i.message}{src}")

        super().__init__("\n".join(lines))

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class LogValidator:
    """
    Stateless validator.  Call LogValidator.validate(origin, dut).

    Raises LogValidationError if any ERROR-level issue is found.
    Returns a (possibly empty) list of WARNING ValidationIssues if all clear.
    """

    # Minimum number of TX and RX blocks to consider a log usable
    MIN_TX_BLOCKS = 1
    MIN_RX_BLOCKS = 0   # RX-only logs not required but checked if present

    @staticmethod
    def validate(
        origin: ParsedLog,
        dut: ParsedLog,
    ) -> list[ValidationIssue]:
        """
        Run all checks.  Returns warnings list if OK, raises LogValidationError
        if any blocking error is found.
        """
        issues: list[ValidationIssue] = []

        issues += LogValidator._check_file_readable(origin, "origin")
        issues += LogValidator._check_file_readable(dut, "dut")
        issues += LogValidator._check_blocks_present(origin, "origin")
        issues += LogValidator._check_blocks_present(dut, "dut")
        issues += LogValidator._check_tx_data_quality(origin, "origin")
        issues += LogValidator._check_tx_data_quality(dut, "dut")
        issues += LogValidator._check_rx_data_quality(origin, "origin")
        issues += LogValidator._check_rx_data_quality(dut, "dut")
        issues += LogValidator._check_product_match(origin, dut)
        issues += LogValidator._check_block_overlap(origin, dut)

        errors = [i for i in issues if i.severity == Severity.ERROR]
        if errors:
            raise LogValidationError(issues)

        return [i for i in issues if i.severity == Severity.WARNING]

    # -----------------------------------------------------------------------
    # Individual checks
    # -----------------------------------------------------------------------

    @staticmethod
    def _check_file_readable(log: ParsedLog, source: str) -> list[ValidationIssue]:
        """Check the file was actually read without parse errors."""
        issues = []
        fatal_warnings = [w for w in log.parse_warnings if "Cannot read" in w]
        if fatal_warnings:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="FILE_UNREADABLE",
                message=f"File could not be read: {fatal_warnings[0]}",
                source=source,
            ))
        elif log.parse_warnings:
            for w in log.parse_warnings:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code="PARSE_WARNING",
                    message=w,
                    source=source,
                ))
        return issues

    @staticmethod
    def _check_blocks_present(log: ParsedLog, source: str) -> list[ValidationIssue]:
        """Ensure the log contains at least some usable TX blocks."""
        issues = []

        if len(log.tx_blocks) < LogValidator.MIN_TX_BLOCKS:
            # Distinguish "found block headers but data was null/missing"
            # from "no block headers at all — wrong file / corrupted".
            if log.rejected_tx_blocks:
                bad_nums = sorted({n for n, _, _ in log.rejected_tx_blocks})
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="NO_TX_BLOCKS",
                    message=(
                        f"{len(bad_nums)} TX block header(s) were found "
                        f"(blocks {', '.join(str(n) for n in bad_nums[:8])}"
                        f"{' …' if len(bad_nums) > 8 else ''}) but every one has "
                        f"null/missing power data. The log capture likely stopped "
                        f"mid-test or the file is truncated."
                    ),
                    source=source,
                ))
            else:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="NO_TX_BLOCKS",
                    message=(
                        f"No TX measurement blocks found. "
                        f"The file may be empty, corrupted, or not a calibration log."
                    ),
                    source=source,
                ))

        if len(log.tx_blocks) == 0 and len(log.rx_blocks) == 0:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="EMPTY_LOG",
                message="Log contains no TX or RX blocks at all.",
                source=source,
            ))

        return issues

    @staticmethod
    def _check_tx_data_quality(log: ParsedLog, source: str) -> list[ValidationIssue]:
        """Check every TX block has a valid measured power value."""
        issues = []

        null_blocks = [
            b for b in log.tx_blocks
            if b.tx_measured_dbm is None
        ]
        if null_blocks:
            # This shouldn't happen (parser already drops them), but guard anyway
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="TX_NULL_POWER",
                message=(
                    f"{len(null_blocks)} TX block(s) have no measured power "
                    f"(POWER_DBM_RMS_AVG_S1 missing or null). "
                    f"Blocks: {', '.join(b.label for b in null_blocks[:5])}"
                    + (" …" if len(null_blocks) > 5 else "")
                ),
                source=source,
            ))

        # Blocks whose header was detected but data was null/missing
        # (and NOT explicitly marked "Skipped" by the test station).
        # These never made it into log.tx_blocks, so they must be
        # surfaced here or they'd silently vanish from calibration.
        if log.rejected_tx_blocks:
            bad_nums = sorted({n for n, _, _ in log.rejected_tx_blocks})
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="TX_BLOCK_NULL_DATA",
                message=(
                    f"{len(bad_nums)} TX block(s) (numbers "
                    f"{', '.join(str(n) for n in bad_nums[:8])}"
                    f"{' …' if len(bad_nums) > 8 else ''}) were detected in the "
                    f"log but have no usable power measurement, and were not "
                    f"marked as intentionally skipped by the test station. "
                    f"This usually means the capture was interrupted or the "
                    f"file is corrupted/truncated."
                ),
                source=source,
            ))

        # Informational: blocks explicitly skipped by the test station.
        # Not an error — the station chose to skip them — but worth a
        # warning so the operator knows coverage is incomplete.
        if log.skipped_tx_blocks:
            skipped_nums = sorted({n for n, _ in log.skipped_tx_blocks})
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="TX_BLOCK_SKIPPED",
                message=(
                    f"{len(skipped_nums)} TX block(s) (numbers "
                    f"{', '.join(str(n) for n in skipped_nums[:8])}"
                    f"{' …' if len(skipped_nums) > 8 else ''}) were marked "
                    f"'Skipped' by the test station and will not be calibrated."
                ),
                source=source,
            ))

        # Check for physically impossible power values
        bad_power = [
            b for b in log.tx_blocks
            if b.tx_measured_dbm is not None and not (-30 <= b.tx_measured_dbm <= 40)
        ]
        if bad_power:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="TX_POWER_OUT_OF_RANGE",
                message=(
                    f"{len(bad_power)} TX block(s) have power outside the "
                    f"physical range [-30, 40] dBm — likely a measurement error. "
                    f"Blocks: {', '.join(b.label for b in bad_power[:3])}"
                    + (" …" if len(bad_power) > 3 else "")
                ),
                source=source,
            ))

        # Warn if a block is missing a target power
        no_target = [b for b in log.tx_blocks if b.tx_target_dbm is None]
        if no_target:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="TX_NO_TARGET",
                message=(
                    f"{len(no_target)} TX block(s) have no TX_POWER_DBM target value."
                ),
                source=source,
            ))

        # Warn about missing frequency info
        no_freq = [b for b in log.tx_blocks if b.freq_mhz == 0]
        if no_freq:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="TX_NO_FREQ",
                message=(
                    f"{len(no_freq)} TX block(s) have no frequency — cannot "
                    f"determine band or match blocks across logs."
                ),
                source=source,
            ))

        return issues

    @staticmethod
    def _check_rx_data_quality(log: ParsedLog, source: str) -> list[ValidationIssue]:
        """Check RX blocks have at least PER or RSSI data."""
        issues = []

        if not log.rx_blocks and not log.rejected_rx_blocks and not log.skipped_rx_blocks:
            return issues   # No RX at all is valid (some logs are TX-only)

        no_per = [b for b in log.rx_blocks if b.per is None and b.rssi_rx1 is None]
        if no_per:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="RX_NO_DATA",
                message=(
                    f"{len(no_per)} RX block(s) have no PER or RSSI data."
                ),
                source=source,
            ))

        # RX block headers detected but with null/missing data, and NOT
        # explicitly marked "Skipped" by the test station — a real gap.
        if log.rejected_rx_blocks:
            bad_nums = sorted({n for n, _, _ in log.rejected_rx_blocks})
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="RX_BLOCK_NULL_DATA",
                message=(
                    f"{len(bad_nums)} RX block(s) (numbers "
                    f"{', '.join(str(n) for n in bad_nums[:8])}"
                    f"{' …' if len(bad_nums) > 8 else ''}) were detected in the "
                    f"log but have no usable PER/RSSI measurement, and were not "
                    f"marked as intentionally skipped. This usually means the "
                    f"capture was interrupted or the file is corrupted/truncated."
                ),
                source=source,
            ))

        # Informational: RX blocks explicitly skipped by the test station.
        if log.skipped_rx_blocks:
            skipped_nums = sorted({n for n, _ in log.skipped_rx_blocks})
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="RX_BLOCK_SKIPPED",
                message=(
                    f"{len(skipped_nums)} RX block(s) (numbers "
                    f"{', '.join(str(n) for n in skipped_nums[:8])}"
                    f"{' …' if len(skipped_nums) > 8 else ''}) were marked "
                    f"'Skipped' by the test station and will not be compared."
                ),
                source=source,
            ))

        return issues

    @staticmethod
    def _check_product_match(origin: ParsedLog, dut: ParsedLog) -> list[ValidationIssue]:
        """Warn if origin and DUT logs come from different products."""
        issues = []

        op = (origin.metadata.product_name or "").strip().upper()
        dp = (dut.metadata.product_name or "").strip().upper()

        if op and dp and op != dp:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="PRODUCT_MISMATCH",
                message=(
                    f"Product mismatch: origin is '{origin.metadata.product_name}' "
                    f"but DUT is '{dut.metadata.product_name}'. "
                    f"Comparing logs from different products is not valid."
                ),
                source="both",
            ))

        if not op:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="NO_PRODUCT_NAME",
                message="Could not determine product name from origin log.",
                source="origin",
            ))
        if not dp:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="NO_PRODUCT_NAME",
                message="Could not determine product name from DUT log.",
                source="dut",
            ))

        return issues

    @staticmethod
    def _check_block_overlap(origin: ParsedLog, dut: ParsedLog) -> list[ValidationIssue]:
        """Ensure origin and DUT share at least some matching TX blocks."""
        issues = []

        if not origin.tx_blocks or not dut.tx_blocks:
            return issues  # Already caught by _check_blocks_present

        def tx_sig(b):
            return (b.block_number, b.freq_mhz, b.modulation, b.bandwidth, b.antenna)

        origin_sigs = {tx_sig(b) for b in origin.tx_blocks}
        dut_sigs    = {tx_sig(b) for b in dut.tx_blocks}
        common      = origin_sigs & dut_sigs

        if not common:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="NO_MATCHING_BLOCKS",
                message=(
                    f"Origin ({len(origin_sigs)} TX blocks) and DUT "
                    f"({len(dut_sigs)} TX blocks) share no matching blocks. "
                    f"The logs may be from different test configurations."
                ),
                source="both",
            ))
        else:
            # Warn if significant mismatch
            total  = len(origin_sigs | dut_sigs)
            match_pct = len(common) / total * 100
            if match_pct < 50:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code="LOW_BLOCK_OVERLAP",
                    message=(
                        f"Only {len(common)}/{total} TX blocks match between "
                        f"origin and DUT ({match_pct:.0f}%). Many blocks will be "
                        f"marked UNMATCHED."
                    ),
                    source="both",
                ))

            # Warn about blocks in DUT not present in origin
            dut_only = dut_sigs - origin_sigs
            if dut_only:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code="DUT_EXTRA_BLOCKS",
                    message=(
                        f"{len(dut_only)} TX block(s) in DUT log have no counterpart "
                        f"in the origin log and will be marked UNMATCHED."
                    ),
                    source="dut",
                ))

        return issues