# News Application Capstone Project

A secure, role-based news management and dissemination platform built with Django, Django REST Framework (DRF), and MariaDB. The application incorporates fine-grained role-based access control (RBAC), automated post-save signal hooks, an interactive editorial approval pipeline, reader subscription feeds, and developer REST endpoints.

---

## 🌟 Special Features & Technical Architecture

### 1. Robust Role-Based Access Control (RBAC) & Mutual Exclusivity
The platform models three distinct operational roles with strict domain separation:
* **Readers**: Browse published articles, manage personalized subscriptions (following specific journalists or publishers), and query custom feeds. Reader accounts are restricted from drafting content.
* **Journalists**: Draft and submit news reports via a dedicated Journalist Desk or REST API endpoints. Articles remain unapproved (`approved=False`) until vetted by editorial staff.
* **Editors & Superusers**: Complete oversight across publications, draft queues, and account moderation. Editors review pending articles and trigger publishing workflows.

Role integrity and group synchronization:
* Mutual exclusivity is enforced at the model level (e.g., editorial and journalist accounts cannot hold reader subscriptions).
* Model-level hooks in `CustomUser.save()` automatically synchronize roles with native Django `Group` permissions.
* A custom management command (`python manage.py setup_roles`) provisions all necessary role groups and permission mappings.

---

### 2. Automated Event-Driven Workflows (Signals & Webhooks)
The application leverages event automation to decouple publication actions from notifications:
* **Django `post_save` Signals**: Attached to the `Article` model to monitor status transitions. When an editor updates an article from `approved=False` to `approved=True`:
  * A structured email alert is automatically dispatched via Django's core mail backend alerting the author of successful publication.
  * An automated internal HTTP `POST` webhook is triggered to `/api/approved/` to notify connected syndication clients of newly approved content.
* **Staff Approval Pipeline**: Staff registrations (Journalist and Editor roles) default to `is_active=False`. Superusers utilize an in-app Account Approval Dashboard to review and activate pending staff members before access is granted.

---

### 3. Dual-Layer Authentication & RESTful Architecture
* **Hybrid Authentication Scheme**: Configured with Django REST Framework's `SessionAuthentication` and `TokenAuthentication` simultaneously:
  * Web clients and browsers interact via CSRF-protected session states.
  * Programmatic external consumers, headless clients, and automated testing suites authenticate statelessly via standard HTTP `Authorization: Token <key>` headers.
* **Interactive Developer & API Portal**: Includes an interactive in-browser Token Generator tool allowing developers to issue credentials via `POST /api/token/` and inspect JSON endpoint payloads (`/api/articles/` and `/api/articles/subscribed/`) directly without external tools.

---

### 4. Technical Architecture Diagram

```
+--------------------------------------------------------------------------+
|                               Browser & Client UI                        |
|  (home.html [extends base.html] | Desk | Feeds | Admin Approval Desk)    |
+--------------------------------------------------------------------------+
                                     |
           +-------------------------+-------------------------+
           | (Session & CSRF Auth)                             | (HTTP Token Auth)
           v                                                   v
+-----------------------+                             +--------------------+
|   Django Web Views    |                             | Django REST API    |
| (views.py / RBAC gate)|                             | (api_views.py)     |
+-----------------------+                             +--------------------+
           |                                                   |
           +-------------------------+-------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |       Model & Data Layer    |
                      |  CustomUser, Publisher,     |
                      |  Article, Newsletter        |
                      +-----------------------------+
                                     |
                                     | (Article.approved -> True)
                                     v
                      +-----------------------------+
                      |      Signal Automation      |
                      |  - post_save Signal         |
                      |  - Console Email Dispatch   |
                      |  - Internal POST Webhook    |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |       Database Storage      |
                      |       (MariaDB / MySQL)     |
                      +-----------------------------+
```

---

## 💻 Tech Stack

* **Backend**: Python 3.14, Django 6.1, Django REST Framework
* **Database**: MariaDB / MySQL (via `mysqlclient` / `pymysql`)
* **Authentication**: Django Session Authentication & DRF Token Authentication
* **Testing & Quality**: Django `APITestCase`, `unittest.mock`, `flake8`, `black`

---

## 🗄️ Database Configuration (MariaDB)

Ensure MariaDB is running locally and execute the following SQL commands to configure the database and user credentials:

```sql
CREATE DATABASE news_application_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON news_application_db.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
```

---

## 🚀 Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/arianmalayery-studio/News_App.git
   cd News_App
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations and seed initial roles**:
   ```bash
   python manage.py migrate
   python manage.py setup_roles
   ```

5. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the local development server**:
   ```bash
   python manage.py runserver
   ```
   Navigate to `http://127.0.0.1:8000/` to explore the platform.

---

## 🧪 Testing & Code Quality

* **Execute Automated Test Suite**:
  ```bash
  python manage.py test news
  ```
  Runs the complete test suite validating model validation, signal delivery, role permissions, and REST endpoints.

* **Run PEP 8 Linter**:
  ```bash
  flake8 news
  ```
  Verifies strict conformance to PEP 8 standards and 79-character line length limits.