from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from math import asin, cos, radians, sin, sqrt
from urllib.error import URLError
from urllib.request import urlopen
from uuid import UUID

from flask import current_app
from flask.cli import with_appcontext
import click
import sqlalchemy as sa

from app.extensions import db
from app.models import (
    AlertSettings,
    Device,
    FcmToken,
    Earthquake,
    FeltReport,
    NotificationAttempt,
    NotificationOutbox,
)
from app.utils.geo import multipolygon_from_circle, point_wkb

PUBLISH_EVENTS_URL = "https://iesdata.iliauni.edu.ge:3030/api/publish_events/?limit=5"

# Stable id so a second populate_db does not insert the same row again.
SAMPLE_DEVICE = {
    "device_id": UUID("11111111-1111-4111-8111-111111111101"),
    "fcm_token": "sample-fcm-token-tbilisi-android",
    "platform": "android",
    "language": "ka",
    "app_version": "1.2.0",
    "min_magnitude": Decimal("3.0"),
    "circle": (44.8271, 41.7151, 120_000),
}

def _is_production_environment():
    """ამოწმებს გაშვებულია თუ არა აპი production გარემოში."""
    return current_app.config.get("APP_ENV") == "production"


def _require_reset_confirmation(confirm_text):
    """init_db-სთვის სავალდებულო დამცავი ტექსტის ვალიდაცია."""
    if confirm_text != "RESET_DB":
        raise click.ClickException("უსაფრთხოების მიზნით მიუთითე --confirm-text RESET_DB")


def _ensure_postgis():
    """Geometry სვეტებს PostGIS სჭირდება. გაფართოებას სუპერმომხმარებელი აყენებს."""
    exists = db.session.execute(
        sa.text("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
    ).scalar()
    if not exists:
        raise click.ClickException("PostGIS არ არის. ჯერ გაუშვი scripts/bootstrap_db.sh.")


def init_db_core():
    """Drop and recreate all database tables."""
    _ensure_postgis()
    db.session.execute(sa.text("DROP TABLE IF EXISTS earthquake_revisions CASCADE"))
    db.session.execute(sa.text("DROP TABLE IF EXISTS notifications_sent CASCADE"))
    db.session.commit()
    db.drop_all()
    db.create_all()


def _km(lat1, lon1, lat2, lon2):
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(a))


def _magnitude_choice(event):
    magnitudes = event.get("magnitudes") or []
    fallback = None
    for item in magnitudes:
        if item.get("value") is None:
            continue
        code = ((item.get("magnitude") or {}).get("code") or "M").upper()
        chosen = (code, float(item["value"]))
        if code == "ML":
            return chosen
        if fallback is None:
            fallback = chosen
    return fallback


def _magnitude(event):
    chosen = _magnitude_choice(event)
    return None if chosen is None else chosen[1]


def _origin_time(event):
    raw = event.get("origin_time") or ""
    if raw.endswith("Z") or "+" in raw[10:]:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    else:
        parsed = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _published_events():
    try:
        with urlopen(PUBLISH_EVENTS_URL, timeout=15) as response:
            payload = json.load(response)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        click.echo(
            f"publish_events was not reachable ({exc.__class__.__name__}). "
            "The sample felt report stays unlinked and the notification is skipped."
        )
        return []

    events = []
    for item in payload.get("items") or []:
        event = item.get("event") or {}
        if event.get("id") is None or event.get("latitude") is None or event.get("longitude") is None:
            continue
        events.append(event)
    click.echo(f"Read {len(events)} published events.")
    return events


def _intensity(magnitude, distance_km):
    if magnitude >= 4 and distance_km < 40:
        return "SEVERE"
    if magnitude >= 3 and distance_km < 80:
        return "MODERATE"
    return "MILD"


def _nearest_event(events, latitude, longitude):
    ranked = []
    for event in events:
        magnitude = _magnitude(event)
        if magnitude is None:
            continue
        distance = _km(latitude, longitude, float(event["latitude"]), float(event["longitude"]))
        ranked.append((distance, magnitude, event))
    ranked.sort(key=lambda item: item[0])
    return ranked[0] if ranked else None


