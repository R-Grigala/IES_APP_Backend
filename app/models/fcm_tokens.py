from app.extensions import db
from app.models.base import BaseModel


class FcmToken(db.Model, BaseModel):
    __tablename__ = "fcm_tokens"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.Uuid,
        db.ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    fcm_token = db.Column(db.Text, unique=True, nullable=False)
    notifications_enabled = db.Column(
        db.Boolean,
        nullable=False,
        server_default=db.true(),
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    device = db.relationship("Device", back_populates="fcm_tokens")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": str(self.device_id),
            "fcm_token": self.fcm_token,
            "notifications_enabled": self.notifications_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

