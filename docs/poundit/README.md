# Pound It design: installed Wagtail frontend

The design is connected to the installed `poundit` app in Alternative-Naissance. The public root uses `PounditHomePage`, and all Pound It page types now share the black/yellow design, navigation, responsive layouts and typography. Programs, schedules, faculty and calendar entries render the backend's actual records.

## Apply or refresh the local installation

From the repository root:

```powershell
docker compose up -d --build --no-deps app
```

Open http://localhost:8000/ and hard-refresh if necessary. The Dockerfile copies templates and assets into the image and runs `collectstatic`, so workspace edits need a rebuild. This command recreates the app service and retains the database/media volumes. The design has already been rebuilt into the local installation.

Use http://localhost:8000/admin/ to edit Pound It pages, snippets and Pound It settings. Frontend integration adds no migrations or package dependencies. The original maternity homepage template has been restored because Pound It now has its own page class; the backend's separate site configuration controls which page tree is served.

## Active templates

| Model | Template and behavior |
| --- | --- |
| PounditHomePage | `home_page.html`: editorial hero, category discovery, live featured programs/faculty, upcoming events/dates |
| ProgramIndexPage | `program_index_page.html`: real category routes, structured prices and schedules, expandable complete class details |
| FacultyIndexPage | `faculty_index_page.html`: regular/occasional faculty, biographies, styles and social links |
| SchedulePage | `schedule_page.html`: days and named rooms, text labels with training colors, optional day filter |
| EventIndexPage | `event_index_page.html`: type filters, upcoming events and archive |
| EventPage | `event_page.html`: uncropped poster, date/time/venue/price, status-aware registration |
| ImportantDatesPage | `important_dates_page.html`: category filters, month groups, tentative/past labels |
| SchoolProgramsPage | `school_programs_page.html`: residency facts, one existing Django inquiry form and confirmation state |
| ContentPage | `content_page.html`: editorial/legal content and child navigation; current source policy links until legal copy is populated |

Programs and faculty are snippets, so details live at stable fragments on their index pages, not invented detail-page routes. Older standalone detail-template drafts are not routed by the installed backend.

The shell is `templates/poundit/base.html`. Reusable active components include header/footer, announcement, page hero, responsive image, program/faculty/event cards, training key and form layout. All six backend StreamField blocks have styled templates in `templates/poundit/blocks/`.

## Design system

| Item | Value |
| --- | --- |
| Ink / black | #131514 / #000000 |
| Yellow | #FEFF01 |
| White / paper | #FFFFFF / #EFF0EB |
| Functional red / green | #ED1C24 / #1C7D33 |
| Typography | Locally hosted OFL Anton; Arial/Helvetica body |
| Spacing | .25, .5, .75, 1, 1.5, 2, 3, 4, 6rem |
| Container / reading width | 1320px / 72ch |
| Corners | Square |
| Responsive widths checked | 360, 390, 768, 1024, 1440px |

CSS: `alternative_naissance/static/poundit/poundit.css`.
JavaScript: `alternative_naissance/static/poundit/poundit.js`.
No frontend framework, build tooling, autoplay, tracking or animation dependency was added.

Training identifiers map to black (crew), yellow (ages 6-9), red (ages 10-15), and green (PIBA/open). Additional toddler/young-child levels use a neutral marker. Every color has a text label.

## Editable content and remaining editorial work

- Headings, descriptions, season announcements, prices, times, biographies, dates and action URLs come from the actual page/snippet/settings fields.
- The logo and editorial photography use audited source assets as static fallbacks. Wagtail hero, program, faculty and event images take precedence where those fields exist. Imported Pound It images and focal points still need completion; no faculty portraits are attached in the current seed.
- The backend has no fields for the homepage's category photos and culture-story images/copy. Those source-based editorial sections remain in templates; see BACKEND_CONTRACT.md for optional field additions.
- The seeded legal pages are empty. The UI links to the current source waiver/privacy/refund pages until approved copy is populated; it does not invent legal text or capture signatures.
- School residency descriptive copy and the studio public email/maps/video settings still need editorial completion. Inquiry persistence and notification behavior remain the backend's responsibility. The seed notes that an email recipient must be configured.
- Upcoming events render when supplied; the current seed has no upcoming event records. Calendar dates remain explicitly marked tentative where the data says so.

The source audit and asset provenance are in [SOURCE_AUDIT.md](SOURCE_AUDIT.md), the installed field mapping in [BACKEND_CONTRACT.md](BACKEND_CONTRACT.md), and verification/limits in [QA.md](QA.md). No production deployment was performed.
