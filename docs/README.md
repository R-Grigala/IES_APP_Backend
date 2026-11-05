# IES App Backend documentation

ეს ფოლდერი აღწერს აპლიკაციის არქიტექტურას, მონაცემთა ბაზას, API-ს და გაშვების წესებს.

## დოკუმენტები

- [API reference](API.md) — ყველა v1 endpoint, payload, response და სტატუსი.
- [Architecture](ARCHITECTURE.md) — აპლიკაციის ფენები და ძირითადი flow-ები.
- [Database](DATABASE.md) — ცხრილები, კავშირები, constraint-ები და cascade წესები.
- [Operations](OPERATIONS.md) — გარემოს მომზადება, ბაზის შექმნა, seed და გაშვება.

## სწრაფი ბმულები

- Swagger UI: `http://127.0.0.1:5000/docs/`
- API base path: `/api/v1`
- მთავარი entrypoint: [`run.py`](../run.py)
- Flask app setup: [`app/__init__.py`](../app/__init__.py)
- CLI commands: [`app/commands.py`](../app/commands.py)
