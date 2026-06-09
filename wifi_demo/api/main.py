from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from db.models import User
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.config import get_db, init_db
from db.repository import UserRepo, SessionRepo, PostRepo
from schemas import (
    LoginRequest, LoginResponse,
    SessionSummary, SessionDetail,
    StatsResponse, PostOut
)

app = FastAPI(title="WiFi Calibration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = UserRepo.verify(db, body.matricule, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")
    return LoginResponse(
        id=user.id,
        matricule=user.matricule,
        full_name=user.full_name,
        role=user.role,
    )

# ── Users ─────────────────────────────────────────────────────────────────────

@app.patch("/users/{user_id}/name")
def update_name(user_id: int, body: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.full_name = body["full_name"]
    db.commit()
    return {"ok": True}

@app.patch("/users/{user_id}/password")
def update_password(user_id: int, body: dict, db: Session = Depends(get_db)):
    import bcrypt
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt.checkpw(body["old_password"].encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Wrong password")
    user.password_hash = bcrypt.hashpw(
        body["new_password"].encode(), bcrypt.gensalt()
    ).decode()
    db.commit()
    return {"ok": True}

# ── Sessions ──────────────────────────────────────────────────────────────────

@app.get("/sessions", response_model=list[SessionSummary])
def list_sessions(limit: int = 100, user_id: int = None,
                  db: Session = Depends(get_db)):
    sessions = SessionRepo.list_recent(db, limit=limit, user_id=user_id)
    return [SessionSummary.model_validate(s) for s in sessions]

@app.post("/sessions", status_code=201)
def create_session(body: dict, db: Session = Depends(get_db)):
    from db.models import CalibrationSession, TxResult, RxResult
    try:
        session = CalibrationSession(
            user_id       = body.get("user_id"),
            post_id       = body.get("post_id"),
            dut_serial    = body.get("dut_serial", ""),
            origin_serial = body.get("origin_serial", ""),
            product_name  = body.get("product_name", ""),
            tolerance_dbm = body.get("tolerance_dbm", 0.5),
            overall_pass  = body.get("overall_pass", False),
            tx_total      = body.get("tx_total", 0),
            tx_pass       = body.get("tx_pass", 0),
            tx_fail       = body.get("tx_fail", 0),
            tx_corrections= body.get("tx_corrections", 0),
            rx_total      = body.get("rx_total", 0),
            rx_pass       = body.get("rx_pass", 0),
            rx_fail       = body.get("rx_fail", 0),
            avg_delta_dbm = body.get("avg_delta_dbm"),
            max_delta_dbm = body.get("max_delta_dbm"),
        )
        db.add(session)
        db.flush()

        for r in body.get("tx_results", []):
            db.add(TxResult(session_id=session.id, **r))

        for r in body.get("rx_results", []):
            db.add(RxResult(session_id=session.id, **r))

        db.commit()
        return {"id": session.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)):
    s = SessionRepo.get_by_id(db, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    tx = SessionRepo.get_tx_blocks(db, session_id)
    rx = SessionRepo.get_rx_blocks(db, session_id)
    return SessionDetail.model_validate(
        {**s.__dict__, "tx_blocks": tx, "rx_blocks": rx}
    )

@app.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    SessionRepo.delete(db, session_id)
    return {"deleted": session_id}

# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/stats/summary", response_model=StatsResponse)
def stats_summary(db: Session = Depends(get_db)):
    return SessionRepo.stats_summary(db)

@app.get("/stats/deltas")
def stats_deltas(limit: int = 30, db: Session = Depends(get_db)):
    return SessionRepo.recent_deltas(db, limit=limit)

# ── Posts ─────────────────────────────────────────────────────────────────────

@app.get("/posts", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    return PostRepo.list_all(db)

@app.get("/debug/users")
def debug_users(db: Session = Depends(get_db)):
    from db.models import User
    users = db.query(User).all()
    return [{"id": u.id, "matricule": u.matricule, "role": u.role, "hash_prefix": u.password_hash[:20]} for u in users]

@app.post("/posts", status_code=201)
def create_post(body: dict, db: Session = Depends(get_db)):
    from db.models import Post
    try:
        post = Post(
            number=body.get("number"),
            name=body.get("name"),
            ip_address=body.get("ip_address"),
            is_active=body.get("is_active", True),
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return {"id": post.id, "number": post.number, "name": post.name}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))