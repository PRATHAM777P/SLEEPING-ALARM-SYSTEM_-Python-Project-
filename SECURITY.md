# 🔒 Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | ✅ Active  |
| 1.x     | ❌ EOL     |

---

## 📸 Privacy & Data Handling

This project processes **live webcam video** on-device. Please understand:

| Data | Where it goes | Persisted? |
|------|---------------|------------|
| Webcam frames | Processed in RAM only | ❌ No |
| Face / eye regions | Processed in RAM only | ❌ No |
| Sleep-event snapshots | `snapshots/` folder on **your machine** | ✅ Yes (local) |
| Session logs | `logs/` folder on **your machine** (JSON Lines) | ✅ Yes (local) |

> **No data is ever transmitted to any server, cloud service, or third party.**
> The project is entirely offline.

### Important: snapshots contain face images
The `snapshots/` directory is listed in `.gitignore`. **Do not commit it.**
If you fork or share the repository, verify that no `snapshots/` images are
accidentally staged.

---

## 🛡️ What this project does NOT do

- ❌ Does not record or store continuous video
- ❌ Does not send any data over the network
- ❌ Does not require API keys or cloud credentials
- ❌ Does not access microphone, GPS, or any other sensor
- ❌ Does not read environment variables or system information

---

## 🚨 Reporting a Vulnerability

If you discover a security issue (e.g., a dependency with a known CVE,
an unintended data-leak path, or an injection vector), please report it
**privately** before opening a public issue:

1. **Email**: `your-email@example.com` (replace with your real address)
2. **Subject**: `[SECURITY] Sleeping Alarm System — <brief description>`
3. Include steps to reproduce and the potential impact.

We aim to respond within **5 business days** and release a patch within
**14 days** of confirmation.

Please **do not** open a public GitHub issue for security vulnerabilities —
use private disclosure instead.

---

## 🔐 Dependency Security

Dependencies are pinned in `requirements.txt`. To audit them:

```bash
pip install pip-audit
pip-audit -r requirements.txt
```

To check for known CVEs in OpenCV or NumPy:

```bash
pip install safety
safety check -r requirements.txt
```

---

## 🧱 Recommended Hardening

| Recommendation | Reason |
|----------------|--------|
| Run in a virtual environment (`venv`) | Isolates dependencies |
| Do not run as root/admin | Limits blast radius |
| Keep `snapshots/` out of version control | Contains face images |
| Rotate logs periodically | Avoids unbounded disk growth |
| Pin dependencies in CI | Prevents supply-chain surprises |

---

*Last updated: 2025*
