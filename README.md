# Vehicle Management System (VMS)

A **Django + React Native** solution that lets fleets manage vehicles, trips, fuel, maintenance and documents from **web** and **mobile**.

This repository now contains **two runnable parts**:

```
├── backend/                # Django project (folder name: VMS)
│   └── vehicle_management/ … 
└── mobile_app/             # React Native (Expo) application
```

---

## 1. Prerequisites

| Tool | Version | Used by |
|------|---------|---------|
| Python | 3.10 – 3.13 | Backend |
| MySQL | 5.7 / 8 | Backend DB |
| Node.js | ≥ 18 LTS | Mobile |
| npm / Yarn | npm ≥ 9 or Yarn ≥ 1.22 | Mobile |
| Expo CLI | `npm i -g expo-cli` | Mobile (dev + build) |
| Android Studio | latest | Android build / emulator |
| Xcode (macOS) | ≥ 15 | iOS build / simulator |

---

## 2. Backend ‑ Django REST API

### 2.1. Clone & create a virtual-env

```bash
git clone https://github.com/your-org/vms.git
cd vms/backend      # the folder that has manage.py
python -m venv env
source env/bin/activate   # Windows: env\Scripts\activate
```

### 2.2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> Requirements already include **Django 4**, **djangorestframework**, **mysql-connector-python**, **django-rest-framework-authtoken** and more.

### 2.3. Configure environment variables (optional)

The sample project is wired for local MySQL with user `root` / password `root@2001`.  
Override any setting via **`.env`** or shell:

```bash
export DJANGO_SECRET_KEY="change-me"
export DB_NAME="vms_db"
export DB_USER="myuser"
export DB_PASSWORD="mypassword"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
```

You can also switch to PostgreSQL by editing `DATABASES` in `settings.py`.

### 2.4. Database migrations & superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 2.5. Run development server

```bash
python manage.py runserver 0.0.0.0:8000
```

Open:

* Admin site – http://localhost:8000/admin  
* Browsable API – http://localhost:8000/api/v1/

### 2.6. Generate an auth token for a user (optional)

```bash
python manage.py drf_create_token <username>
```

Tokens **expire after 7 days** (`TOKEN_EXPIRY_DAYS` in `settings.py`).

### 2.7. Running tests & linting

```bash
pytest                 # if you add tests
flake8                 # style check
```

---

## 3. Mobile App – React Native (Expo)

### 3.1. Install JS deps

```bash
cd mobile_app
npm install          # or: yarn install
```

### 3.2. Environment variables

Copy the sample and edit:

```bash
cp .env.example .env
```

Key setting:

```
API_BASE_URL=http://<your-LAN-IP>:8000/api/v1
```

When the backend runs on another machine / Docker / cloud, point to its public URL (HTTPS in production).

### 3.3. Start in development

```bash
npm run dev          # alias for: expo start
```

* Scan the QR with **Expo Go** on your phone **OR**
* Press **a** for an Android emulator / **i** for iOS simulator.

### 3.4. Offline support

The app queues **POST/PUT/PATCH/DELETE** requests when offline and re-sends them once connectivity returns (see `app/services/apiService.js`). A red banner warns when the device is offline.

### 3.5. Building binaries

| Platform | Command |
|----------|---------|
| Android APK (local) | `cd android && ./gradlew assembleRelease` |
| Android AAB | `./gradlew bundleRelease` |
| iOS | open `ios/` workspace in Xcode → Archive |
| EAS Build (cloud) | `eas build --platform android|ios` |

> You can keep using **Expo Go** during development; no native build needed until release.

---

## 4. Project Structure (high-level)

```
backend/
├── accounts/          # Custom user model, auth backends
├── vehicles/          # Vehicle CRUD, model, admin
├── trips/             # Trip lifecycle & logic
├── maintenance/       # Maintenance records
├── fuel/              # Fuel transactions
├── geolocation/       # Location logs & update endpoint
├── api/               # NEW: mobile-friendly REST API (v1)
└── vehicle_management/settings.py  # global config

mobile_app/
├── app/
│   ├── screens/       # Dashboard, Vehicles, Trips…
│   ├── components/    # Re-usable UI widgets
│   ├── services/      # apiService (Axios)
│   ├── context/       # Auth & Network contexts
│   └── store/         # Redux Toolkit slices
├── assets/            # Icons, splash, fonts
└── app.json           # Expo config
```

---

## 5. REST API Cheat-Sheet

| Resource | Endpoint | Notes |
|----------|----------|-------|
| Auth token | `POST /api/v1/token-auth/` | `{ "username": "...", "password": "..." }` |
| Current user | `GET /api/v1/users/me/` | Requires `Authorization: Token xxx` |
| Vehicles | `/api/v1/vehicles/` | Full CRUD |
| Trips | `/api/v1/trips/` | Actions: `end_trip/`, `cancel_trip/` |
| Maintenance | `/api/v1/maintenance/` | — |
| Fuel | `/api/v1/fuel/` | Image upload supported |
| Location | `/api/location/update/` | From mobile GPS |

Explore with the **browsable API** or import the **Postman collection** (provided separately).

---

## 6. Deployment Tips

* Put Django behind **Gunicorn + Nginx** or **uWSGI**.
* Use **PostgreSQL** in production.
* Point `STATIC_ROOT` & `MEDIA_ROOT` to object storage (S3, GCS).
* Serve the mobile app through **Expo EAS Update** or distribute via stores.

---

## 7. Troubleshooting

| Problem | Fix |
|---------|-----|
| `django.core.exceptions.ImproperlyConfigured: Error loading MySQLdb` | `pip install mysqlclient` or stay with `mysql-connector-python` |
| **Mobile** “Network request failed” | Ensure phone & backend are on same LAN and API URL is correct |
| Token expires too quickly | Increase `TOKEN_EXPIRY_DAYS` in `settings.py` |
| iOS build fails “Pods not installed” | `cd ios && pod install` |
| Expo stuck at 99 % | `expo start -c` (clear cache) |

---

## 8. Contributing

1. Fork → create a feature branch: `git checkout -b feature/my-feature`.
2. Follow **PEP 8** & **ESLint/Prettier**.
3. Add/ update tests.
4. Open a Pull Request with description & screenshots/GIFs.

---

## 9. License

This project is released under the **MIT License** – see `LICENSE` file for details.

Happy hacking! 🚗📱
