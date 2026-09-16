# Frontend QA: installed application

Verified against the local Docker Wagtail installation on September 13, 2026.

## Automated and browser checks

- Existing backend page/inquiry suite: **64 tests passed** using a separate test database. System check reported no issues.
- Read-only `tools/check_poundit.py`: all **45 templates compile**; **25 live routes render** with one main landmark, one h1, unique IDs, image alt attributes, design stylesheet, no empty links or broken template/encoding text.
- **29 same-site link targets resolve**, including program/faculty fragment anchors.
- Existing SchoolInquiryForm renders once, preserving labels, CSRF, hidden honeypot, linked errors and invalid-field attributes.
- Event fixtures verify registration visibility for scheduled, past, cancelled, sold-out and postponed states.
- Browser: **75 layout checks** across 15 actual pages at 360, 390, 768, 1024 and 1440px. No horizontal page overflow or observed broken loaded images.
- Pages checked: home, all programs, adult/competitive categories, schedule, faculty, events, important dates, schools, about, contact, waiver, privacy, refunds and terms.
- Desktop home/program discovery and schedule, mobile menu/schedule and error-form screenshots visually reviewed.
- Selecting Wednesday displayed only that day and announced **10 classes shown**.
- Mobile Escape closed navigation, reset aria-expanded and restored focus to Menu.
- JavaScript-free homepage fixture retained visible, usable navigation without horizontal overflow.
- Invalid inquiry fixture focused the error summary and exposed three invalid fields; no real inquiry was submitted.
- Local image rebuild and static collection succeeded; database/media volumes retained.

## Reproduce

From the repository root:

```powershell
docker compose up -d --build --no-deps app
docker compose exec -T app python manage.py test poundit.tests.test_pages poundit.tests.test_inquiries --noinput
docker compose cp tools/check_poundit.py app:/tmp/check_poundit.py
docker compose exec -T app python /tmp/check_poundit.py
```

The optional `--preview-dir /app/static/poundit/qa` flag creates disposable form-error, no-JS and event-archive HTML for local browser inspection. It does not create or modify pages/inquiries. Wagtail may generate image renditions as part of normal rendering. Test fixtures are not production content.

## Practical limits and content dependencies

- Browser checks used Chromium in Codex. Firefox, Safari, a physical touch device and a screen-reader session were not tested.
- Reduced-motion and print rules are present; OS-level reduced-motion emulation was not performed.
- CMS image rendition syntax compiles, but the Pound It seed currently lacks assigned CMS images. End-to-end focal-point/crop review remains after image import. Real source photography is currently served as local static fallback media.
- Legal pages are empty in the seed. Their frontend fallback points to the existing source waiver/privacy/refund pages; terms directs visitors to contact the studio. Approved legal copy and signature workflow remain editorial/backend work.
- Faculty text and schedule/program records are integrated. Portraits, event content, school narrative, final contact/map/video settings still need completion.
- Inquiry tests passed with Django's test mail backend and mocked failure paths. No live email-delivery test or successful public inquiry was performed.
- Existing environment warnings concern requests/urllib3 and a legacy service-request string comparison. They are outside this frontend change.
- No production deployment or external account configuration was performed.

Earlier prototype fixture checks were superseded by these installed-model checks. Source design differences and image provenance are documented in SOURCE_AUDIT.md.
