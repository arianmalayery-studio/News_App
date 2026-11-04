# News Application Capstone Project

A secure, role-based news management and dissemination platform built with Django, Django REST Framework (DRF), and MariaDB.

---

## Features

- **Custom Role-Based Access Control (RBAC)**: Supports `READER`, `EDITOR`, and `JOURNALIST` roles with mutually exclusive subscriptions.
- **Automated Permission Syncing**: Custom management command (`setup_roles`) and model-level hooks (`CustomUser.save()`) synchronize roles with Django Auth Groups and Permissions.
- **Editor Review Pipeline**: Dedicated template-driven dashboard for editors to review pending drafts and approve articles for publication.
- **Signal Automation**: Django `post_save` signals automatically dispatch console email notifications to subscribed readers and trigger an internal HTTP POST webhook to `/api/approved/`.
- **RESTful API**: Comprehensive API supporting Token Authentication, role-based method permissions, article curation, and subscription-filtered feeds.
- **Automated Test Coverage**: Full `APITestCase` suite with mocks for outbox emails and HTTP requests.
- **PEP 8 Compliance**: Enforces clean imports, docstrings, and strict 79-character line length limits via `flake8`, `black`, `autopep8`, and `autoflake`.

---

## Tech Stack

- **Backend**: Python 3.14, Django 6.1, Django REST Framework
- **Database**: MariaDB / MySQL (via `mysqlclient` / `pymysql`)
- **Authentication**: Django Session Auth & DRF Token Authentication
- **Testing & Quality**: Django `APITestCase`, `unittest.mock`, `flake8`, `black`

---

## Database Configuration (MariaDB)

Ensure MariaDB is running locally and execute the following SQL commands to create the database and user:

```sql
CREATE DATABASE news_application_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON news_application_db.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
