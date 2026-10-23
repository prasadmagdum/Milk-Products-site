# Magdum Dairy

A Django store for browsing dairy products, managing customer addresses, and placing orders.

## Features

- Product categories, search, and product details
- Customer registration, sign-in, password change, and password reset
- Customer address management
- Authenticated shopping cart with quantity controls
- Checkout, persisted order history, and order-status management in Django admin
- Wishlist management
- Contact form email delivery with saved messages in Django admin

Orders are recorded with a **Pending** status. This project does not currently integrate an online payment provider; payment must be arranged outside the site.

## Run locally

From the `ec` project directory:

```powershell
python manage.py migrate
python manage.py runserver
```

For local development, contact and password-reset emails are written to the console by Django's configured email backend.
For deployment, collect static assets with `python manage.py collectstatic --noinput`.

To send mail through an SMTP provider, set `EMAIL_BACKEND` to
`django.core.mail.backends.smtp.EmailBackend` and configure `EMAIL_HOST`,
`EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`,
`DEFAULT_FROM_EMAIL`, and `CONTACT_RECIPIENT_EMAIL` in the environment. Never
store production mail credentials in source control.

For HTTPS deployment, set `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=false`, and
provide the comma-separated host names in `DJANGO_ALLOWED_HOSTS`. Production mode
requires both settings, redirects HTTP to HTTPS, and enables secure session and
CSRF cookies. HSTS is enabled for one year by default; set `SECURE_HSTS_SECONDS=0`
if HTTPS is not fully configured for the deployment. HSTS subdomain coverage and
preload are intentionally opt-in; enable them only when every affected hostname
is permanently HTTPS-only.

## Verify

```powershell
python manage.py check
python manage.py test app.tests
```
