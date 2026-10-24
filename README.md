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

Result :

![image](https://github.com/prasadmagdum/Milk-Products-site/blob/531a5a29e4c8747df544f05a005356c85cc8b559/Screenshot%202026-05-04%20212437.png)
