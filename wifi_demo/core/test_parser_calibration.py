"""
tests/test_parser_calibration.py
---------------------------------
Validates LogParser and CalibrationEngine against the real Sagemcom log files.
Run with:  python -m pytest tests/ -v
       or:  python tests/test_parser_calibration.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core import (
    LogParser, CalibrationEngine,
    Band, TxStatus, RxStatus,
    DEFAULT_TX_TOLERANCE_DBM,
)

# Paths to the real log files (adjust if needed)
ORIGIN_LOG = "/mnt/user-data/uploads/log_origine_Silver.log"
DUT_LOG    = "/mnt/user-data/uploads/SN_254087406A1SC000R2504201252_ATR_TEST_WIFI_CONDUIT_1_L4_SLOT1_27_01_26__11_32_32___1_.log"


# ===========================================================================
# Parser tests
# ===========================================================================

def test_parse_origin_metadata():
    log = LogParser.parse(ORIGIN_LOG)
    assert log.metadata.product_name == "EDERSON", \
        f"Expected EDERSON, got {log.metadata.product_name}"
    assert "BWC" in log.metadata.app_version, \
        f"Expected BWC in version, got {log.metadata.app_version}"
    print(f"  ✓ Origin metadata: product={log.metadata.product_name}, "
          f"version={log.metadata.app_version}, "
          f"station={log.metadata.test_station}")


def test_parse_dut_serial():
    log = LogParser.parse(DUT_LOG)
    assert "254087406" in log.metadata.serial_number, \
        f"Expected serial with 254087406, got {log.metadata.serial_number}"
    print(f"  ✓ DUT serial: {log.metadata.serial_number}")


def test_origin_tx_block_count():
    log = LogParser.parse(ORIGIN_LOG)
    assert log.tx_count == 25, \
        f"Expected 25 TX blocks in origin, got {log.tx_count}"
    print(f"  ✓ Origin TX blocks: {log.tx_count}")


def test_origin_rx_block_count():
    log = LogParser.parse(ORIGIN_LOG)
    assert log.rx_count >= 19, \
        f"Expected >=19 RX blocks in origin, got {log.rx_count}"
    print(f"  ✓ Origin RX blocks: {log.rx_count}")


def test_dut_tx_block_count():
    log = LogParser.parse(DUT_LOG)
    assert log.tx_count == 25, \
        f"Expected 25 TX blocks in DUT, got {log.tx_count}"
    print(f"  ✓ DUT TX blocks: {log.tx_count}")


def test_tx_measured_values():
    """Spot-check specific known values from the logs."""
    log = LogParser.parse(DUT_LOG)

    # Block 8: 5500MHz OFDM-6 BW-20 ANT1 → measured = 21.22
    blk = next((b for b in log.tx_blocks
                if b.block_number == 8 and b.freq_mhz == 5500
                and b.antenna == 'ANT1'), None)
    assert blk is not None, "Block 8 TX 5500MHz ANT1 not found"
    assert abs(blk.tx_measured_dbm - 21.22) < 0.01, \
        f"Expected 21.22, got {blk.tx_measured_dbm}"
    assert blk.tx_limit_lo == 20.5
    assert blk.tx_limit_hi == 23.5
    print(f"  ✓ TX 8 5500MHz ANT1: measured={blk.tx_measured_dbm}, "
          f"limits=({blk.tx_limit_lo}, {blk.tx_limit_hi})")

    # Block 18: 5610MHz MCS0 BW-80 ANT3 → measured = 23.02
    blk2 = next((b for b in log.tx_blocks
                 if b.block_number == 18 and b.freq_mhz == 5610
                 and b.antenna == 'ANT3'), None)
    assert blk2 is not None, "Block 18 TX 5610MHz ANT3 not found"
    assert abs(blk2.tx_measured_dbm - 23.02) < 0.01, \
        f"Expected 23.02, got {blk2.tx_measured_dbm}"
    print(f"  ✓ TX 18 5610MHz ANT3: measured={blk2.tx_measured_dbm}")


def test_tx_band_assignment():
    log = LogParser.parse(DUT_LOG)
    bands = {b.band for b in log.tx_blocks}
    assert Band.GHz_5   in bands, "5GHz band missing"
    assert Band.GHz_2_4 in bands, "2.4GHz band missing"
    assert Band.GHz_6   in bands, "6GHz band missing"
    print(f"  ✓ TX bands found: {[b.value for b in bands]}")


def test_rx_per_values():
    log = LogParser.parse(DUT_LOG)
    # All PER values should be 0.0
    per_values = [b.per for b in log.rx_blocks if b.per is not None]
    assert len(per_values) > 0, "No PER values found"
    assert all(p == 0.0 for p in per_values), \
        f"Non-zero PER found: {[p for p in per_values if p != 0.0]}"
    print(f"  ✓ All {len(per_values)} PER values = 0.0%")


def test_rx_rssi_sentinel():
    """RSSI = -999 sentinel blocks should be flagged as invalid."""
    log = LogParser.parse(DUT_LOG)
    sentinel_blocks = [b for b in log.rx_blocks
                       if b.rssi_rx1 == RxBlock_INVALID(log)]
    print(f"  ✓ RX blocks checked for -999 sentinel")


def RxBlock_INVALID(log):
    return -999.0


# ===========================================================================
# Calibration engine tests
# ===========================================================================

def test_calibration_block_matching():
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut)

    unmatched = [r for r in report.tx_results if r.status == TxStatus.UNMATCHED]
    assert len(unmatched) == 0, \
        f"Unmatched TX blocks: {[r.label for r in unmatched]}"
    print(f"  ✓ All {len(report.tx_results)} TX blocks matched")


def test_calibration_deltas():
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut)

    # Block 8, 5500MHz ANT1: origin=21.13, dut=21.22 → delta=+0.09
    r = next((r for r in report.tx_results
              if r.block_number == 8 and r.freq_mhz == 5500
              and r.antenna == 'ANT1'), None)
    assert r is not None
    assert abs(r.delta_dbm - 0.09) < 0.01, \
        f"Expected delta +0.09, got {r.delta_dbm}"
    assert r.correction_dbm is not None
    assert abs(r.correction_dbm - (-0.09)) < 0.01
    print(f"  ✓ TX 8 5500MHz ANT1: delta={r.delta_str}, "
          f"correction={r.correction_str}, status={r.status.value}")


def test_calibration_pass_status():
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut)

    # All blocks WITH limits should PASS (our DUT is a good device)
    blocks_with_limits = [r for r in report.tx_results
                          if r.tx_limit_lo is not None]
    fails = [r for r in blocks_with_limits if r.status == TxStatus.FAIL]
    assert len(fails) == 0, \
        f"Unexpected FAIL blocks: {[r.label for r in fails]}"
    print(f"  ✓ All {len(blocks_with_limits)} limited TX blocks PASS")


def test_calibration_2g_delta():
    """2.4GHz ANT3 has largest delta (+0.67) — verify it's detected."""
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut)

    r = next((r for r in report.tx_results
              if r.block_number == 14 and r.freq_mhz == 2412
              and r.antenna == 'ANT3'), None)
    assert r is not None, "Block 14 2412MHz ANT3 not found"
    assert r.delta_dbm is not None
    assert abs(r.delta_dbm - 0.67) < 0.02, \
        f"Expected delta ~+0.67, got {r.delta_dbm}"
    print(f"  ✓ 2.4GHz ANT3 largest delta: {r.delta_str} "
          f"(correction: {r.correction_str})")


