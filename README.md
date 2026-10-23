# Student Skill & Career Readiness Analysis System

A Flask + SQLite self-assessment app. A student picks a target career role,
rates their skills 1–5, logs projects as evidence, and sees a dashboard with
category averages, gaps, and rule-based next actions.

Self-assessment only. It is **not** an employability prediction or hiring tool.

Delivery snapshot: open [`status-dashboard.html`](status-dashboard.html) for completion status, test evidence, and open items.

## Stack
- Python + Flask
- SQLite (parameterized queries, foreign keys enforced)
- Server-rendered Jinja templates, plain CSS, minimal vanilla JS
- Chart.js (category averages only)

## Requirements
- Python 3.10+

## Setup

```bash
cd student-career-readiness
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Initialize the database

```bash
python database/seed.py
```

This creates `database/career_readiness.db` and seeds 3 roles (Python
Developer, Web Developer, Data Analyst), 20 skills, and their target ratings.

Re-running is safe (uses `INSERT OR IGNORE`).

## Run the app

```bash
source venv/bin/activate
python app.py
```

Open http://127.0.0.1:5000

Flow: Register → Profile (pick a target role) → Assessment → Dashboard →
Projects → History (reassess later to compare).

## Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
python -m pytest tests/ --cov=services --cov-report=term-missing
```

## Project structure

```
student-career-readiness/
├── app.py                      Flask app: routes, session, access control
├── requirements.txt
├── database/
│   ├── schema.sql              Tables, FKs, CHECK constraints
│   └── seed.py                 Roles, skills, role-skill targets
├── services/
│   ├── auth.py                 Register/login, profile, projects
│   ├── scoring.py              Gaps, category averages, readiness %
│   └── recommendations.py      Rule-based recommendations
├── templates/                  base, login, register, profile,
│                               assessment, dashboard, projects, history
├── static/css/style.css        Neutral flat UI, single accent
├── static/js/dashboard.js      Chart.js category bar chart
├── status-dashboard.html       Build/verification status snapshot
├── tests/                      auth, scoring, recommendations, integration
└── android-wrapper/            Optional Android WebView shell
```

## Rules encoded in the app

- Gap = target − your rating. Gap > 0 = below target.
- Category average = mean of rated skills only. Unrated skills are
  "Not assessed" and excluded. No ratings → friendly message, no divide-by-zero.
- Readiness % = (mean of category averages / 5) × 100. Always shown next to
  the gap breakdown, never alone.
- Recommendations are plain if/else rules; each is traceable to the skill gap
  that triggered it.
- Assessments are append-only. No edit/delete.
- Every query is scoped to the logged-in student. A student cannot read another
  student's data.

## Not included (by design)

Admin role, certifications, resume parsing, job matching, AI recommendations,
public rankings, multi-college features, editing past assessments.

## Optional Android wrapper

`android-wrapper/` is a thin WebView shell around the deployed Flask app, not a
native rewrite.

```bash
cd android-wrapper
./gradlew assembleDebug           # app/build/outputs/apk/debug/app-debug.apk
./gradlew assembleRelease         # signed app/build/outputs/apk/release/app-release.apk
```

- `appUrl` defaults to `https://your-app.onrender.com`. Override at build time:
  `./gradlew assembleDebug -PappUrl=https://your-deployment.example.com`
- Cleartext HTTP is off (`android:usesCleartextTraffic="false"`), so point it at
  an HTTPS deployment.
- A failed main-frame load shows a retry screen instead of a blank WebView.
- Release signing reads `android-wrapper/keystore.properties` (gitignored).
  Create your own keystore for a production build:

  ```bash
  keytool -genkeypair -keystore my-release.jks -alias careerreadiness \
    -keyalg RSA -keysize 2048 -validity 10000
  ```

  Then write `keystore.properties` with `storeFile`, `storePassword`,
  `keyAlias`, and `keyPassword`. Without that file, release builds are unsigned.
- A local demo keystore (`demo-release.jks`) is gitignored and was used to
  produce the verified test APK; do not ship it to a store.

