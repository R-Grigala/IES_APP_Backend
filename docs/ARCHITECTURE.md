# Architecture

## ფენები

```text
HTTP request
    ↓
Flask-RESTX resource (app/api/v1)
    ↓
parser/schema validation (app/api/v1/nsmodels)
    ↓
SQLAlchemy model (app/models)
    ↓
PostgreSQL + PostGIS
```

- `app/__init__.py` ქმნის Flask application-ს, აერთებს extensions-ს და CLI commands-ს.
- `app/extensions.py` ქმნის SQLAlchemy, Flask-Migrate და RESTX API ობიექტებს.
- `app/api/v1/` შეიცავს endpoint behavior-ს.
- `app/api/v1/nsmodels/` შეიცავს request parser-ებსა და Swagger response models-ს.
- `app/models/` არის database schema და serialization logic.
- `app/commands.py` შეიცავს `init_db` და `populate_db` commands-ს.
- `app/utils/geo.py` ამუშავებს PostGIS GeoJSON/geometry conversion-ს.

## ძირითადი flow-ები

### Device + FCM

1. Client აკეთებს `POST /devices/`-ს device metadata-ით.
2. Notification permission-ის ჩართვის შემდეგ აკეთებს `POST /devices/{id}/fcm-tokens/`-ს.
3. Device-ზე token-ის ახალი POST ძველ token-ს შლის.
4. Permission-ის გამორთვისას client აკეთებს `DELETE`-ს.
5. Notification recipient query ითვალისწინებს მხოლოდ არსებულ `notifications_enabled` token-ს.

### Location

`location_settings` არის ცალკე one-to-one ჩანაწერი. Sharing state-ის შეცვლა არ შლის ბოლო კოორდინატს; location submission კი მხოლოდ enabled state-ის დროს მუშაობს.

### Notification recipient selection

`POST /notifications/` არ აგზავნის push-ს პირდაპირ. ის ქმნის `notification_outbox` row-ს იმ device-ებისთვის, რომლებიც აკმაყოფილებენ:

1. `alert_settings.enabled`;
2. earthquake magnitude >= `min_magnitude`;
3. epicenter intersects alert area;
4. device activeა და აქვს active FCM token;
5. იგივე earthquake/device/type უკვე არ არის outbox-ში.

## მონაცემთა სიცოცხლის ციკლი

- Device-ის წაშლა cascade-ით შლის location settings, alert settings, FCM token-ს და notification outbox-ს.
- Felt report-ს სავალდებულო device აქვს; device-ის წაშლისას მისი reports-იც იშლება (`ON DELETE CASCADE`). Felt report დამოუკიდებელი ჩანაწერია და earthquake-ს არ უკავშირდება.
- Earthquake-ის წაშლა cascade-ით შლის notification outbox-სა და attempts-ს.
