from uuid import UUID

from flask_restx import Resource, marshal
from sqlalchemy.exc import IntegrityError

from app.api.v1.nsmodels.fcm_tokens import (
    fcm_token_error_model,
    fcm_token_list_model,
    fcm_token_model,
    fcm_token_parser,
    fcm_tokens_ns,
)
from app.extensions import db
from app.models import Device, FcmToken


def _device(device_id):
    try:
        device_uuid = UUID(device_id)
    except (TypeError, ValueError):
        return None, ({"error": "validation_error", "message": "device_id must be a UUID."}, 400)

    device = db.session.get(Device, device_uuid)
    if device is None:
        return None, ({"error": "not_found", "message": "Device not found."}, 404)
    return device, None


def _clean_token(value):
    return value.strip() if value and value.strip() else None


@fcm_tokens_ns.route("/devices/<string:device_id>/fcm-tokens/")
class FcmTokenListApi(Resource):
    @fcm_tokens_ns.response(200, "Success", fcm_token_list_model)
    @fcm_tokens_ns.response(400, "Validation Error", fcm_token_error_model)
    @fcm_tokens_ns.response(404, "Not Found", fcm_token_error_model)
    def get(self, device_id):
        device, error = _device(device_id)
        if error:
            return error
        return marshal(
            {"items": [token.to_dict() for token in device.fcm_tokens]},
            fcm_token_list_model,
        ), 200

    @fcm_tokens_ns.expect(fcm_token_parser)
    @fcm_tokens_ns.response(201, "Created", fcm_token_model)
    @fcm_tokens_ns.response(200, "Updated", fcm_token_model)
    @fcm_tokens_ns.response(400, "Validation Error", fcm_token_error_model)
    @fcm_tokens_ns.response(404, "Not Found", fcm_token_error_model)
    @fcm_tokens_ns.response(409, "Conflict", fcm_token_error_model)
    def post(self, device_id):
        device, error = _device(device_id)
        if error:
            return error

        args = fcm_token_parser.parse_args()
        token_value = _clean_token(args.get("fcm_token"))
        if token_value is None or len(token_value) > 4096:
            return {
                "error": "validation_error",
                "message": "fcm_token must be between 1 and 4096 characters.",
            }, 400

        now = db.session.scalar(db.select(db.func.now()))
        token = FcmToken.query.filter_by(fcm_token=token_value).first()
        created = token is None

        # Keep exactly one token for this device. Delete the previous token
        # before moving an existing token here, so the device_id unique
        # constraint is not violated during flush.
        previous_token = FcmToken.query.filter(
            FcmToken.device_id == device.device_id,
            FcmToken.fcm_token != token_value,
        ).all()
        for old_token in previous_token:
            db.session.delete(old_token)
        db.session.flush()

        if token is None:
            token = FcmToken(
                device=device,
                fcm_token=token_value,
                notifications_enabled=True,
            )
            db.session.add(token)
        else:
            token.device = device
            token.notifications_enabled = True
            token.updated_at = now

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "conflict", "message": "Could not store the FCM token."}, 409

        db.session.refresh(token)
        return marshal(token.to_dict(), fcm_token_model), 201 if created else 200


@fcm_tokens_ns.route("/devices/<string:device_id>/fcm-tokens/<int:token_id>")
class FcmTokenDetailApi(Resource):
    @fcm_tokens_ns.response(204, "Deleted")
    @fcm_tokens_ns.response(400, "Validation Error", fcm_token_error_model)
    @fcm_tokens_ns.response(404, "Not Found", fcm_token_error_model)
    def delete(self, device_id, token_id):
        device, error = _device(device_id)
        if error:
            return error

        token = FcmToken.query.filter_by(id=token_id, device_id=device.device_id).first()
        if token is None:
            return {"error": "not_found", "message": "FCM token not found."}, 404

        db.session.delete(token)
        db.session.commit()
        return "", 204
