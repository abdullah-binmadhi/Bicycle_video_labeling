Signing & Notarization Guide

This document summarizes commands and CI notes for signing and notarizing macOS `.app` bundles and code-signing Windows artifacts.

macOS (.app) — local signing & notarization (Apple Developer account required)

1) Create an app-specific password and ensure you have a valid Developer ID Application certificate in your keychain.

2) Codesign the app locally:

```bash
# Sign the app (replace TEAM_ID and Identity string)
codesign --deep --options runtime --timestamp --sign "Developer ID Application: Your Name (TEAMID)" "CycleSafe Studio.app"

# Verify signature
codesign --verify --deep --strict --verbose=2 "CycleSafe Studio.app"
```

3) Notarize with notarytool (recommended) or altool:

```bash
# Upload and notarize (notarytool is newer and recommended)
# Configure your Apple developer credentials in a keychain profile or use environment variables
xcrun notarytool submit "CycleSafe Studio.app" --keychain-profile "AC_PASSWORD_PROFILE" --wait

# After notarization, staple the ticket to the app
xcrun stapler staple "CycleSafe Studio.app"
```

CI notes (GitHub Actions):
- Create secrets: `APPLE_ID`, `APPLE_APP_PASSWORD` (app-specific password) and/or configure `notarytool` keychain profiles.
- Avoid committing P12/PFX files to the repo. If you must sign in CI, store certificates in GitHub Secrets (base64 encoded) and restore them in the workflow (use ephemeral keychain on macOS runner).

Example signing step (macOS job) snippet:

```yaml
- name: Import signing certificate
  run: |
    echo "$P12_BASE64" | base64 --decode > signing.p12
    security create-keychain -p password build.keychain
    security import signing.p12 -k ~/Library/Keychains/build.keychain -P "$P12_PASS" -T /usr/bin/codesign
    security list-keychains -s ~/Library/Keychains/build.keychain
  env:
    P12_BASE64: ${{ secrets.MY_P12_B64 }}
    P12_PASS: ${{ secrets.MY_P12_PASS }}

- name: Codesign and notarize
  run: |
    codesign --deep --options runtime --timestamp --sign "$CERT_NAME" "CycleSafe Studio.app"
    xcrun notarytool submit "CycleSafe Studio.app" --keychain-profile "AC_PASSWORD_PROFILE" --wait
    xcrun stapler staple "CycleSafe Studio.app"
  env:
    # secrets for notarytool or APPLE_ID/APP_SPECIFIC_PASSWORD
    APPLE_ID: ${{ secrets.APPLE_ID }}
    APP_SPECIFIC_PASSWORD: ${{ secrets.APP_SPECIFIC_PASSWORD }}
```

Windows (.exe / installer) — code signing

1) Obtain a code signing certificate (PFX) from a trusted CA.
2) Locally sign with `signtool` (Windows SDK) or `osslsigncode`:

```powershell
# Using signtool
signtool sign /fd SHA256 /a /f "yourcert.pfx" /p <PFX_PASSWORD> "Path\To\Your.exe"

# Verify
signtool verify /pa /v "Path\To\Your.exe"
```

CI notes for Windows signing:
- Store the PFX as a base64-encoded secret (e.g., `WINDOWS_PFX_B64`) and password in secrets.
- In the workflow restore the PFX and sign the built artifacts using `osslsigncode` or `signtool` if the runner has Windows SDK installed.

General recommendations

- Use GitHub Actions with separate jobs per platform (macos-latest, windows-latest) to produce platform-native artifacts.
- Keep signing credentials in repo secrets and import them into ephemeral keychains or temporary files during the workflow.
- For distribution on macOS, notarize the `.app` so users don't get Gatekeeper warnings.

If you want, I can add a sample GitHub Actions signing job that demonstrates importing a macOS P12 from secrets and running `codesign` + `notarytool` as a follow-up.
