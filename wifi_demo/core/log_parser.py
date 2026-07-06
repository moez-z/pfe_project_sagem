import re
import os
from pathlib import Path
from typing import Optional

from .models import (
    Band, BlockType,
    LogMetadata, TxBlock, RxBlock, ParsedLog,
)


# ---------------------------------------------------------------------------
# Regex patterns (compiled once at module load)
# ---------------------------------------------------------------------------

# Timestamp prefix on log lines:  [HH:MM:SS:mmm]
_RE_TIMESTAMP = re.compile(r'^\[(\d{2}:\d{2}:\d{2}:\d{3})\]\s*(.*)')

# Block header — numbered test entry:
#   8.TX_VERIFY EVM MASK POWER SPECTRUM 5500 OFDM-6 NON_HT BW-20 ANT1 ___
#   7.RX_VERIFY PER 5500 MCS0 HE_SU BW-20 ANT1 ANT2 ANT3 ANT4 ____________
_RE_BLOCK_HDR = re.compile(
    r'^(\d+)\.(TX_VERIFY|RX_VERIFY)\s+(.*?)(?:\s*_{3,}.*)?$'
)

# Summary timing lines — same pattern but ends with ":N.NNN s" — skip these
_RE_TIMING = re.compile(r':\s*\d+\.\d{3}\s*s\s*$')

# Key-value field line:
#   POWER_DBM_RMS_AVG_S1   :   21.22 dBm   ( 20.5, 23.5)
_RE_KV = re.compile(
    r'^([A-Z_0-9]+)\s*:\s*(-?[\d.]+(?:e[+-]?\d+)?)\s*(\w+)?\s*'
    r'(?:\(\s*(-?[\d.]*)\s*,\s*(-?[\d.]*)\s*\))?'
)

# BDT config line: conf_GTW_BWC_Nom_Produit : EDERSON
_RE_CONF = re.compile(r'conf_GTW_BWC_(\w+)\s*:\s*(.+)')
_RE_CONF2 = re.compile(r'\[(\d{2}:\d{2}:\d{2}:\d{3})\]\s*={3,}>\s*(.*?)\s*<={3,}')

# Serial number from filename:
#   SN_<serial>_ATR_TEST_...
_RE_SN_FILENAME = re.compile(r'SN_([A-Z0-9]+)_ATR_TEST')

_RE_POWER_RMS_AVG = re.compile(r'^POWER_(?:DBM_)?RMS_AVG_\w+$')


# ---------------------------------------------------------------------------
# LogParser
# ---------------------------------------------------------------------------

