from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from .models import Band, ParsedLog, TxBlock, RxBlock


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default tolerance (dBm): delta > this value → flag for correction
DEFAULT_TX_TOLERANCE_DBM = 0.5

# Maximum acceptable calibration correction (dBm)
# Beyond this, something is likely wrong with the hardware
MAX_CORRECTION_DBM = 5.0


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

class TxStatus(Enum):
    PASS          = "PASS"           # Measured within limits
    FAIL          = "FAIL"           # Measured outside limits
    NEEDS_CORRECTION = "NEEDS_CORRECTION"  # Delta > tolerance (no hard limits)
    OK            = "OK"             # Delta within tolerance (no hard limits)
    NO_LIMIT      = "NO_LIMIT"       # No limits defined, delta acceptable
    UNMATCHED     = "UNMATCHED"      # No corresponding block in origin


class RxStatus(Enum):
    PASS       = "PASS"
    FAIL       = "FAIL"
    INVALID    = "INVALID"   # RSSI = -999 (multi-antenna aggregate, expected)
    UNMATCHED  = "UNMATCHED"


@dataclass
class TxCalibrationResult:
    """
    Result of comparing one TX block (DUT) against its Origin counterpart.

    delta_dbm = dut_measured − origin_measured
        > 0 → DUT emits more power than origin  (reduce target)
        < 0 → DUT emits less power than origin  (increase target)

    correction_dbm = −delta_dbm
        This is the value to add to the EEPROM calibration offset
        so that the DUT matches the origin.
    """
    # --- Identification ---
    band: Optional[Band] = None
    freq_mhz: int = 0
    modulation: str = ""
    bandwidth: str = ""
    antenna: str = ""
    block_number: int = 0

    # --- Measured values ---
    origin_measured_dbm: Optional[float] = None
    dut_measured_dbm: Optional[float] = None
    tx_target_dbm: Optional[float] = None
    tx_limit_lo: Optional[float] = None
    tx_limit_hi: Optional[float] = None

    # --- Calibration computation ---
    delta_dbm: Optional[float] = None        # DUT − Origin
    correction_dbm: Optional[float] = None  # −delta (apply to EEPROM)
    tolerance_used: float = DEFAULT_TX_TOLERANCE_DBM

    # --- Status ---
    status: TxStatus = TxStatus.UNMATCHED
    warning: str = ""

    @property
    def needs_correction(self) -> bool:
        return self.status in (TxStatus.FAIL, TxStatus.NEEDS_CORRECTION)

    @property
    def label(self) -> str:
        return (f"{self.block_number}.TX {self.freq_mhz}MHz "
                f"{self.modulation} {self.bandwidth} {self.antenna}")

    @property
    def limits_str(self) -> str:
        if self.tx_limit_lo is not None and self.tx_limit_hi is not None:
            return f"({self.tx_limit_lo}, {self.tx_limit_hi})"
        return "—"

    @property
    def delta_str(self) -> str:
        if self.delta_dbm is None:
            return "—"
        sign = "+" if self.delta_dbm >= 0 else ""
        return f"{sign}{self.delta_dbm:.3f} dBm"

    @property
    def correction_str(self) -> str:
        if self.correction_dbm is None:
            return "—"
        sign = "+" if self.correction_dbm >= 0 else ""
        return f"{sign}{self.correction_dbm:.3f} dBm"


@dataclass
class RxComparisonResult:
    """Result of comparing one RX block (DUT) against its Origin counterpart."""
    # --- Identification ---
    band: Optional[Band] = None
    freq_mhz: int = 0
    mcs: str = ""
    bandwidth: str = ""
    antenna_label: str = ""
    block_number: int = 0

    # --- Measured values ---
    origin_rssi: Optional[float] = None
    dut_rssi: Optional[float] = None
    rssi_delta: Optional[float] = None       # DUT − Origin

    origin_per: Optional[float] = None
    dut_per: Optional[float] = None
    per_limit_hi: Optional[float] = None

    # --- Status ---
    status: RxStatus = RxStatus.UNMATCHED
    warning: str = ""

    @property
    def label(self) -> str:
        return (f"{self.block_number}.RX {self.freq_mhz}MHz "
                f"{self.mcs} {self.bandwidth} {self.antenna_label}")

    @property
    def rssi_delta_str(self) -> str:
        if self.rssi_delta is None:
            return "—"
        sign = "+" if self.rssi_delta >= 0 else ""
        return f"{sign}{self.rssi_delta:.1f} dBm"


