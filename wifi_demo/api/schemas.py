from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    matricule: str
    password: str

class LoginResponse(BaseModel):
    id: int
    matricule: str
    full_name: str
    role: str


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            int
    dut_serial:    str
    product_name:  str
    overall_pass:  bool
    tx_total:      int
    tx_pass:       int
    tx_fail:       int
    rx_total:      int
    rx_pass:       int
    rx_fail:       int
    avg_delta_dbm: Optional[float]
    max_delta_dbm: Optional[float]
    created_at:    datetime


class TxBlock(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    band: str; freq_mhz: int; modulation: str
    bandwidth: str; antenna: str
    origin_dbm: Optional[float]; dut_dbm: Optional[float]
    delta_dbm: Optional[float]; correction_dbm: Optional[float]
    status: str

class RxBlock(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    band: str; freq_mhz: int; mcs: str
    bandwidth: str; antenna_label: str
    origin_rssi: Optional[float]; dut_rssi: Optional[float]
    rssi_delta: Optional[float]; status: str

class SessionDetail(SessionSummary):
    tx_blocks: list[TxBlock] = []
    rx_blocks: list[RxBlock] = []


class BandStat(BaseModel):
    total: int; pass_: int; rate: float
    class Config:
        populate_by_name = True

class StatsResponse(BaseModel):
    total_sessions:  int
    passed_sessions: int
    failed_sessions: int
    pass_rate:       float
    avg_delta_dbm:   Optional[float]
    max_delta_dbm:   Optional[float]
    band_stats:      dict


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; number: int; name: str
    ip_address: Optional[str]; is_active: bool