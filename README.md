# Django Real Estate Website (2025 Update)

A Real Estate Agent website build using HTML, CSS and Django.
This website serves as a listing directory for a real estate agent.
Clear and simple design using CSS and Bootstrap.
Most of the information visible on the website can be updated from the admin panel without the use of code.

**Tested on Python 3.12.9 and Django 5.2**

## 2025 Update:

- Dockerized the application.
- Re-working the design.
- Fixing the code with up-to date design patterns.
- Updated python libraries

## Features

- Responsive and Mobile Friendly Design using Bootstrap.
- Add Listings with multiple images from Admin Panel.
- Change Website Information from Admin Panel.
- Integrated Google Maps Coordinate System.

## Installation

1. Clone this repository.
2. Copy `.sample.env` to `.env` and fill it in:
   - Generate a secret key: `python -c "import secrets; print(secrets.token_urlsafe())"` and set `SECRET_KEY`.
   - Change the database name, username and password.
   - Set the initial admin username, email and password. The account is created on first start; leave the password empty to skip it.
   - Optional: a Google Maps API key for the admin map widget: https://developers.google.com/maps/documentation/javascript/get-api-key
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

## Changing Website Information and Adding Listings

If you need to change the information contained on the website. Most of information are stored in the database and can be changed from the admin panel (/admin). You can access the admin panel using the admin information you added in step 2.
Listings can also be added or updated from the admin panel.

## TODO

- Better Responsive Images.
- Update Images, Better CSS styling.

## Images

![Index](https://imgur.com/x9fhZmk.jpg)
![Properties](https://imgur.com/Err7SAg.jpg)

More Images: https://imgur.com/a/wZcj2DU
