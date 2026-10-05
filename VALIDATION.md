# Validation record

## Public client-showcase website

The later client-presentation website is independent of the Python system.
On October 5, 2026, its Vite production build and strict TypeScript check passed,
and all **9 frontend tests** passed. A local production preview served HTTP 200.
See [WEBSITE.md](WEBSITE.md) for website deployment, capabilities and validation limits.

The website deliberately uses fictional records and simulated face verification;
it has no camera capture, biometric collection, live backend or customer accounts.

## Python application

Verified in this workspace on **5 October 2026**.

| Check | Result |
| --- | --- |
| Python runtime | Project-local CPython 3.11.15 |
| Dependency installation | All 44 packages installed; direct versions in requirements.txt, resolved environment in requirements-lock.txt |
| Source compilation | Passed for app, config, database, face, services, UI, utilities, scripts and tests |
| Automated suite | **25 passed** in 34.64 seconds |
| Official YuNet and SFace model downloads | Both SHA-256 values verified |
| Actual model execution | YuNet blank-frame detection/rejection, landmark alignment and SFace 128-dimensional inference passed |
| Streamlit application tests | Kiosk startup, guarded admin routes, login, registration page, admin list and populated dashboard passed |
| Dashboard outputs | Four chart types, table, CSV control and search filtering exercised by Streamlit AppTest |
| HTTP server | Started on 127.0.0.1:8501; /_stcore/health returned HTTP 200 with `ok` |
| Application database | Empty data/attendance.db initialized; no people or fake attendance seeded |

## Environment details

The existing Python 3.11 launcher entry referenced a missing executable. A Python
3.11 runtime and virtual environment were installed inside the project using uv;
the system Python 3.14 installation was not modified. Model and package downloads
required network-enabled execution.

The initial sandboxed pytest run passed 15 tests; 10 tests could not create
temporary directories because of Windows access restrictions. Rerunning the full
suite with workspace-local temporary files outside that sandbox restriction
produced **25 passed**. These were environment errors, not assertion failures.

Commands used:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe scripts/check_models.py
.\.venv\Scripts\python.exe -m compileall -q app.py config database face services ui utils scripts tests
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true
Invoke-WebRequest http://127.0.0.1:8501/_stcore/health -UseBasicParsing
```

## Not verified

- Physical webcam access, permissions, live enrollment and human challenge completion.
- Real-face accuracy, false acceptance/rejection, demographic performance or deliberate spoof resistance.
- Pixel-level browser review: no browser automation surface was available; AppTest checked UI rendering and interactions programmatically.
- Remote deployment, multiple kiosks, encrypted storage or formal security assessment.

Synthetic model inputs check execution only, not recognition quality. Complete
the manual camera acceptance checklist in README.md before demonstrating or
deploying the application. Basic head-turn liveness is not certified anti-spoofing.

No administrator password was chosen for the user. Run `scripts/setup_admin.py`
locally before using the protected pages.