def populate_db_core():
    """Insert one sample device, its alert area, one felt report, and one notification."""
    _ensure_postgis()
    spec = SAMPLE_DEVICE
    longitude, latitude, radius_m = spec["circle"]
    events = _published_events()

    device = db.session.get(Device, spec["device_id"])
    if device is None:
        device = Device(
            device_id=spec["device_id"],
            platform=spec["platform"],
            language=spec["language"],
            app_version=spec["app_version"],
        )
        device.create(commit=False)
        click.echo(f"Created sample device: {spec['device_id']}")
    else:
        click.echo("Sample device already exists.")

    if FcmToken.query.filter_by(device_id=spec["device_id"]).first() is None:
        FcmToken(
            device_id=spec["device_id"],
            fcm_token=spec["fcm_token"],
            notifications_enabled=True,
        ).create(commit=False)
        click.echo("Created sample FCM token.")
    else:
        click.echo("Sample FCM token already exists.")

    if db.session.get(AlertSettings, spec["device_id"]) is None:
        AlertSettings(
            device_id=spec["device_id"],
            enabled=True,
            min_magnitude=spec["min_magnitude"],
            area=multipolygon_from_circle(longitude, latitude, radius_m),
            area_source="circle",
        ).create(commit=False)
        click.echo("Created sample alert area: 120 km circle around Tbilisi.")
    else:
        click.echo("Sample alert settings already exist.")

    nearest = _nearest_event(events, latitude, longitude)
    earthquake = None
    if nearest is not None:
        _distance, magnitude, event = nearest
        ies_event_id = int(event["id"])
        magnitude_type, magnitude_value = _magnitude_choice(event)
        earthquake = Earthquake.query.filter_by(ies_event_id=ies_event_id).first()
        if earthquake is None:
            earthquake = Earthquake(
                ies_event_id=ies_event_id,
                iesdata_id=event.get("iesdata_id"),
                seiscomp_oid=event.get("seiscomp_oid"),
                is_automatic=bool(event.get("is_automatic")),
                origin_time=_origin_time(event),
                latitude=float(event["latitude"]),
                longitude=float(event["longitude"]),
                depth=event.get("depth") or 0,
                location_ge=event.get("location_ge") or str(ies_event_id),
                location_en=event.get("location_en") or str(ies_event_id),
                magnitude_type=magnitude_type,
                magnitude_value=magnitude_value,
                created_by_kind="service",
                created_by_name="ies-monitoring",
            )
            earthquake.create(commit=False)
            click.echo(f"Created sample earthquake {ies_event_id}.")
        else:
            click.echo(f"Sample earthquake already exists: {ies_event_id}.")

    report = FeltReport.query.filter_by(device_id=spec["device_id"]).first()
    if report is None and nearest is not None:
        distance, magnitude, event = nearest
        origin = _origin_time(event)
        reported_at = origin + timedelta(minutes=12)
        minutes_ago = 7
        FeltReport(
            device_id=spec["device_id"],
            earthquake_id=earthquake.id,
            intensity=_intensity(magnitude, distance),
            minutes_ago=minutes_ago,
            reported_at=reported_at,
            felt_at=reported_at - timedelta(minutes=minutes_ago),
            location=point_wkb(float(event["longitude"]) + 0.02, float(event["latitude"]) + 0.01),
            language=spec["language"],
            platform=spec["platform"],
        ).create(commit=False)
        click.echo(f"Created felt report for earthquake {earthquake.ies_event_id}.")
    elif report is None:
        reported_at = datetime.now(timezone.utc)
        FeltReport(
            device_id=spec["device_id"],
            intensity="MILD",
            minutes_ago=None,
            reported_at=reported_at,
            felt_at=None,
            language=spec["language"],
            platform=spec["platform"],
        ).create(commit=False)
        click.echo("Created an unlinked felt report.")
    else:
        click.echo("Sample felt report already exists.")

    if earthquake is not None and NotificationOutbox.query.filter_by(device_id=spec["device_id"]).first() is None:
        _distance, magnitude, event = nearest
        matches = db.session.execute(
            sa.text(
                """
                SELECT 1
                FROM alert_settings AS a
                JOIN devices AS d ON d.device_id = a.device_id
                JOIN fcm_tokens AS ft ON ft.device_id = d.device_id
                WHERE d.device_id = :device_id
                  AND d.is_active
                  AND a.enabled
                  AND a.min_magnitude <= :magnitude
                  AND ft.notifications_enabled
                  AND ST_Intersects(
                        a.area,
                        ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
                      )
                """
            ),
            {
                "device_id": spec["device_id"],
                "magnitude": magnitude,
                "longitude": float(event["longitude"]),
                "latitude": float(event["latitude"]),
            },
        ).scalar()
        if matches:
            sent_at = datetime.now(timezone.utc)
            outbox = NotificationOutbox(
                earthquake_id=earthquake.id,
                device_id=spec["device_id"],
                notification_type="alert",
                status="ok",
                attempt_count=1,
                processed_at=sent_at,
            )
            outbox.create(commit=False)
            NotificationAttempt(
                outbox_id=outbox.id,
                expo_ticket_id=f"sample-ticket-{earthquake.ies_event_id}-{spec['device_id'].hex[:8]}",
                status="ok",
                attempted_at=sent_at,
            ).create(commit=False)
            click.echo(f"Recorded sample notification for earthquake {earthquake.ies_event_id}.")
        else:
            click.echo("Sample notification skipped: the epicenter is outside the alert area.")
    elif earthquake is None:
        click.echo("Sample notification skipped: no published event.")
    else:
        click.echo("Sample notification already exists.")

    db.session.commit()


@click.command("init_db")
@click.option(
    "--force",
    is_flag=True,
    help="Production გარემოში აუცილებელია ამ flag-ის გადაცემა.",
)
@click.option(
    "--confirm-text",
    default="",
    help="უსაფრთხოებისთვის ზუსტად მიუთითე: RESET_DB",
)
@with_appcontext
def init_db(force, confirm_text):
    """CLI: recreate DB schema."""
    if _is_production_environment() and not force:
        raise click.ClickException("Production გარემოში init_db დაბლოკილია. გამოიყენე --force.")

    _require_reset_confirmation(confirm_text)

    if not force and not click.confirm("ნამდვილად გსურს ბაზის სრული reset (drop/create)?"):
        click.echo("ოპერაცია გაუქმდა.")
        return

    click.echo("Creating Database")
    init_db_core()
    click.echo("Database Created")


@click.command("populate_db")
@click.option(
    "--force",
    is_flag=True,
    help="Production გარემოში აუცილებელია ამ flag-ის გადაცემა.",
)
@with_appcontext
def populate_db(force):
    """CLI: insert one sample device, alert area, felt report, and notification."""
    if _is_production_environment() and not force:
        raise click.ClickException("Production გარემოში populate_db დაბლოკილია. გამოიყენე --force.")

    click.echo("Populating database from published earthquakes...")
    populate_db_core()
    click.echo("Database Populated")
