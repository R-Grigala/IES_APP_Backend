from flask_restx import fields

from app.extensions import api

fcm_tokens_ns = api.namespace(
    "FCM Tokens",
    description="Firebase Cloud Messaging tokens registered for devices",
    path="/api/v1",
)

fcm_token_model = fcm_tokens_ns.model(
    "FcmToken",
    {
        "id": fields.Integer(required=True),
        "device_id": fields.String(required=True),
        "fcm_token": fields.String(required=True),
        "notifications_enabled": fields.Boolean(required=True),
        "created_at": fields.String(required=True),
        "updated_at": fields.String(required=True),
    },
)

fcm_token_list_model = fcm_tokens_ns.model(
    "FcmTokenList",
    {
        "items": fields.List(fields.Nested(fcm_token_model), required=True),
    },
)

fcm_token_parser = fcm_tokens_ns.parser()
fcm_token_parser.add_argument("fcm_token", type=str, required=True, location="json")

fcm_token_error_model = fcm_tokens_ns.model(
    "FcmTokenError",
    {
        "error": fields.String(required=True),
        "message": fields.String(required=True),
    },
)
