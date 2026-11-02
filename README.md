# Django Real Estate Website (2025 Update)

A Real Estate Agent website built with Django and Tailwind CSS.
This website serves as a listing directory for a real estate agent.
Most of the information visible on the website can be updated from the admin panel without the use of code.

**Tested on Python 3.12.9 and Django 5.2**

## 2025 Update:

- Dockerized the application.
- Re-working the design.
- Fixing the code with up-to date design patterns.
- Updated python libraries

## Features

- Responsive, mobile-friendly design built with Tailwind CSS (no JavaScript framework).
- Add Listings with multiple images from Admin Panel.
- Change Website Information from Admin Panel.
- Map on every listing (OpenStreetMap via Leaflet, no API key needed).
- Search, filter (location, price, area) and sort listings; results update in place via htmx and every filter state is a shareable URL.
- Photo gallery on each listing with thumbnails, arrows, keyboard and swipe navigation.

## Installation

1. Clone this repository.
2. Copy `.sample.env` to `.env` and fill it in:
   - Generate a secret key: `python -c "import secrets; print(secrets.token_urlsafe())"` and set `SECRET_KEY`.
   - Change the database name, username and password.
   - Set the initial admin username, email and password. The account is created on first start; leave the password empty to skip it.
   - Set `DEBUG=0` and `USE_HTTPS=1` when deploying behind TLS.
3. Run `docker compose up --build`. On start the web container applies migrations, collects static files and creates the admin user; nginx serves the site on port 80 and static/media files directly.

### Local development without Docker

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py test
DEBUG=1 .venv/bin/python manage.py runserver
```

Without a `.env` the app falls back to SQLite and a development secret key.

### Styling

The stylesheet is compiled from `tailwind/site.css` with the Tailwind CSS standalone CLI
(no Node required). `scripts/tailwind` downloads the pinned release on first use:

```bash
scripts/tailwind            # one-off minified build -> static/css/site.css
scripts/tailwind --watch    # rebuild as templates change
```

The compiled `static/css/site.css` is committed, so deployments need no build step. CI fails if
it is out of date, so rebuild after changing templates or `tailwind/site.css`.

## Changing Website Information and Adding Listings

If you need to change the information contained on the website. Most of information are stored in the database and can be changed from the admin panel (/admin). You can access the admin panel using the admin information you added in step 2.
Listings can also be added or updated from the admin panel.

## Images

![Index](https://imgur.com/x9fhZmk.jpg)
![Properties](https://imgur.com/Err7SAg.jpg)

More Images: https://imgur.com/a/wZcj2DU
