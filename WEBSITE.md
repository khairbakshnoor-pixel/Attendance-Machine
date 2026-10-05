# FaceTrack — client showcase website

A polished, responsive marketing website with an interactive attendance dashboard,
built for presenting the FaceTrack concept to prospective clients.

**This website is a public product showcase, not a live biometric service.**
It runs entirely in the browser with clearly labeled fictional data. No password,
backend, database, camera permission, or paid service is needed to run it.

## Run locally

Use Node.js 22 or newer:

```powershell
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://127.0.0.1:5173).

```powershell
npm run build
npm run preview
npm test
```

## Upload to GitHub, then deploy to Vercel

The `facetrack-website.zip` delivery contains only the website source and setup files.
Extract it, upload the extracted contents to your GitHub repository, and import that
repository in Vercel. Do not upload the ZIP itself as your repository's source.

Use these settings:

| Vercel setting | Value |
| --- | --- |
| Framework preset | Vite |
| Root directory | Repository root (`./`) |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Output directory | `dist` |
| Required environment variables | None |

`vercel.json` is already included with the build configuration, SPA fallback and
basic security headers. The website works on Vercel's default HTTPS domain.
GitHub upload and deployment are left to you, as requested.

Official Vercel instructions: https://vercel.com/docs/frameworks/frontend/vite

## Optional branding and sales contact

For local development, copy `web/.env.example` to `.env.local` in the project root:

```powershell
Copy-Item web/.env.example .env.local
```

Then edit:

```dotenv
VITE_COMPANY_NAME=YourBrand
VITE_CONTACT_EMAIL=your-sales-address@example.com
```

Set your real sales address before enabling the email CTA. With an empty email
setting, the sales contact link is hidden. No fake form submission or made-up
contact destination is used. In Vercel, add these same optional environment
variables and redeploy. All `VITE_*` values are public; never put secrets in them.

To change the browser title/description, edit `index.html`. To replace the icon,
edit `public/favicon.svg`. The remaining product copy is in `web/src/Landing.tsx`.

## What clients can explore

- Responsive landing page with an original illustrated attendance card.
- Overview dashboard with calculated sample metrics and a sample trend chart.
- Attendance search by name or ID, date filtering and check-in/check-out filtering.
- CSV export of the currently filtered sample attendance, with spreadsheet-formula escaping.
- People directory with search and a modal for adding a **fictional** team member.
- Simulated check-in/check-out sequence that updates the sample attendance table.
- Duplicate sign-in prevention, sign-out-before-sign-in prevention and repeat sign-out prevention in the demo.
- Workspace name personalization for presentations.
- Reset demo, mobile navigation, keyboard-accessible native dialog and reduced-motion styling.

The sample date is deliberately fixed to **October 5, 2026** and labeled as a sample
day so the presentation is reproducible. People and attendance changes live only
in React state and disappear on refresh. The trend chart is labeled illustrative.
The simulated camera station is an animation, not face recognition.

## Website files

```text
index.html                 Metadata and application entry point
package.json               Development/build/test commands
package-lock.json          Resolved dependency versions
tsconfig.json              Strict TypeScript configuration
vite.config.ts             Vite + React build configuration
vercel.json                Vercel deployment and headers
public/favicon.svg         Original product icon
web/.env.example           Optional branding/contact template
web/src/main.tsx           React entry point
web/src/App.tsx            Interactive demo dashboard and dialogs
web/src/Landing.tsx        Public marketing site and product illustration
web/src/styles.css         Responsive layout, styling and reduced motion
web/src/demo.ts            Fictional data and sample attendance rules
web/src/api.ts             Shared types, brand setting and safe CSV utilities
web/src/demo.test.ts       Attendance/filter/export regression tests
web/src/render.test.tsx    Landing and demo rendering checks
```

No external fonts, analytics, trackers, stock images, or remote API calls are
required. The hero illustration is drawn in CSS; no real face photos are bundled.

## Validation completed

On October 5, 2026, `npm run build` passed TypeScript checking and generated the
production bundle. `npm test` passed all **9 tests** covering sample attendance
rules, filters, CSV escaping, and landing/dashboard rendering. The production
preview returned HTTP 200 locally. The source-only ZIP was integrity-checked.

No connected browser automation surface was available for a pixel-level visual
review. Responsive layouts are implemented at mobile, tablet and desktop
breakpoints; review the preview on your target devices before showing clients.
No GitHub upload or live Vercel deployment was performed.

## Relation to the existing Python application

The full workspace also contains the earlier Python/Streamlit recognition system.
The showcase does not connect to it or read its database. `.vercelignore` excludes
Python environments, models, biometric data and unrelated files from the website
deployment. `.gitignore` excludes local secrets, dependencies and data.

A future live product will require an authenticated backend, real browser-camera
integration, validated anti-spoofing, appropriate data protection, operational
monitoring and customer-specific deployment work. The website does not claim
that this production integration or a SaaS subscription system has been delivered.
