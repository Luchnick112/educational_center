# Helper Mobile

Mobile client for the Educational Center API, built with Ionic Vue and Capacitor.

## Local development

```powershell
cd mobile
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

The development server runs on `http://127.0.0.1:5174` and proxies `/api` to
`http://127.0.0.1:8000`. Leave `VITE_API_URL` empty to use the proxy, or set it
to a reachable API origin when testing on another device.

## Checks

```powershell
npm.cmd run type-check
npm.cmd run build
```

## Native platforms

Capacitor is configured in `capacitor.config.ts`. The Android project is stored
in `android/`; iOS has not been generated because iOS builds require macOS and
Xcode.

Authentication tokens use Android Keystore/iOS Keychain through
`@aparajita/capacitor-secure-storage`. Browser development keeps a localStorage
fallback.

After web changes, update the native project with:

```powershell
npm.cmd run build
npm.cmd run cap:sync
```
