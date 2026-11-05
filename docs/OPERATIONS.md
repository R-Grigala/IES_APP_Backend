# Operations and development

## გარემოს მომზადება

1. შექმენი PostgreSQL role/database და PostGIS:

   ```bash
   bash scripts/bootstrap_db.sh
   ```

2. შეავსე `.env`-ში database პარამეტრები. პაროლი repository-ში არ უნდა ჩაიწეროს.

3. შექმენი fresh schema:

   ```bash
   venv/bin/flask --app run init_db --confirm-text RESET_DB
   ```

   Production-ში დაამატე `--force`.

4. სურვილისამებრ შექმენი სატესტო მონაცემები:

   ```bash
   venv/bin/flask --app run populate_db
   ```

5. გაუშვი API:

   ```bash
   venv/bin/python run.py
   ```

Swagger: `http://127.0.0.1:5000/docs/`.

## CLI commands

- `init_db` — მთლიანად შლის და თავიდან ქმნის ყველა model table-ს.
- `populate_db` — ამატებს sample device, FCM token, alert area, earthquake, felt report და notification outbox row-ს. ხელმეორედ გაშვება არსებულ sample ჩანაწერებს არ იმეორებს.

Schema ცვლილებების შემდეგ fresh environment-ს თავიდან ქმნიან `init_db`-ით.

## კონფიგურაცია

მხარდაჭერილი გარემოს ცვლადებია:

- `APP_ENV` — development ან production;
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`;
- `POSTGRES_SSLMODE`;
- `DB_ECHO`.

Application intentionally არ იყენებს `postgres`/`root` superuser-ს.

## შემოწმება

Python syntax-ის სწრაფი შემოწმება:

```bash
python3 -m py_compile app/**/*.py
```

API-ის interactive contract ნახე Swagger-ში. Database-dependent behavior-ის შესამოწმებლად საჭიროა მოქმედი PostgreSQL/PostGIS connection.
