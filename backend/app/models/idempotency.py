import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from app.db.database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    response_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)