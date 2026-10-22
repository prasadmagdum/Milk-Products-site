# Magdum Dairy

A Django storefront for Magdum Dairy products in Kolhapur. Customers can browse
and search products, manage a cart and wishlist, save delivery addresses, and
place cash-on-delivery orders. Staff can manage products, orders, and contact
messages in Django admin.

![Magdum Dairy storefront](Screenshot%202026-05-04%20212437.png)

## Run locally

Requirements: Python 3.10+, Django 4.2, and Pillow.

From the repository root in PowerShell:

```powershell
Set-Location .\ec
python -m pip install "Django>=4.2,<5.0" Pillow
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Sign in at `/admin/` to add products, set prices,
and manage orders and contact messages. Uploaded product images are stored in
`ec/media/`.

In development, password reset emails are printed to the runserver console.

## Production configuration

Do not use the local SQLite database, development secret, console email backend,
or Django's development server for a production deployment. Set these
environment variables in the hosting provider's secret/configuration manager:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY` to a newly generated, private Django secret
- `DJANGO_ALLOWED_HOSTS` to comma-separated production hostnames
- `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`, and `DJANGO_DEFAULT_FROM_EMAIL`
- `DJANGO_EMAIL_HOST_USER` and `DJANGO_EMAIL_HOST_PASSWORD` when required by
  the SMTP provider
- `DJANGO_EMAIL_USE_TLS=true` or `DJANGO_EMAIL_USE_SSL=true`, as required by the
  provider (do not enable both)
- `DJANGO_HSTS_INCLUDE_SUBDOMAINS=true` only if all subdomains are HTTPS-only
- `DJANGO_HSTS_PRELOAD=true` only after meeting browser preload requirements;
  this also requires HSTS subdomains and a one-year max-age

The production settings require an explicit secret and allowed hosts, redirect
HTTP to HTTPS, use secure session and CSRF cookies, and enable HSTS for one
hour by default. Configure a durable
production database, persistent media storage, SMTP credentials, and a static
file server for `ec/staticfiles/` before deploying. Apply migrations and run
`python manage.py collectstatic` as part of deployment.

The HSTS subdomain and browser-preload options are intentionally disabled by
default. Enable them only after confirming that every relevant subdomain is
HTTPS-only and you are ready for the long-lived browser policy.

## Verify

```powershell
Set-Location .\ec
python manage.py check
python manage.py test app.tests
```
