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
2. Add keys inside a file called .env (Sample: .sample.env)
   - Generate a Secret Key: `python -c "import secrets; print(secrets.token_urlsafe())"` and add it to SECRET_KEY.
   - _Change DATABASE: Name, Username, Password._
   - _Admin Information: Username, Email, Password._
   - Get Your Google Maps API Key: https://developers.google.com/maps/documentation/javascript/get-api-key and add it to GEOPOSITION_GOOGLE_MAPS_API_KEY.
3. RUN! `docker compose -f docker-compose.yaml up --build`

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
