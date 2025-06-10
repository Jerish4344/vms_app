# Vehicle Management System – Mobile App

A cross-platform React Native application that lets drivers, managers, and admins access your existing Django-based Vehicle Management System (VMS) from their phones and tablets.

---

## 1. Project Structure

```
mobile_app/
├── android/           # Native Android project (auto-generated)
├── ios/               # Native iOS project (auto-generated)
├── app/               # Source code (screens, components, hooks, services)
├── assets/            # Images, fonts, icons
├── .env.example       # Sample environment variables
├── app.json           # Expo / RN config
└── README.md          # ← you are here
```

---

## 2. Prerequisites

| Tool | Version (recommended) | Notes |
|------|-----------------------|-------|
| Node.js | ≥ 18 LTS | JavaScript runtime |
| npm / Yarn | npm ≥ 9 or Yarn ≥ 1.22 | Package manager |
| Expo CLI *or* React Native CLI | Expo `npm i -g expo-cli` | Easiest way to run/debug |
| Android Studio | latest | Android emulator & SDK |
| Xcode (macOS only) | ≥ 15 | iOS simulator & build tools |
| Watchman (macOS) | optional | Faster file watching |

> You **don’t** need Android Studio/Xcode when using physical devices with Expo Go.

---

## 3. Getting Started

```bash
# 1. Clone the repository (or pull latest)
git clone https://github.com/your-org/vms.git
cd vms/mobile_app

# 2. Install dependencies
# choose ONE of the package managers
npm install        # – or –  yarn install

# 3. Copy env variables and configure
cp .env.example .env
```

Then edit `.env`:

```
API_BASE_URL=https://your-domain.com/api/v1
# If you use http on LAN you may need: http://192.168.x.x:8000/api/v1
```

You can add other vars (e.g., `GOOGLE_MAPS_KEY=`) as the code evolves.

---

## 4. Running the App

### 4.1 Expo workflow (recommended)

```bash
# Start Metro bundler + Expo dev server
npm run dev          # alias for: expo start
```

* Scan the QR code with **Expo Go** on Android/iOS.
* Press **a** to open Android emulator, **i** for iOS simulator.

### 4.2 React Native CLI (bare) workflow

```bash
# Android
npm run android      # npx react-native run-android

# iOS – macOS only
npm run ios          # npx react-native run-ios
```

> The first build is slow; subsequent starts are faster.

---

## 5. Authentication

1. Users obtain a token from the Django endpoint  
   `POST /api/v1/token-auth/` with `{ username, password }`.
2. The token is stored securely (AsyncStorage / Keychain).  
3. All API calls include header:  
   `Authorization: Token <token>`.

Tokens expire after **7 days** by default (see `TOKEN_EXPIRY_DAYS` in Django `settings.py`).

---

## 6. Build & Release

### Android (APK/AAB)

```bash
# Generate a release build (Gradle)
cd android
./gradlew assembleRelease    # APK
./gradlew bundleRelease      # AAB
```

### iOS (App Store / TestFlight)

```bash
cd ios
# Update pods
pod install
# Release build
xcodebuild -workspace mobile_app.xcworkspace -scheme mobile_app -configuration Release
```

Or use EAS Build (Expo) for cloud builds.

---

## 7. Linting & Formatting

```bash
npm run lint     # ESLint
npm run format   # Prettier
```

Continuous integration hooks can be added later.

---

## 8. Troubleshooting

| Issue | Fix |
|-------|-----|
| _Metro bundler stuck at 99%_ | Clear cache: `expo start -c` |
| _Network request failed_ | Ensure phone & backend on same LAN / correct `API_BASE_URL` |
| _iOS build fails “Pods not found”_ | `cd ios && pod install && cd ..` |
| _Invalid token_ | Re-login or increase `TOKEN_EXPIRY_DAYS` on the backend |

---

## 9. Contributing

1. Create a branch: `git checkout -b feature/my-feature`.
2. Follow the project ESLint/Prettier rules.
3. Open a PR with clear description and screenshots/GIFs.

---

## 10. License

Copyright © 2025  
Released under the MIT License.
