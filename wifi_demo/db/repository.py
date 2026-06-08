import bcrypt
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session as DbSession
from db.models import Post, User, CalibrationSession, TxResult, RxResult


# ── Password hashing ──────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    except Exception:
        return False


# ── User repository ───────────────────────────────────────────────────────────

class UserRepo:

    @staticmethod
    def create(db: DbSession, matricule: str, password: str,
               full_name: str = "", role: str = "operator") -> User:
        if db.query(User).filter_by(matricule=matricule).first():
            raise ValueError(f"matricule '{matricule}' already exists.")
        user = User(
            matricule=matricule,
            password_hash=_hash_password(password),
            full_name=full_name,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def verify(db: DbSession, matricule: str, password: str) -> Optional[User]:
        user = db.query(User).filter_by(matricule=matricule).first()
        if user and _verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            db.commit()
            return user
        return None

    @staticmethod
    def list_all(db: DbSession) -> list[User]:
        return db.query(User).order_by(User.matricule).all()

    @staticmethod
    def ensure_default_admin(db: DbSession):
        if db.query(User).count() == 0:
            UserRepo.create(db, "admin", "admin123",
                            full_name="Administrator", role="admin")
            print("[db] Created default admin user (admin / admin123)")


# ── Post repository ───────────────────────────────────────────────────────────

class PostRepo:

    @staticmethod
    def ensure_defaults(db: DbSession):
        if db.query(Post).count() == 0:
            for i in range(1, 11):
                db.add(Post(number=i, name=f"Caisson {i}"))
            db.commit()
            print("[db] Created 10 default posts (Caisson 1–10)")

    @staticmethod
    def get_by_number(db: DbSession, number: int):
        return db.query(Post).filter_by(number=number).first()

    @staticmethod
    def get_by_id(db: DbSession, post_id: int):
        return db.query(Post).filter_by(id=post_id).first()

    @staticmethod
    def list_active(db: DbSession):
        return db.query(Post).filter_by(is_active=True).order_by(Post.number).all()

    @staticmethod
    def list_all(db: DbSession):
        return db.query(Post).order_by(Post.number).all()

    @staticmethod
    def update(db: DbSession, post_id: int,
               name: str = None, ip_address: str = None,
               is_active: bool = None):
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            raise ValueError(f"Post id={post_id} not found")
        if name       is not None: post.name       = name
        if ip_address is not None: post.ip_address = ip_address
        if is_active  is not None: post.is_active  = is_active
        db.commit()
        db.refresh(post)
        return post


# ── Session repository ────────────────────────────────────────────────────────

class SessionRepo:

    @staticmethod
    def save(db: DbSession, report, user_id: Optional[int] = None,
             post_id: Optional[int] = None) -> int:
        from db.config import SessionLocal
        fresh_db = SessionLocal()
        try:
            session = CalibrationSession(
                user_id         = user_id,
                post_id         = post_id,
                dut_serial      = report.dut_serial,
                origin_serial   = report.origin_serial,
                product_name    = report.product_name,
                dut_filename    = report.dut_filename,
                origin_filename = report.origin_filename,
                tolerance_dbm   = report.tolerance_dbm,
                overall_pass    = report.overall_pass,
                tx_total        = len(report.tx_results),
                tx_pass         = report.tx_pass_count,
                tx_fail         = report.tx_fail_count,
                tx_corrections  = report.tx_needs_correction_count,
                rx_total        = len(report.rx_results),
                rx_pass         = report.rx_pass_count,
                rx_fail         = report.rx_fail_count,
                avg_delta_dbm   = report.tx_avg_delta,
                max_delta_dbm   = report.tx_max_delta,
            )
            fresh_db.add(session)
            fresh_db.flush()

            for r in report.tx_results:
                fresh_db.add(TxResult(
                    session_id     = session.id,
                    band           = r.band.value if r.band else "",
                    block_number   = r.block_number,
                    freq_mhz       = r.freq_mhz,
                    modulation     = r.modulation,
                    bandwidth      = r.bandwidth,
                    antenna        = r.antenna,
                    origin_dbm     = r.origin_measured_dbm,
                    dut_dbm        = r.dut_measured_dbm,
                    delta_dbm      = r.delta_dbm,
                    correction_dbm = r.correction_dbm,
                    tx_target_dbm  = r.tx_target_dbm,
                    limit_lo       = r.tx_limit_lo,
                    limit_hi       = r.tx_limit_hi,
                    status         = r.status.value,
                ))

            for r in report.rx_results:
                fresh_db.add(RxResult(
                    session_id    = session.id,
                    band          = r.band.value if r.band else "",
                    block_number  = r.block_number,
                    freq_mhz      = r.freq_mhz,
                    mcs           = r.mcs,
                    bandwidth     = r.bandwidth,
                    antenna_label = r.antenna_label,
                    origin_rssi   = r.origin_rssi,
                    dut_rssi      = r.dut_rssi,
                    rssi_delta    = r.rssi_delta,
                    origin_per    = r.origin_per,
                    dut_per       = r.dut_per,
                    status        = r.status.value,
                ))

            fresh_db.commit()
            print(f"[db] saved session id={session.id}, "
                  f"user_id={user_id}, post_id={post_id}")
            return session.id

        except Exception as e:
            fresh_db.rollback()
            print(f"[db] SessionRepo.save failed: {e!r}")
            raise
        finally:
            fresh_db.close()

    @staticmethod
    def list_recent(db: DbSession, limit: int = 100,
                    user_id: Optional[int] = None) -> list[CalibrationSession]:
        q = db.query(CalibrationSession)
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        return q.order_by(CalibrationSession.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_by_id(db: DbSession, session_id: int) -> Optional[CalibrationSession]:
        return db.query(CalibrationSession).filter_by(id=session_id).first()

    @staticmethod
    def get_tx_blocks(db: DbSession, session_id: int) -> list[TxResult]:
        return (db.query(TxResult)
                .filter_by(session_id=session_id)
                .order_by(TxResult.band, TxResult.freq_mhz, TxResult.block_number)
                .all())

    @staticmethod
    def get_rx_blocks(db: DbSession, session_id: int) -> list[RxResult]:
        return (db.query(RxResult)
                .filter_by(session_id=session_id)
                .order_by(RxResult.band, RxResult.freq_mhz, RxResult.block_number)
                .all())

    @staticmethod
    def delete(db: DbSession, session_id: int):
        s = db.query(CalibrationSession).filter_by(id=session_id).first()
        if s:
            db.delete(s)
            db.commit()

    @staticmethod
    def stats_summary(db: DbSession) -> dict:
        from sqlalchemy import func
        total  = db.query(func.count(CalibrationSession.id)).scalar() or 0
        passed = db.query(func.count(CalibrationSession.id))\
                   .filter_by(overall_pass=True).scalar() or 0
        failed = total - passed
        avg_delta = db.query(func.avg(CalibrationSession.avg_delta_dbm)).scalar()
        max_delta = db.query(func.max(CalibrationSession.max_delta_dbm)).scalar()

        band_stats = {}
        for band in ["5 GHz", "2.4 GHz", "6 GHz"]:
            total_b = db.query(func.count(TxResult.id))\
                        .filter_by(band=band).scalar() or 0
            pass_b  = db.query(func.count(TxResult.id))\
                        .filter(TxResult.band == band,
                                TxResult.status == "PASS").scalar() or 0
            band_stats[band] = {
                "total": total_b,
                "pass":  pass_b,
                "rate":  round(pass_b / total_b * 100, 1) if total_b else 0,
            }

        return {
            "total_sessions":  total,
            "passed_sessions": passed,
            "failed_sessions": failed,
            "pass_rate":       round(passed / total * 100, 1) if total else 0,
            "avg_delta_dbm":   round(avg_delta, 3) if avg_delta else None,
            "max_delta_dbm":   round(max_delta, 3) if max_delta else None,
            "band_stats":      band_stats,
        }

    @staticmethod
    def recent_deltas(db: DbSession, limit: int = 30) -> list[dict]:
        rows = (db.query(
                    CalibrationSession.id,
                    CalibrationSession.created_at,
                    CalibrationSession.avg_delta_dbm,
                    CalibrationSession.max_delta_dbm,
                    CalibrationSession.overall_pass,
                    CalibrationSession.dut_serial,
                )
                .order_by(CalibrationSession.created_at.desc())
                .limit(limit)
                .all())
        return [
            {
                "id":           r.id,
                "date":         r.created_at.strftime("%d/%m %H:%M"),
                "avg_delta":    r.avg_delta_dbm,
                "max_delta":    r.max_delta_dbm,
                "overall_pass": r.overall_pass,
                "dut_serial":   r.dut_serial,
            }
            for r in reversed(rows)
        ]