
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text,
)
from sqlalchemy.orm import relationship

from db.config import Base


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    matricule      = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    full_name     = Column(String(128), default="")
    role          = Column(String(32), default="operator")   # admin / operator
    created_at    = Column(DateTime, default=datetime.utcnow)
    last_login    = Column(DateTime, nullable=True)

    sessions = relationship("CalibrationSession", back_populates="user",
                            cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.matricule} ({self.role})>"
    

class Post(Base):
    __tablename__ = "posts"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    number     = Column(Integer, nullable=False, unique=True)
    name       = Column(String(32),  nullable=False)
    ip_address = Column(String(45),  nullable=True)
    is_active  = Column(Boolean,     default=True)
    created_at = Column(DateTime,    default=datetime.utcnow)

    sessions   = relationship("CalibrationSession", back_populates="post")

    def __repr__(self):
        return f"<Post {self.number} – {self.name}>"


# ── Calibration sessions ──────────────────────────────────────────────────────

class CalibrationSession(Base):
    __tablename__ = "calibration_sessions"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Device info
    dut_serial      = Column(String(64),  default="")
    origin_serial   = Column(String(64),  default="")
    product_name    = Column(String(64),  default="")
    post_id         = Column(Integer, ForeignKey("posts.id"), nullable=True)  # ← ADD THIS
    dut_filename    = Column(String(256), default="")
    origin_filename = Column(String(256), default="")
    tolerance_dbm   = Column(Float,       default=0.5)

    # Summary results
    overall_pass    = Column(Boolean,  default=False)
    tx_total        = Column(Integer,  default=0)
    tx_pass         = Column(Integer,  default=0)
    tx_fail         = Column(Integer,  default=0)
    tx_corrections  = Column(Integer,  default=0)
    rx_total        = Column(Integer,  default=0)
    rx_pass         = Column(Integer,  default=0)
    rx_fail         = Column(Integer,  default=0)
    avg_delta_dbm   = Column(Float,    nullable=True)
    max_delta_dbm   = Column(Float,    nullable=True)

    created_at      = Column(DateTime, default=datetime.utcnow, index=True)
    notes           = Column(Text,     default="")

    # Relationships
    user      = relationship("User", back_populates="sessions")
    post     = relationship("Post", back_populates="sessions")              # ← ADD THIS
    tx_blocks = relationship("TxResult", back_populates="session",
                             cascade="all, delete-orphan")
    rx_blocks = relationship("RxResult", back_populates="session",
                             cascade="all, delete-orphan")

    def __repr__(self):
        status = "PASS" if self.overall_pass else "FAIL"
        return f"<Session #{self.id} {self.dut_serial} {status}>"


# ── TX results ────────────────────────────────────────────────────────────────

class TxResult(Base):
    __tablename__ = "tx_results"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    session_id     = Column(Integer, ForeignKey("calibration_sessions.id"),
                            nullable=False, index=True)

    band           = Column(String(16),  default="")
    block_number   = Column(Integer,     default=0)
    freq_mhz       = Column(Integer,     default=0)
    modulation     = Column(String(32),  default="")
    bandwidth      = Column(String(16),  default="")
    antenna        = Column(String(8),   default="")

    origin_dbm     = Column(Float, nullable=True)
    dut_dbm        = Column(Float, nullable=True)
    delta_dbm      = Column(Float, nullable=True)
    correction_dbm = Column(Float, nullable=True)
    tx_target_dbm  = Column(Float, nullable=True)
    limit_lo       = Column(Float, nullable=True)
    limit_hi       = Column(Float, nullable=True)
    status         = Column(String(32),  default="")

    session = relationship("CalibrationSession", back_populates="tx_blocks")


# ── RX results ────────────────────────────────────────────────────────────────

class RxResult(Base):
    __tablename__ = "rx_results"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    session_id     = Column(Integer, ForeignKey("calibration_sessions.id"),
                            nullable=False, index=True)

    band           = Column(String(16),  default="")
    block_number   = Column(Integer,     default=0)
    freq_mhz       = Column(Integer,     default=0)
    mcs            = Column(String(16),  default="")
    bandwidth      = Column(String(16),  default="")
    antenna_label  = Column(String(32),  default="")

    origin_rssi    = Column(Float, nullable=True)
    dut_rssi       = Column(Float, nullable=True)
    rssi_delta     = Column(Float, nullable=True)
    origin_per     = Column(Float, nullable=True)
    dut_per        = Column(Float, nullable=True)
    status         = Column(String(32),  default="")

    session = relationship("CalibrationSession", back_populates="rx_blocks")


