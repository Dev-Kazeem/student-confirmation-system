# Student Confirmation & Document Verification System

**Usmanu Danfodiyo University, Sokoto**

An enhanced web-based platform for online student confirmation and document
verification. Newly admitted students can complete confirmation activities
online, upload required documents, track their application status, and download
a verifiable digital confirmation slip. Admission officers can review
applications, verify documents, and approve or reject them. Administrators can
manage users, departments, programmes, admission sessions, and audit logs.

---

## Status

This repository currently contains **Phase One: Project Setup**. Later phases
add models, authentication, admission checking, document upload, officer
review, notifications, confirmation slips, reports, audit logs, and tests.

| Phase | Description                                   | Status |
|-------|-----------------------------------------------|--------|
| 1     | Project setup, base templates, custom User    | ✅ Done |
| 2     | Database models & migrations                  | ⏳ Next |
| 3     | Authentication & roles                        | ⏳      |
| 4     | Admission records & student profile           | ⏳      |
| 5     | Application & document management             | ⏳      |
| 6     | Officer review workflow                       | ⏳      |
| 7     | Notifications & confirmation slips            | ⏳      |
| 8     | Reports, search, audit logs, security review  | ⏳      |
| 9     | Testing, UI polish, deployment, documentation | ⏳      |

---

## Technology Stack

- **Backend:** Python 3.12, Django 5.0
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons
- **Database:** SQLite (development), PostgreSQL (production)
- **Static files:** WhiteNoise
- **Media (production):** Cloudinary (Phase 7)
- **Config:** python-decouple, dj-database-url
- **Email:** console backend (dev), SMTP (prod)

---

## Project Structure
