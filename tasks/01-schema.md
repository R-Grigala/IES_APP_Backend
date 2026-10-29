# 01 — PostGIS და ოთხი ცხრილი

## რას ვაკეთებთ

ერთ მიგრაციაში ვამატებთ PostGIS-ს და ოთხ ცხრილს: `devices`, `alert_settings`, `felt_reports`, `notifications_sent`.

`regions` არ იქმნება. მიწისძვრის `event_id` გარე გასაღები არ არის: მიწისძვრა სხვა სერვისზე დევს და აქიდან მხოლოდ endpoint-ით იკითხება.

## როგორ

- `CREATE EXTENSION IF NOT EXISTS postgis` ამ აპის ბაზაზე.
- გეომეტრია SRID 4326-ია: ზონა `MultiPolygon`, ანგარიშის წერტილი `Point`.
- `alert_settings.area` და `felt_reports.location` იღებენ GIST ინდექსს.
- `felt_reports.device_id` არის `ON DELETE SET NULL`: მოწყობილობის წაშლისას ანგარიში სტატისტიკისთვის რჩება.
- `notifications_sent`-ის პირველადი გასაღები `(event_id, device_id)`-ია. `device_id` შლის ჩანაწერს მოწყობილობასთან ერთად. `event_id`-ს `ON DELETE` არ აქვს, რადგან მიწისძვრის ცხრილი ამ ბაზაში არ არის.
- `area_source` არის მხოლოდ `custom` ან `circle`. ორივე ბაზაში პოლიგონია.

```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE devices (
  device_id     uuid PRIMARY KEY,
  push_token    text UNIQUE,
  platform      text NOT NULL CHECK (platform IN ('ios', 'android', 'web')),
  language      text NOT NULL DEFAULT 'ka' CHECK (language IN ('ka', 'en')),
  app_version   text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  last_seen_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE alert_settings (
  device_id      uuid PRIMARY KEY REFERENCES devices(device_id) ON DELETE CASCADE,
  enabled        boolean NOT NULL DEFAULT true,
  min_magnitude  numeric(3,1) NOT NULL DEFAULT 3.0,
  area           geometry(MultiPolygon, 4326) NOT NULL,
  area_source    text NOT NULL DEFAULT 'custom' CHECK (area_source IN ('custom', 'circle')),
  updated_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX alert_settings_area_idx ON alert_settings USING GIST (area);

CREATE TABLE felt_reports (
  id           bigserial PRIMARY KEY,
  device_id    uuid REFERENCES devices(device_id) ON DELETE SET NULL,
  intensity    text NOT NULL CHECK (intensity IN ('MILD', 'MODERATE', 'SEVERE')),
  minutes_ago  integer CHECK (minutes_ago >= 0),
  reported_at  timestamptz NOT NULL,
  felt_at      timestamptz,
  location     geometry(Point, 4326),
  event_id     integer,
  language     text,
  platform     text,
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX felt_reports_device_idx   ON felt_reports (device_id);
CREATE INDEX felt_reports_event_idx    ON felt_reports (event_id);
CREATE INDEX felt_reports_felt_at_idx  ON felt_reports (felt_at);
CREATE INDEX felt_reports_location_idx ON felt_reports USING GIST (location);

CREATE TABLE notifications_sent (
  event_id         integer NOT NULL,
  device_id        uuid NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
  expo_ticket_id   text,
  status           text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ok', 'error')),
  error            text,
  sent_at          timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (event_id, device_id)
);
```

## მზადაა, როცა

მიგრაცია ერთხელ ეშვება, `regions` და `REFERENCES seismic_events` სქემაში არ არის, და `event_id` ორივე ცხრილში ჩვეულებრივი `integer`-ია.
