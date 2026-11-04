from app.extensions import db
from app.models.base import BaseModel


class LocationSettings(db.Model, BaseModel):
    """Location sharing state and the latest location for one device."""

    __tablename__ = "location_settings"

    device_id = db.Column(
        db.Uuid,
        db.ForeignKey("devices.device_id", ondelete="CASCADE"),
        primary_key=True,
    )
    location_sharing_enabled = db.Column(
        db.Boolean,
        nullable=False,
        server_default=db.false(),
    )
    location_sharing_updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )
    last_latitude = db.Column(db.Float, nullable=True)
    last_longitude = db.Column(db.Float, nullable=True)
    last_accuracy = db.Column(db.Float, nullable=True)
    last_location_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_location_updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    device = db.relationship("Device", back_populates="location_settings")

    def __repr__(self):
        return (
            f"<LocationSettings device_id={self.device_id} "
            f"enabled={self.location_sharing_enabled}>"
        )
