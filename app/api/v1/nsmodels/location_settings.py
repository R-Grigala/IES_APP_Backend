from flask_restx import fields
from app.extensions import api

location_settings_ns = api.namespace(
    "Location Settings",
    description=(
        "Location sharing and last known location for already registered devices. "
        "This namespace does not register devices."
    ),
    path="/api/v1",
)

location_sharing_parser = location_settings_ns.parser()
location_sharing_parser.add_argument(
    "location_sharing_enabled",
    type=bool,
    required=True,
    location="json",
    help="Whether this device may submit new location fixes.",
)

location_parser = location_settings_ns.parser()
location_parser.add_argument(
    "latitude",
    type=float,
    required=True,
    location="json",
    help="Latitude in decimal degrees (-90 to 90).",
)
location_parser.add_argument(
    "longitude",
    type=float,
    required=True,
    location="json",
    help="Longitude in decimal degrees (-180 to 180).",
)
location_parser.add_argument(
    "accuracy",
    type=float,
    required=False,
    location="json",
    help="Optional location accuracy in meters; must be non-negative.",
)
location_parser.add_argument(
    "recorded_at",
    type=str,
    required=False,
    location="json",
    help="Optional ISO 8601 timestamp with a timezone; defaults to current UTC time.",
)

location_settings_error_model = location_settings_ns.model(
    "LocationSettingsError",
    {
        "message": fields.String,
    },
)

location_response_model = location_settings_ns.model(
    "DeviceLocation",
    {
        "device_id": fields.String(required=True),
        "location_sharing_enabled": fields.Boolean(required=True),
        "latitude": fields.Float(description="Last known latitude, or null."),
        "longitude": fields.Float(description="Last known longitude, or null."),
        "accuracy": fields.Float(description="Location accuracy in meters, or null."),
        "recorded_at": fields.String(
            description=(
                "Timestamp supplied with the location fix, or null. "
                "Defaults to the server's current UTC time when omitted."
            )
        ),
        "location_updated_at": fields.String(
            description=(
                "Server UTC time when the location was last saved, or null."
            )
        ),
    },
)