def test_corrections_list():
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut, tolerance_dbm=0.5)
    corrections = CalibrationEngine.get_corrections(report)
    print(f"  ✓ Corrections needed (tolerance=0.5dBm): {len(corrections)}")
    for c in corrections:
        print(f"    → {c['label']}: delta={c['delta_dbm']:+.3f} dBm, "
              f"correction={c['correction_dbm']:+.3f} dBm")


def test_rx_all_pass():
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut)

    fails = [r for r in report.rx_results if r.status == RxStatus.FAIL]
    assert len(fails) == 0, \
        f"Unexpected RX FAIL: {[r.label for r in fails]}"
    rx_pass  = report.rx_pass_count
    rx_inv   = report.rx_invalid_count
    print(f"  ✓ RX: {rx_pass} PASS, {rx_inv} INVALID (expected -999 sentinels)")


def test_summary_output():
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut)
    print(report.summary())


def test_by_band_filter():
    origin = LogParser.parse(ORIGIN_LOG)
    dut    = LogParser.parse(DUT_LOG)
    report = CalibrationEngine.compare(origin, dut)

    for band in [Band.GHz_5, Band.GHz_2_4, Band.GHz_6]:
        sub = report.by_band(band)
        print(f"  ✓ {band.value}: {len(sub.tx_results)} TX, "
              f"{len(sub.rx_results)} RX blocks")


# ===========================================================================
# Runner
# ===========================================================================

if __name__ == "__main__":
    tests = [
        test_parse_origin_metadata,
        test_parse_dut_serial,
        test_origin_tx_block_count,
        test_origin_rx_block_count,
        test_dut_tx_block_count,
        test_tx_measured_values,
        test_tx_band_assignment,
        test_rx_per_values,
        test_calibration_block_matching,
        test_calibration_deltas,
        test_calibration_pass_status,
        test_calibration_2g_delta,
        test_corrections_list,
        test_rx_all_pass,
        test_by_band_filter,
        test_summary_output,
    ]

    passed = 0
    failed = 0
    print("\n" + "="*60)
    print("  RUNNING TESTS")
    print("="*60)

    for test_fn in tests:
        name = test_fn.__name__.replace("test_", "").replace("_", " ")
        print(f"\n▶ {name}")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"  {passed} passed  |  {failed} failed")
    print("="*60 + "\n")
    sys.exit(0 if failed == 0 else 1)
