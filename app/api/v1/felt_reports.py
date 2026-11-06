from uuid import UUID

from flask_restx import Resource, marshal

from app.api.v1.nsmodels.felt_reports import (
    error_model,
    felt_report_device_list_model,
    felt_report_list_model,
    felt_report_model,
    felt_report_parser,
    felt_reports_get_parser,
    felt_reports_ns,
)
from app.extensions import db
from app.models import Device, FeltReport

LIST_DEFAULT_LIMIT = 100
LIST_MAX_LIMIT = 200


def _limit(value):
    if value is None:
        return LIST_DEFAULT_LIMIT, None
    if value < 1 or value > LIST_MAX_LIMIT:
        return None, (
            {
                "error": "validation_error",
                "message": f"limit must be between 1 and {LIST_MAX_LIMIT}.",
            },
            400,
        )
    return value, None


def _get_device(device_id):
    try:
        device_uuid = UUID(device_id)
    except (TypeError, ValueError):
        return None, {"error": "validation_error", "message": "device_id must be a UUID."}, 400

    device = db.session.get(Device, device_uuid)
    if device is None:
        return None, {"error": "not_found", "message": "Device not found."}, 404
    return device, None, None


def _create_felt_report(device_id):
    device, error, status = _get_device(device_id)
    if error:
        return error, status

    args = felt_report_parser.parse_args()
    time_ago = args["time_ago"]
    if time_ago < 0:
        return {"error": "validation_error", "message": "time_ago must be zero or greater."}, 400

    latitude = args["latitude"]
    longitude = args["longitude"]
    accuracy = args.get("accuracy")
    if not -90 <= latitude <= 90:
        return {"error": "validation_error", "message": "latitude must be between -90 and 90."}, 400
    if not -180 <= longitude <= 180:
        return {"error": "validation_error", "message": "longitude must be between -180 and 180."}, 400
    if accuracy is not None and accuracy < 0:
        return {"error": "validation_error", "message": "accuracy must be zero or greater."}, 400

    report = FeltReport(
        device_id=device.device_id,
        intensity=args["intensity"],
        time_ago=time_ago,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
    )
    report.create()
    return marshal(report.to_dict(), felt_report_model), 201


@felt_reports_ns.route("/felt-reports/")
class FeltReportsApi(Resource):
    @felt_reports_ns.expect(felt_reports_get_parser)
    @felt_reports_ns.response(200, "Success", felt_report_list_model)
    @felt_reports_ns.response(400, "Validation Error", error_model)
    def get(self):
        """List felt reports, newest created_at first."""
        limit, error = _limit(felt_reports_get_parser.parse_args().get("limit"))
        if error:
            return error
        total = FeltReport.query.count()
        rows = (
            FeltReport.query.order_by(FeltReport.created_at.desc(), FeltReport.id.desc())
            .limit(limit)
            .all()
        )
        return marshal(
            {"items": [row.to_dict() for row in rows], "total": total, "limit": limit},
            felt_report_list_model,
        ), 200



@felt_reports_ns.route("/devices/<string:device_id>/felt-report/")
class DeviceFeltReportApi(Resource):
    @felt_reports_ns.expect(felt_reports_get_parser)
    @felt_reports_ns.response(200, "Success", felt_report_device_list_model)
    @felt_reports_ns.response(400, "Validation Error", error_model)
    @felt_reports_ns.response(404, "Not Found", error_model)
    def get(self, device_id):
        """Return all felt reports submitted by a device."""
        device, error, status = _get_device(device_id)
        if error:
            return error, status

        limit, error = _limit(felt_reports_get_parser.parse_args().get("limit"))
        if error:
            return error

        query = FeltReport.query.filter_by(device_id=device.device_id)
        rows = query.order_by(FeltReport.created_at.desc(), FeltReport.id.desc()).limit(limit).all()
        return marshal(
            {
                "device_id": str(device.device_id),
                "items": [row.to_dict() for row in rows],
                "total": query.count(),
                "limit": limit,
            },
            felt_report_device_list_model,
        ), 200

    @felt_reports_ns.expect(felt_report_parser)
    @felt_reports_ns.response(201, "Created", felt_report_model)
    @felt_reports_ns.response(400, "Validation Error", error_model)
    @felt_reports_ns.response(404, "Not Found", error_model)
    def post(self, device_id):
        """Store a felt report for a registered device."""
        return _create_felt_report(device_id)


@felt_reports_ns.route("/felt-reports/<int:report_id>")
class FeltReportDetailApi(Resource):
    @felt_reports_ns.response(200, "Success", felt_report_model)
    @felt_reports_ns.response(404, "Not Found", error_model)
    def get(self, report_id):
        """Return one felt report."""
        report = db.session.get(FeltReport, report_id)
        if report is None:
            return {"error": "not_found", "message": "Felt report not found."}, 404
        return marshal(report.to_dict(), felt_report_model), 200