@dataclass
class CalibrationReport:
    """
    Full report produced by CalibrationEngine.compare().
    Contains all TX and RX results plus summary statistics.
    """
    origin_filename: str = ""
    dut_filename: str = ""
    dut_serial: str = ""
    origin_serial: str = ""
    product_name: str = ""
    tolerance_dbm: float = DEFAULT_TX_TOLERANCE_DBM

    tx_results: list[TxCalibrationResult] = field(default_factory=list)
    rx_results: list[RxComparisonResult]  = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # --- TX summary ---
    @property
    def tx_pass_count(self) -> int:
        return sum(1 for r in self.tx_results if r.status == TxStatus.PASS)

    @property
    def tx_fail_count(self) -> int:
        return sum(1 for r in self.tx_results if r.status == TxStatus.FAIL)

    @property
    def tx_needs_correction_count(self) -> int:
        return sum(1 for r in self.tx_results if r.status == TxStatus.NEEDS_CORRECTION)

    @property
    def tx_ok_count(self) -> int:
        return sum(1 for r in self.tx_results
                   if r.status in (TxStatus.OK, TxStatus.NO_LIMIT))

    @property
    def tx_max_delta(self) -> Optional[float]:
        deltas = [abs(r.delta_dbm) for r in self.tx_results
                  if r.delta_dbm is not None]
        return max(deltas) if deltas else None

    @property
    def tx_avg_delta(self) -> Optional[float]:
        deltas = [r.delta_dbm for r in self.tx_results
                  if r.delta_dbm is not None]
        return sum(deltas) / len(deltas) if deltas else None

    # --- RX summary ---
    @property
    def rx_pass_count(self) -> int:
        return sum(1 for r in self.rx_results if r.status == RxStatus.PASS)

    @property
    def rx_fail_count(self) -> int:
        return sum(1 for r in self.rx_results if r.status == RxStatus.FAIL)

    @property
    def rx_invalid_count(self) -> int:
        return sum(1 for r in self.rx_results if r.status == RxStatus.INVALID)

    @property
    def overall_pass(self) -> bool:
        return (self.tx_fail_count == 0 and
                self.tx_needs_correction_count == 0 and
                self.rx_fail_count == 0)

    def by_band(self, band: Band) -> "CalibrationReport":
        """Return a filtered view with only results for the given band."""
        sub = CalibrationReport(
            origin_filename=self.origin_filename,
            dut_filename=self.dut_filename,
            dut_serial=self.dut_serial,
            origin_serial=self.origin_serial,
            product_name=self.product_name,
            tolerance_dbm=self.tolerance_dbm,
        )
        sub.tx_results = [r for r in self.tx_results if r.band == band]
        sub.rx_results = [r for r in self.rx_results if r.band == band]
        return sub

    def summary(self) -> str:
        """Human-readable summary string."""
        lines = [
            "=" * 60,
            "  CALIBRATION REPORT",
            "=" * 60,
            f"  DUT     : {self.dut_serial}",
            f"  Origin  : {self.origin_serial}",
            f"  Product : {self.product_name}",
            f"  Tolerance: ±{self.tolerance_dbm} dBm",
            "-" * 60,
            "  TX CALIBRATION",
            f"    Total blocks  : {len(self.tx_results)}",
            f"    PASS (limits) : {self.tx_pass_count}",
            f"    FAIL (limits) : {self.tx_fail_count}",
            f"    Correction needed : {self.tx_needs_correction_count}",
            f"    Within tolerance  : {self.tx_ok_count}",
        ]
        if self.tx_avg_delta is not None:
            sign = "+" if self.tx_avg_delta >= 0 else ""
            lines.append(f"    Avg delta : {sign}{self.tx_avg_delta:.3f} dBm")
        if self.tx_max_delta is not None:
            lines.append(f"    Max |delta|: {self.tx_max_delta:.3f} dBm")

        lines += [
            "-" * 60,
            "  RX COMPARISON",
            f"    Total blocks : {len(self.rx_results)}",
            f"    PASS         : {self.rx_pass_count}",
            f"    FAIL         : {self.rx_fail_count}",
            f"    N/A (RSSI -999): {self.rx_invalid_count}",
            "-" * 60,
            f"  OVERALL: {'✅ PASS' if self.overall_pass else '❌ FAIL / CORRECTION NEEDED'}",
            "=" * 60,
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CalibrationEngine
# ---------------------------------------------------------------------------

class CalibrationEngine:
    """
    Core comparison engine.

    Block matching strategy
    -----------------------
    Blocks are matched by their "signature":
        (block_number, band, freq_mhz, modulation, bandwidth, antenna)

    This is more robust than matching by index alone because the block
    numbers may not always be in the same order between the origin and DUT
    logs (some blocks can be skipped).
    """

    @staticmethod
    def compare(
        origin: ParsedLog,
        dut: ParsedLog,
        tolerance_dbm: float = DEFAULT_TX_TOLERANCE_DBM,
    ) -> CalibrationReport:
        """
        Compare a DUT log against the Origin/Reference log.

        Parameters
        ----------
        origin : ParsedLog
            The reference (golden/silver) log.
        dut : ParsedLog
            The log from the device being calibrated.
        tolerance_dbm : float
            TX delta threshold above which correction is flagged.
            Default = 0.5 dBm.

        Returns
        -------
        CalibrationReport
        """
        report = CalibrationReport(
            origin_filename=origin.metadata.filename,
            dut_filename=dut.metadata.filename,
            dut_serial=dut.metadata.serial_number,
            origin_serial=origin.metadata.serial_number,
            product_name=dut.metadata.product_name or origin.metadata.product_name,
            tolerance_dbm=tolerance_dbm,
        )

        # Build lookup maps keyed by block signature
        origin_tx_map = CalibrationEngine._build_tx_map(origin.tx_blocks)
        origin_rx_map = CalibrationEngine._build_rx_map(origin.rx_blocks)

        # --- TX comparison ---
        for dut_blk in dut.tx_blocks:
            sig = CalibrationEngine._tx_signature(dut_blk)
            orig_blk = origin_tx_map.get(sig)
            result = CalibrationEngine._compare_tx_block(
                dut_blk, orig_blk, tolerance_dbm
            )
            report.tx_results.append(result)

        # --- Flag DUT blocks missing from origin ---
        dut_tx_sigs = {CalibrationEngine._tx_signature(b) for b in dut.tx_blocks}
        for sig, orig_blk in origin_tx_map.items():
            if sig not in dut_tx_sigs:
                report.warnings.append(
                    f"TX block missing in DUT: {orig_blk.label}"
                )

        # --- RX comparison ---
        for dut_blk in dut.rx_blocks:
            sig = CalibrationEngine._rx_signature(dut_blk)
            orig_blk = origin_rx_map.get(sig)
            result = CalibrationEngine._compare_rx_block(dut_blk, orig_blk)
            report.rx_results.append(result)

        # Carry over parse warnings
        report.warnings += dut.parse_warnings + origin.parse_warnings

        return report

    # -----------------------------------------------------------------------
    # TX block comparison
    # -----------------------------------------------------------------------

    @staticmethod
    def _compare_tx_block(
        dut: TxBlock,
        origin: Optional[TxBlock],
        tolerance: float,
    ) -> TxCalibrationResult:

        res = TxCalibrationResult(
            band=dut.band,
            freq_mhz=dut.freq_mhz,
            modulation=dut.modulation,
            bandwidth=dut.bandwidth,
            antenna=dut.antenna,
            block_number=dut.block_number,
            dut_measured_dbm=dut.tx_measured_dbm,
            tx_target_dbm=dut.tx_target_dbm,
            tx_limit_lo=dut.tx_limit_lo,
            tx_limit_hi=dut.tx_limit_hi,
            tolerance_used=tolerance,
        )

        if origin is None:
            res.status = TxStatus.UNMATCHED
            res.warning = "No matching block in origin log"
            return res

        res.origin_measured_dbm = origin.tx_measured_dbm

        # Compute delta
        if dut.tx_measured_dbm is not None and origin.tx_measured_dbm is not None:
            delta = round(dut.tx_measured_dbm - origin.tx_measured_dbm, 4)
            res.delta_dbm = delta
            res.correction_dbm = round(-(delta / 2), 4)

            # Sanity check — huge delta means hardware issue
            if abs(delta) > MAX_CORRECTION_DBM:
                res.warning = (
                    f"Delta {delta:+.2f} dBm exceeds max correction "
                    f"({MAX_CORRECTION_DBM} dBm) — hardware issue?"
                )

        # Determine status
        if dut.has_limits and dut.tx_measured_dbm is not None:
            # Hard limits present in the log
            if dut.passes_limits:
                res.status = TxStatus.PASS
            else:
                res.status = TxStatus.FAIL
        elif res.delta_dbm is not None:
            # No hard limits — use tolerance on delta
            if abs(res.delta_dbm) > tolerance:
                res.status = TxStatus.NEEDS_CORRECTION
            else:
                res.status = TxStatus.OK
        else:
            res.status = TxStatus.NO_LIMIT

        return res

    # -----------------------------------------------------------------------
    # RX block comparison
    # -----------------------------------------------------------------------

    @staticmethod
    def _compare_rx_block(
        dut: RxBlock,
        origin: Optional[RxBlock],
    ) -> RxComparisonResult:

        res = RxComparisonResult(
            band=dut.band,
            freq_mhz=dut.freq_mhz,
            mcs=dut.mcs,
            bandwidth=dut.bandwidth,
            antenna_label=dut.antenna_label,
            block_number=dut.block_number,
            dut_rssi=dut.rssi_rx1,
            dut_per=dut.per,
            per_limit_hi=dut.per_limit_hi,
        )

        if origin:
            res.origin_rssi = origin.rssi_rx1
            res.origin_per  = origin.per

        # RSSI -999 is a sentinel for multi-antenna aggregate blocks
        if not dut.rssi_valid:
            res.status = RxStatus.INVALID
            return res

        # PER check (primary pass/fail criterion for RX)
        per_hi = dut.per_limit_hi if dut.per_limit_hi is not None else 10.0
        if dut.per is not None:
            res.status = RxStatus.PASS if dut.per <= per_hi else RxStatus.FAIL
        else:
            res.status = RxStatus.UNMATCHED

        # RSSI delta (informational)
        if (origin and origin.rssi_valid and
                dut.rssi_rx1 is not None and origin.rssi_rx1 is not None):
            res.rssi_delta = round(dut.rssi_rx1 - origin.rssi_rx1, 2)

        return res

    # -----------------------------------------------------------------------
    # Block signature helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _tx_signature(blk: TxBlock) -> tuple:
        """Unique key for matching TX blocks across two logs."""
        return (blk.block_number, blk.freq_mhz, blk.modulation,
                blk.bandwidth, blk.antenna)

    @staticmethod
    def _rx_signature(blk: RxBlock) -> tuple:
        """Unique key for matching RX blocks across two logs."""
        return (blk.block_number, blk.freq_mhz, blk.mcs,
                blk.bandwidth, blk.antenna_label)

    @staticmethod
    def _build_tx_map(blocks: list[TxBlock]) -> dict:
        return {CalibrationEngine._tx_signature(b): b for b in blocks}

    @staticmethod
    def _build_rx_map(blocks: list[RxBlock]) -> dict:
        return {CalibrationEngine._rx_signature(b): b for b in blocks}

    # -----------------------------------------------------------------------
    # Utility — blocks that need EEPROM correction
    # -----------------------------------------------------------------------

    @staticmethod
    def get_corrections(report: CalibrationReport) -> list[dict]:
        """
        Returns a list of dicts for every TX block that needs correction.
        Ready to feed into the EEPROM writer or display in a UI table.

        Each dict contains:
            band, freq_mhz, modulation, bandwidth, antenna,
            dut_measured, origin_measured, delta, correction, status
        """
        corrections = []
        for r in report.tx_results:
            if r.needs_correction:
                corrections.append({
                    "label":            r.label,
                    "band":             r.band.value if r.band else "",
                    "freq_mhz":         r.freq_mhz,
                    "modulation":       r.modulation,
                    "bandwidth":        r.bandwidth,
                    "antenna":          r.antenna,
                    "dut_measured_dbm": r.dut_measured_dbm,
                    "origin_measured_dbm": r.origin_measured_dbm,
                    "delta_dbm":        r.delta_dbm,
                    "correction_dbm":   r.correction_dbm,
                    "status":           r.status.value,
                    "warning":          r.warning,
                })
        return corrections

   