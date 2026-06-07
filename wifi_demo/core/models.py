"""
models.py
---------
Dataclasses for the WiFi calibration log parser.
Every parsed entity is represented here — no logic, pure data.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BlockType(Enum):
    TX_VERIFY = "TX_VERIFY"
    RX_VERIFY = "RX_VERIFY"


class Band(Enum):
    GHz_2_4 = "2.4 GHz"
    GHz_5   = "5 GHz"
    GHz_6   = "6 GHz"

    @staticmethod
    def from_freq(freq_mhz: int) -> "Band":
        if 2400 <= freq_mhz <= 2500:
            return Band.GHz_2_4
        elif 5150 <= freq_mhz <= 5850:
            return Band.GHz_5
        elif 5925 <= freq_mhz <= 7125:
            return Band.GHz_6
        raise ValueError(f"Cannot determine band for frequency {freq_mhz} MHz")


# ---------------------------------------------------------------------------
# Log header metadata
# ---------------------------------------------------------------------------

@dataclass
class LogMetadata:
    """Information extracted from the log file header."""
    serial_number: str = ""          # e.g. 254087406A1SC000R2504201252
    product_name: str = ""           # e.g. EDERSON
    app_version: str = ""            # e.g. BWC_V1.2.2
    test_station: str = ""           # e.g. EZR-BBS30717
    test_config: str = ""            # e.g. ATR_TEST_WIFI_CONDUIT_1;5G//6G
    test_date: str = ""              # from filename or timestamp
    filename: str = ""               # original filename


# ---------------------------------------------------------------------------
# A single TX_VERIFY test block
# ---------------------------------------------------------------------------

@dataclass
class TxBlock:
    """
    Represents one TX_VERIFY block extracted from the log.

    Key measurement: POWER_DBM_RMS_AVG_S1
    This is the actual measured RMS power at the antenna (in dBm).
    It is compared to tx_target (what the tester requested) and
    used for calibration delta computation against a reference log.
    """
    # --- Identification ---
    block_number: int = 0            # e.g. 8 from "8.TX_VERIFY ..."
    band: Optional[Band] = None      # 2.4 / 5 / 6 GHz
    freq_mhz: int = 0                # e.g. 5500
    modulation: str = ""             # e.g. OFDM-6, MCS11, DSSS-1
    standard: str = ""               # e.g. NON_HT, HE_SU
    bandwidth: str = ""              # e.g. BW-20, BW-80
    antenna: str = ""                # e.g. ANT1, ANT2, ANT3, ANT4

    # --- Key measurements ---
    tx_target_dbm: Optional[float] = None       # TX_POWER_DBM (requested)
    tx_measured_dbm: Optional[float] = None     # POWER_DBM_RMS_AVG_S1 (actual)
    tx_limit_lo: Optional[float] = None         # Lower limit from log
    tx_limit_hi: Optional[float] = None         # Upper limit from log

    # --- Secondary power metrics ---
    power_rms_max: Optional[float] = None       # POWER_DBM_RMS_MAX_S1
    power_rms_min: Optional[float] = None       # POWER_DBM_RMS_MIN_S1
    power_peak_avg: Optional[float] = None      # POWER_PEAK_AVG_VSA1
    freq_error_avg_ppm: Optional[float] = None  # FREQ_ERROR_AVG

    # --- Raw header string (for debugging) ---
    raw_header: str = ""

    @property
    def has_limits(self) -> bool:
        return self.tx_limit_lo is not None and self.tx_limit_hi is not None

    @property
    def passes_limits(self) -> Optional[bool]:
        """Returns True/False if limits exist, None otherwise."""
        if not self.has_limits or self.tx_measured_dbm is None:
            return None
        return self.tx_limit_lo <= self.tx_measured_dbm <= self.tx_limit_hi

    @property
    def label(self) -> str:
        return (f"{self.block_number}.TX {self.freq_mhz}MHz "
                f"{self.modulation} {self.bandwidth} {self.antenna}")


# ---------------------------------------------------------------------------
# A single RX_VERIFY test block
# ---------------------------------------------------------------------------

@dataclass
class RxBlock:
    """
    Represents one RX_VERIFY block extracted from the log.

    For RX we only compare — no calibration correction is applied.
    Key metrics: RSSI per antenna chain, PER (Packet Error Rate).
    """
    # --- Identification ---
    block_number: int = 0
    band: Optional[Band] = None
    freq_mhz: int = 0
    mcs: str = ""                    # e.g. MCS0, MCS7
    standard: str = ""               # e.g. HE_SU
    bandwidth: str = ""              # e.g. BW-20, BW-80
    antennas: list = field(default_factory=list)  # e.g. ['ANT1','ANT2']

    # --- Key measurements ---
    rx_power_dbm: Optional[float] = None         # RX_POWER_DBM (injected by tester)
    per: Optional[float] = None                  # Packet Error Rate (%)
    per_limit_lo: Optional[float] = None
    per_limit_hi: Optional[float] = None

    # RSSI per chain (up to 4 antennas)
    rssi_rx1: Optional[float] = None             # RSSI_RX1
    rssi_rx2: Optional[float] = None             # RSSI_RX2
    rssi_rx3: Optional[float] = None             # RSSI_RX3
    rssi_rx4: Optional[float] = None             # RSSI_RX4

    # RX power level per chain
    rx_power_rx1: Optional[float] = None         # RX_POWER_LEVEL_DBM_RX1
    rx_power_rx2: Optional[float] = None
    rx_power_rx3: Optional[float] = None
    rx_power_rx4: Optional[float] = None

    # Cable / path loss
    cable_loss_db1: Optional[float] = None       # CABLE_LOSS_DB_RET1

    good_packets: Optional[int] = None
    total_packets: Optional[int] = None

    raw_header: str = ""

    # Sentinel: -999 means RSSI not valid (multi-antenna aggregate block)
    RSSI_INVALID = -999.0

    @property
    def rssi_valid(self) -> bool:
        """Returns False if the RSSI is the -999 sentinel value."""
        return (self.rssi_rx1 is not None and
                self.rssi_rx1 != self.RSSI_INVALID)

    @property
    def passes_per(self) -> Optional[bool]:
        if self.per is None:
            return None
        hi = self.per_limit_hi if self.per_limit_hi is not None else 10.0
        lo = self.per_limit_lo if self.per_limit_lo is not None else 0.0
        return lo <= self.per <= hi

    @property
    def antenna_label(self) -> str:
        return "".join(self.antennas) if self.antennas else "ALL"

    @property
    def label(self) -> str:
        return (f"{self.block_number}.RX {self.freq_mhz}MHz "
                f"{self.mcs} {self.bandwidth} {self.antenna_label}")


# ---------------------------------------------------------------------------
# Full parsed log
# ---------------------------------------------------------------------------

@dataclass
class ParsedLog:
    """Top-level result returned by LogParser.parse()."""
    metadata: LogMetadata = field(default_factory=LogMetadata)
    tx_blocks: list = field(default_factory=list)   # list[TxBlock]
    rx_blocks: list = field(default_factory=list)   # list[RxBlock]
    parse_warnings: list = field(default_factory=list)  # list[str]

    @property
    def tx_count(self) -> int:
        return len(self.tx_blocks)

    @property
    def rx_count(self) -> int:
        return len(self.rx_blocks)

    def tx_by_band(self, band: Band) -> list:
        return [b for b in self.tx_blocks if b.band == band]

    def rx_by_band(self, band: Band) -> list:
        return [b for b in self.rx_blocks if b.band == band]
