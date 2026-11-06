# Database

Database არის PostgreSQL + PostGIS. Geometry SRID არის `4326`.

## ცხრილები

### `devices`

Device installation-ის metadata: `device_id` (UUID PK), platform, language, app version, active state და timestamps.

### `fcm_tokens`

ერთი აქტიური FCM token თითო device-ზე:

- `device_id` — FK `devices.device_id`, `UNIQUE`, `ON DELETE CASCADE`;
- `fcm_token` — required და globally `UNIQUE`;
- `notifications_enabled` — active token-ის flag;
- `created_at`, `updated_at`.

### `location_settings`

One-to-one device location state. `device_id` ერთდროულად PK და FK-ია. ინახავს sharing state-ს, ბოლო latitude/longitude/accuracy-ს და client/server timestamps-ს.

### `alert_settings`

One-to-one device alert configuration. ინახავს `enabled`, `min_magnitude`, `area` (`MULTIPOLYGON`, SRID 4326) და `area_source` (`custom`/`circle`). Area-ზე არის GiST index.

### `earthquakes`

ლოკალური earthquake record. `ies_event_id` უნიკალურია; სხვა ცხრილები იყენებენ ლოკალურ `id`-ს. ინახება ერთი არჩეული magnitude — `ML`, ან პირველი მოწოდებული მნიშვნელობა.

### `felt_reports`

მომხმარებლის report. ინახავს სავალდებულო `device_id`-ს, `intensity`-ს,
`time_ago`-ს, server-side `created_at`-ს და frontend-იდან
მიღებულ latitude/longitude/accuracy-ს. Report ცალკე ინახება და მიწისძვრას არ
უკავშირდება. `created_at` არის სერვერზე report-ის მიღების დრო.
`intensity` არის `MILD`, `MODERATE` ან `SEVERE`.

### `notification_outbox`

Notification delivery queue. უნიკალური constraint იცავს ერთი earthquake/device/type-ის duplicate row-სგან. სტატუსებია `pending`, `processing`, `ok`, `error`.

### `notification_attempts`

Outbox delivery attempt-ის audit log. ინახავს Expo ticket/receipt-ს, status-ს და error message-ს.

## კავშირები

```text
devices 1 ─── 0..1 location_settings
devices 1 ─── 0..1 alert_settings
devices 1 ─── 0..1 fcm_tokens
devices 1 ─── N felt_reports
devices 1 ─── N notification_outbox
earthquakes 1 ─── N felt_reports
earthquakes 1 ─── N notification_outbox
notification_outbox 1 ─── N notification_attempts
```

## Schema lifecycle

`init_db` არის destructive reset: `db.drop_all()` და `db.create_all()`. ის გამოიყენე მხოლოდ მაშინ, როცა მონაცემების წაშლა მისაღებია. ახალ გარემოში საჭირო PostGIS extension-ისთვის ჯერ გაუშვი `scripts/bootstrap_db.sh`, შემდეგ `init_db` და `populate_db`.