class LogParser:
    """
    Stateless parser — call LogParser.parse(path) to get a ParsedLog.
    """

    @staticmethod
    def parse(filepath: str | Path) -> ParsedLog:
        """
        Main entry point. Reads the file, splits into lines,
        extracts metadata and all TX/RX blocks.

        Parameters
        ----------
        filepath : str or Path
            Path to the .log file (ISO-8859-1 encoding).

        Returns
        -------
        ParsedLog
            Fully populated dataclass with metadata, tx_blocks, rx_blocks.
        """
        filepath = Path(filepath)
        result = ParsedLog()
        result.metadata.filename = filepath.name

        # --- Extract serial from filename ---
        m = _RE_SN_FILENAME.search(filepath.name)
        if m:
            result.metadata.serial_number = m.group(1)

        # --- Read file ---
        try:
            raw = filepath.read_text(encoding="iso-8859-1")
        except Exception as e:
            result.parse_warnings.append(f"Cannot read file: {e}")
            return result

        # Normalise line endings (CR+LF, CR-only, LF)
        lines = re.split(r'\r\n|\r|\n', raw)

        # Strip ANSI escape sequences from terminal output
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        lines = [ansi_escape.sub('', ln) for ln in lines]

        # --- Two-pass parsing ---
        LogParser._extract_metadata(lines, result.metadata)
        LogParser._extract_blocks(lines, result)

        return result

    # -----------------------------------------------------------------------
    # Pass 1 — metadata
    # -----------------------------------------------------------------------

    @staticmethod
    def _extract_metadata(lines: list[str], meta: LogMetadata) -> None:
        for line in lines:
            stripped = line.strip()

            # Station name:  [11:29:49:863] ===================> EZR-BBS30717 <===
            m = _RE_CONF2.match(stripped)
            if m and not meta.test_station:
                candidate = m.group(2).strip()
                if candidate and '=' not in candidate:
                    meta.test_station = candidate

            # BDT config fields
            m = _RE_CONF.search(stripped)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if key == 'Nom_Produit':
                    meta.product_name = val
                elif key == 'Version_Application':
                    meta.app_version = val
                elif key == 'CONFIG_TEST':
                    meta.test_config = val

            # Serial number in log body (more reliable than filename):
            #   Sn SFIN   : 254087406A1SC000R2504201252
            if 'Sn SFIN' in stripped or 'SN SFIN' in stripped:
                m2 = re.search(r':\s*([A-Z0-9]{10,})', stripped)
                if m2:
                    meta.serial_number = m2.group(1)

    # -----------------------------------------------------------------------
    # Pass 2 — block extraction
    # -----------------------------------------------------------------------

    @staticmethod
    def _extract_blocks(lines: list[str], result: ParsedLog) -> None:
        """
        Walks lines sequentially. When a block header is found,
        collects all subsequent lines until the next block header or
        end-of-section marker, then delegates to the appropriate
        block parser.
        """
        block_lines: list[str] = []
        block_header: str = ""
        block_num: int = 0
        block_type: Optional[BlockType] = None

        def _is_skipped(header: str, lines: list[str]) -> bool:
            if "[Skipped]" in header:
                return True
            return any(
                ln.strip() == "Skipped" or "[Skipped]" in ln
                for ln in lines
            )

        def flush():
            if block_type == BlockType.TX_VERIFY:
                blk = LogParser._parse_tx_block(block_num, block_header, block_lines)
                if blk:
                    result.tx_blocks.append(blk)
                elif _is_skipped(block_header, block_lines):
                    result.skipped_tx_blocks.append((block_num, block_header))
                else:
                    result.rejected_tx_blocks.append(
                        (block_num, block_header, "missing/null POWER_DBM_RMS_AVG_S1")
                    )
            elif block_type == BlockType.RX_VERIFY:
                blk = LogParser._parse_rx_block(block_num, block_header, block_lines)
                if blk:
                    result.rx_blocks.append(blk)
                elif _is_skipped(block_header, block_lines):
                    result.skipped_rx_blocks.append((block_num, block_header))
                else:
                    result.rejected_rx_blocks.append(
                        (block_num, block_header, "missing/null PER and RSSI_RX1")
                    )

        for raw_line in lines:
            stripped = raw_line.strip()

            # Remove timestamp prefix to get content
            m = _RE_TIMESTAMP.match(stripped)
            content = m.group(2).strip() if m else stripped

            # --- Detect block header ---
            hdr_m = _RE_BLOCK_HDR.match(content)
            if hdr_m and not _RE_TIMING.search(content):
                # Save previous block
                flush()
                # Start new block
                block_num  = int(hdr_m.group(1))
                block_type = BlockType(hdr_m.group(2))
                block_header = content
                block_lines = []
                continue

            # --- Accumulate lines for current block ---
            if block_type is not None:
                block_lines.append(content)

        # Flush last block
        flush()

    # -----------------------------------------------------------------------
    # TX block parser
    # -----------------------------------------------------------------------


    @staticmethod
    def _parse_tx_block(num: int, header: str, lines: list[str]) -> Optional[TxBlock]:
        # --- Detect explicit "Skipped" marker ---
        for line in lines:
            s = line.strip()
            if s == "Skipped" or "[Skipped]" in s:
                return None  # caller records as skipped block

        blk = TxBlock(block_number=num, raw_header=header)

        # --- Parse header tokens ---
        tokens = header.split()
        for tok in tokens:
            if re.match(r'^\d{4,5}$', tok):
                blk.freq_mhz = int(tok)
            elif tok.startswith('BW-'):
                blk.bandwidth = tok
            elif tok.startswith('ANT'):
                blk.antenna = tok
            elif tok in ('NON_HT', 'HE_SU', 'HE_MU', 'HE_TB'):
                blk.standard = tok
            elif re.match(r'^(MCS\d+|OFDM-\d+|DSSS-\d+|CCK-\d+)$', tok):
                blk.modulation = tok

        if blk.freq_mhz:
            try:
                blk.band = Band.from_freq(blk.freq_mhz)
            except ValueError:
                pass

        # --- Parse fields ---
        #
        # power_candidates holds every *RMS*AVG* field found in this block:
        #   (value, lo, hi, priority)
        #   priority 0 → POWER_RMS_AVG_VSA1     (preferred when no limits)
        #   priority 1 → POWER_DBM_RMS_AVG_S1
        #   priority 2 → any other *RMS*AVG* variant (forward-compat)
        #
        tx_power_seen = 0
        power_candidates: list[tuple[float, Optional[float], Optional[float], int]] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            m = _RE_KV.match(line)
            if not m:
                continue

            key   = m.group(1)
            value = LogParser._safe_float(m.group(2))
            lo    = LogParser._safe_float(m.group(4)) if m.group(4) else None
            hi    = LogParser._safe_float(m.group(5)) if m.group(5) else None

            if value is None:
                continue

            if key == 'TX_POWER_DBM':
                tx_power_seen += 1
                if tx_power_seen == 1:          # first occurrence = target
                    blk.tx_target_dbm = value

            elif key == 'POWER_RMS_AVG_VSA1':
                power_candidates.append((value, lo, hi, 0))

            elif key == 'POWER_DBM_RMS_AVG_S1':
                power_candidates.append((value, lo, hi, 1))

            elif _RE_POWER_RMS_AVG.match(key) and 'PRE' not in key:
                # Catch future field-name variants automatically.
                # 'PRE' fields (POWER_PRE_AVG_VSA1) are pre-correction snapshots
                # — never the true measured power — so we skip them explicitly.
                power_candidates.append((value, lo, hi, 2))

            elif key == 'POWER_DBM_RMS_MAX_S1':
                blk.power_rms_max = value

            elif key == 'POWER_DBM_RMS_MIN_S1':
                blk.power_rms_min = value

            elif key == 'POWER_PEAK_AVG_VSA1':
                blk.power_peak_avg = value

            elif key == 'FREQ_ERROR_AVG':
                blk.freq_error_avg_ppm = value

        # --- Select the best power candidate ---
        if power_candidates:
            # Prefer any candidate that carries hard limits (lo or hi present)
            with_limits = [
                c for c in power_candidates if c[1] is not None or c[2] is not None
            ]
            pool = with_limits if with_limits else power_candidates
            # Among the chosen pool, pick the field with the lowest priority number
            best = min(pool, key=lambda c: c[3])
            blk.tx_measured_dbm = best[0]
            blk.tx_limit_lo     = best[1]
            blk.tx_limit_hi     = best[2]

        # Only return block if we got the key measurement
        if blk.tx_measured_dbm is None:
            return None
        return blk

    # -----------------------------------------------------------------------
    # RX block parser
    # -----------------------------------------------------------------------

    @staticmethod
    def _parse_rx_block(num: int, header: str, lines: list[str]) -> Optional[RxBlock]:
        # --- Detect explicit "Skipped" marker from the test station ---
        for line in lines:
            s = line.strip()
            if s == "Skipped" or "[Skipped]" in s:
                return None  # caller records this as a skipped block, not null data

        blk = RxBlock(block_number=num, raw_header=header)

        # --- Parse header tokens ---
        tokens = header.split()
        antennas = []
        for tok in tokens:
            if re.match(r'^\d{4,5}$', tok):
                blk.freq_mhz = int(tok)
            elif tok.startswith('BW-'):
                blk.bandwidth = tok
            elif tok.startswith('ANT'):
                antennas.append(tok)
            elif tok in ('NON_HT', 'HE_SU', 'HE_MU', 'HE_TB'):
                blk.standard = tok
            elif re.match(r'^MCS\d+$', tok):
                blk.mcs = tok
        blk.antennas = antennas

        if blk.freq_mhz:
            try:
                blk.band = Band.from_freq(blk.freq_mhz)
            except ValueError:
                pass

        # --- Parse fields ---
        for line in lines:
            line = line.strip()
            if not line:
                continue

            m = _RE_KV.match(line)
            if not m:
                continue

            key   = m.group(1)
            value = LogParser._safe_float(m.group(2))
            lo    = LogParser._safe_float(m.group(4)) if m.group(4) else None
            hi    = LogParser._safe_float(m.group(5)) if m.group(5) else None

            if value is None:
                continue

            if key == 'RX_POWER_DBM':
                blk.rx_power_dbm = value

            elif key == 'PER':
                blk.per = value
                blk.per_limit_lo = lo
                blk.per_limit_hi = hi

            elif key == 'RSSI_RX1':
                blk.rssi_rx1 = value
            elif key == 'RSSI_RX2':
                blk.rssi_rx2 = value
            elif key == 'RSSI_RX3':
                blk.rssi_rx3 = value
            elif key == 'RSSI_RX4':
                blk.rssi_rx4 = value

            elif key == 'RX_POWER_LEVEL_DBM_RX1':
                blk.rx_power_rx1 = value
            elif key == 'RX_POWER_LEVEL_DBM_RX2':
                blk.rx_power_rx2 = value
            elif key == 'RX_POWER_LEVEL_DBM_RX3':
                blk.rx_power_rx3 = value
            elif key == 'RX_POWER_LEVEL_DBM_RX4':
                blk.rx_power_rx4 = value

            elif key == 'CABLE_LOSS_DB_RET1':
                blk.cable_loss_db1 = value

            elif key == 'GOOD_PACKETS':
                blk.good_packets = int(value)
            elif key == 'TOTAL_PACKETS':
                blk.total_packets = int(value)

        # Only return block if it has at least PER or RSSI
        if blk.per is None and blk.rssi_rx1 is None:
            return None
        return blk

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _safe_float(s: Optional[str]) -> Optional[float]:
        """Convert string to float, return None on failure."""
        if s is None:
            return None
        try:
            return float(s)
        except (ValueError, TypeError):
            return None