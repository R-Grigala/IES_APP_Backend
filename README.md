# IES_APP_Backend

Flask API for the IES earthquake mobile application. The layout matches Ies_Monitoring: `run.py`, `app/extensions.py`, `app/models`, Flask-RESTX namespaces, and Flask-Migrate.

The database password stays in `.env`. The app role is not the `postgres` superuser.

```bash
bash scripts/bootstrap_db.sh
venv/bin/flask --app run init_db --confirm-text RESET_DB
venv/bin/flask --app run upgrade_db
venv/bin/flask --app run populate_db
venv/bin/python run.py
```

`bootstrap_db.sh` sudo-ს პაროლს გთხოვს, `.env`-ის როლსა და ბაზას ქმნის და PostGIS-ს აყენებს.

`init_db` ცხრილებს თავიდან ქმნის და `--confirm-text RESET_DB` სჭირდება. Production-ში დამატებით `--force` უნდა გადასცე. `upgrade_db` არსებულ მონაცემს არ შლის: აკლია ცხრილს ან ცარიელ სვეტს ამატებს და ძველი `devices` ცხრილიდან ლოკაციის ველებს `location_settings`-ში გადაიტანს. `populate_db` ერთ სატესტო მოწყობილობას წერს თბილისის 120 კმ წრით, ერთ შენახულ მიწისძვრას, ერთ felt ანგარიშს და ერთ შეტყობინებას `notification_outbox`-ში. `event_id` უახლოესი გამოქვეყნებული მიწისძვრის `event.id`-ია და `earthquakes.ies_event_id`-ში ინახება. ხელახლა გაშვება იმავე ჩანაწერს არ იმეორებს.

Swagger: `http://127.0.0.1:5000/docs/`

| Method | Path | Stores |
| --- | --- | --- |
| GET | `/api/v1/devices/` | stored devices (`?limit=`) |
| GET | `/api/v1/devices/<id>` | one device |
| POST | `/api/v1/devices/` | device id, push token, language |
| GET | `/api/v1/location/<device_id>/` | sharing state and last known location |
| PATCH | `/api/v1/location/<device_id>/` | enable or disable location sharing |
| POST | `/api/v1/location/<device_id>/` | submit the initial or latest location fix |
| PUT | `/api/v1/location/<device_id>/` | replace an existing device's latest location |
| GET | `/api/v1/alert-settings/` | stored alert areas (`?limit=`) |
| GET | `/api/v1/devices/<id>/alert-settings` | one device's polygon |
| PUT | `/api/v1/devices/<id>/alert-settings` | one polygon and minimum magnitude |
| GET | `/api/v1/felt-reports/` | stored felt reports (`?limit=`) |
| GET | `/api/v1/felt-reports/<id>` | one felt report |
| POST | `/api/v1/felt-reports/` | a felt report; `felt_at` is calculated on the server |
| GET, POST | `/api/v1/earthquakes/` | list earthquakes, or store a new one |
| GET, PUT, DELETE | `/api/v1/earthquakes/<event_id>` | one earthquake; PUT replaces it, DELETE removes it |
| GET | `/api/v1/notifications/stats` | totals, status counts, and counts per earthquake |
| GET | `/api/v1/notifications/` | outbox rows (`?limit=`, `event_id`, `device_id`, `status`) |
| GET | `/api/v1/notifications/<id>/attempts` | Expo attempts for one outbox row |
| POST | `/api/v1/notifications/` | `event_id` of a stored earthquake; queues recipients |

### Location settings

Register the device with `POST /api/v1/devices/` first. Location endpoints only
operate on an existing device; they never register one. Location sharing starts
disabled. Enable it with `PATCH /api/v1/location/<device_id>/` and
`{"location_sharing_enabled": true}` before submitting a location.

Send location fixes with `POST` or `PUT` to
`/api/v1/location/<device_id>/`. Both store or replace the device's single
latest location in `location_settings`.

```json
{
  "latitude": 41.7151,
  "longitude": 44.8271,
  "accuracy": 10,
  "recorded_at": "2026-11-04T12:30:00Z"
}
```

`latitude` and `longitude` are required and must be in `-90..90` and `-180..180`.
`accuracy` is optional, measured in meters, and cannot be negative. `recorded_at`
is the location-fix timestamp and must include a timezone; if omitted, it
defaults to the server's current UTC time. The response's `location_updated_at`
is the server UTC time when the fix was saved.

`GET /api/v1/location/<device_id>/` returns the sharing state and latest fix.
Location fields are `null` until the first fix arrives. Disabling sharing with
`PATCH` preserves the saved location and blocks new submissions with `403`.
There is no location deletion endpoint.
