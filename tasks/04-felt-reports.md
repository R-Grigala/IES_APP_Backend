# 04 — felt_reports

## რას ვაკეთებთ

ვინახავთ „იგრძენით მიწისძვრა?“ ანგარიშს, რომელიც კონკრეტულ რეგისტრირებულ
მოწყობილობას ეკუთვნის.

## API

```http
POST /api/v1/devices/{device_id}/felt-report/
Content-Type: application/json
```

`device_id` URL-ში იგზავნება. Body-ში იგზავნება `intensity`, `time_ago`,
`latitude`, `longitude` და optional `accuracy`.
`created_at` body-ში არ იგზავნება — მას სერვერი ავტომატურად წერს report-ის
შექმნისას.

```json
{
  "intensity": "MODERATE",
  "time_ago": 5,
  "latitude": 41.7151,
  "longitude": 44.8271,
  "accuracy": 10
}
```

`intensity` არის `MILD`, `MODERATE` ან `SEVERE`; `time_ago` და `accuracy` არ
შეიძლება იყოს უარყოფითი. Latitude-ის დიაპაზონია `-90..90`, longitude-ის —
`-180..180`. სერვერი ამოწმებს device-ის არსებობას, ინახავს კოორდინატებს და
კოორდინატები ინახება მხოლოდ `latitude`, `longitude` და `accuracy` ველებში;
PostGIS `location` ან `earthquake_id` report-ს არ აქვს.

პასუხები: `201` წარმატებაზე, `400` არასწორ მონაცემებზე და `404` უცნობ device-ზე.

მოწყობილობის report-ების სანახავად გამოიყენება:

```http
GET /api/v1/devices/{device_id}/felt-report/?limit=100
```

პასუხში მოდის `device_id`, report-ების სრული რაოდენობა `total`-ში და ბოლო
report-ები `items`-ში, `created_at`-ის კლებადობით.
