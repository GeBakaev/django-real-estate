# Django Real Estate Website

A Real Estate Agent website build using HTML, CSS and Django.
This website serves as a listing directory for a real estate agent.
Clear and simple design using CSS and Bootstrap.
Most of the information visible on the website can be updated from the admin panel without the use of code.

**Tested on Python 3.10.0 and Django 4.0.1. (Python 3.8+ and Django 3.2+ will work too)**

## Features

* Responsive and Mobile Friendly Design using Bootstrap.
* Add Listings with multiple images from Admin Panel.
* Change Website Information from Admin Panel.
* Integrated Google Maps Coordinate System. (TODO)

## Installation

1. Clone this repository.
2. *Create new Virtual Env. (Optional)*
3. `python install -r requirements.txt`
4. Change settings.py
    * Generate a Secret Key: `python -c "import secrets; print(secrets.token_urlsafe())"` and add it to SECRET_KEY.
    * *Change DATABASE (Optional)*
5. Create Database: `python manage.py migrate` and Create Admin User `python manage.py createsuperuser`
6. RUN! `python manage.py runserver`

## Changing Website Information and Adding Listings

If you need to change the information contained on the website. Most of information are stored in the database and can be changed from the admin panel (/admin). You can access the admin panel using the user you created in step 5.
Listings can also be added or updated from the admin panel.

## TODO

* Better Responsive Images.
* Convert OLD CSS Styling to Bootstrap.
* Add Support for Google Maps Coordinates.
* Add Simple Deploy to Heroku Button.

## Images

![Index](https://imgur.com/x9fhZmk.jpg)
![Properties](https://imgur.com/Err7SAg.jpg)

More Images: https://imgur.com/a/wZcj2DU