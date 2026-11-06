from sqlalchemy import Index

from app.extensions import db
from app.models.base import BaseModel


class FeltReport(db.Model, BaseModel):
    """A device-submitted report that records a felt earthquake experience."""

    __tablename__ = "felt_reports"
    __table_args__ = (
        db.CheckConstraint(
            "intensity IN ('MILD', 'MODERATE', 'SEVERE')",
            name="ck_felt_reports_intensity",
        ),
        db.CheckConstraint("time_ago >= 0", name="ck_felt_reports_time_ago"),
        db.CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="ck_felt_reports_latitude",
        ),
        db.CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="ck_felt_reports_longitude",
        ),
        db.CheckConstraint(
            "accuracy IS NULL OR accuracy >= 0",
            name="ck_felt_reports_accuracy",
        ),
        Index("felt_reports_device_idx", "device_id"),
        Index("felt_reports_created_at_idx", "created_at"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.Uuid,
        db.ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )
    intensity = db.Column(db.Text, nullable=False)
    time_ago = db.Column(db.Integer, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)

    device = db.relationship("Device", back_populates="felt_reports")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": str(self.device_id) if self.device_id else None,
            "intensity": self.intensity,
            "time_ago": self.time_ago,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
        }

    def __repr__(self):
        return f"<FeltReport id={self.id} intensity={self.intensity}>"
