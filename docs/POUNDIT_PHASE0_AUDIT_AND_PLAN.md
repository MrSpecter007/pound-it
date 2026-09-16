# Pound It Hip Hop Studio — Phase 0
## Repository Audit, Source Inventory, and Implementation Plan

**Target repo:** `Alternative-Naissance` (Wagtail 7.0 / Django 5.2.2 / Python 3.12 / PostgreSQL 16)
**Source site:** https://www.pounditdj.com/ (Wix)
**Owner of this document:** Claude (data/architecture). Codex consumes §8 (Template Contract).
**Status:** Awaiting review. No code has been written. No files in the repo have been modified.

---

## 1. Repository Audit

### 1.1 Installed apps

Local apps: `search`, `core`, `servicerequests`, `emails`.
Wagtail contribs present: `forms`, `redirects`, `settings`, `embeds`, `sites`, `users`, `snippets`, `documents`, `images`, `search`, `admin`.
Third-party: `modelcluster`, `taggit`, `django_filters`.

`wagtail.contrib.sitemaps` is **not** installed — see §2.5.

### 1.2 Settings structure

`alternative_naissance/settings/{base,dev,production}.py`, loaded via `python-dotenv`.
`wsgi.py` hardcodes `settings.dev` through `setdefault`, so the Docker container runs dev settings with `DEBUG=True`, `ALLOWED_HOSTS=["*"]`, and a hardcoded `SECRET_KEY`. Static and media are served by Django because `urls.py` gates `staticfiles_urlpatterns()` on `DEBUG`.

Database reads `POSTGRES_*` env vars with defaults matching `.env.example`.

### 1.3 Base Page classes

There is **no shared abstract base page**. Every page model subclasses `wagtail.models.Page` directly: `CoreHomePage`, `ContactPage`, `FeedbackPage`, `EventPage`, `AtelierPage`, `JobPage`, `GenericPage`.

SEO comes from Wagtail's stock `promote_panels` (`slug`, `seo_title`, `search_description`). No custom SEO mixin, no Open Graph fields, no canonical handling.

`GenericPage` is the project's workhorse: a page-header group (`header_title`, `header_subtitle`, `header_background`, `show_page_header`), an `introduction` text field, and a 15-type `body` StreamField.

### 1.4 StreamField / block conventions

Blocks are defined **inline in `core/models.py`** — there is no `blocks.py`. Each is a `blocks.StructBlock` with an inner `class Meta` carrying `icon`, `label`, and `template`, and templates live at `templates/blocks/<name>.html`. Several blocks override `get_context()` to run querysets (`CalendarBlock`, `AtelierListBlock`, `JobsBlock`), so query-driven blocks are an established pattern here, not a novelty.

`GenericPage.body` registers: `why_choose`, `rich_text`, `testimonials`, `benefits`, `benefitpoint`, `paragraphs`, `team`, `cta`, `liste`, `calendar_events`, `dynamic_table`, `atelier`, `map`, `jobs`, `three_columns`.

### 1.5 Snippets

`@register_snippet` on plain models is standard: `Testimonial`, `Feedback`, `NewsletterSubscription`, `Menu` (a `ClusterableModel`), and `servicerequests.ServiceStaff`. Snippets are a first-class convention in this codebase.

### 1.6 SiteSettings

`core.SiteSettings` is `@register_setting` on `BaseSiteSetting` — **per-site**, which matters a great deal for this project. Fields: `site_name`, announcement group (`show_announcement`, `announcement_text`, `announcement_link`, `announcement_button_text`), `phone_number`, `email`, `address`, `facebook_url`, `twitter_url`, `instagram_url`, `pinterest_url`, `contact_page`, `footer_text`, `opening_hours`. Labels and help text are French.

Missing for Pound It: TikTok, YouTube, maps URL, registration URL, dancer portal URL, current season, alternate logo.

### 1.7 Image / document handling

Stock Wagtail. Images are referenced as `ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")` — used consistently. `MEDIA_ROOT` is `alternative_naissance/media`, bind-mounted into the container. `WAGTAILDOCS_EXTENSIONS` is restricted to a safe list.

### 1.8 Forms

`wagtail.contrib.forms` is installed but **no `FormPage` model exists anywhere** — it is dead weight at present.

The real form convention is the `servicerequests` app: plain Django `forms.py`, function views, URLs mounted under `/service-request/`, models split across a `models/` package, and admin exposed through `ModelViewSet` in a `wagtail_hooks/` package. `core` does the lighter version of the same thing — `Inscription` and `JobApplication` get `ModelViewSet`s registered via `@hooks.register("register_admin_viewset")` with `add_to_admin_menu = True`.

### 1.9 Notifications

The `emails` app is a clean, reusable convention and Pound It should use it as-is:

- `EmailTemplate` model — admin-editable `title` and `content` rendered as Django templates, keyed by a unique `scenario` slug.
- `registry.register_email_template(...)` — called from an app's `AppConfig.ready()` to declare defaults, materialized post-migrate.
- `utils.send_templated_email(scenario, context, to_emails)`.

`servicerequests/apps.py` is the reference implementation.

### 1.10 URL / redirect handling

`wagtail.contrib.redirects` is installed **and** `RedirectMiddleware` is in `MIDDLEWARE`. Legacy-URL 301s are available out of the box with no new infrastructure.

`urls.py` order: `django-admin/`, `admin/`, `documents/`, `search/`, `service-request/`, `core.urls`, then `wagtail_urls` as the catch-all.

### 1.11 Localization

`LANGUAGE_CODE = "fr"`, `USE_I18N = True`, `USE_TZ = True`, `TIME_ZONE = "UTC"`.

There is **no** `WAGTAIL_I18N_ENABLED`, no `WAGTAIL_CONTENT_LANGUAGES`, no `LocaleMiddleware`, and `wagtail.locales` is not installed. This is a single-locale French project. See §2.3.

`TIME_ZONE = "UTC"` is worth noting — Pound It class times are Mountain Time.

### 1.12 Tests

No pytest, tox, or setup.cfg — tests run through `manage.py test`.

- `emails/tests.py` — 112 lines, `django.test.TestCase`.
- `servicerequests/tests.py` — 421 lines, `wagtail.test.utils.TestCase`, uses `@override` type annotations and `unittest.mock`.
- `core/tests.py` — empty stub.

Convention to follow: `wagtail.test.utils.TestCase` for anything page-related, typed signatures, docstrings describing what is under test.

### 1.13 Docker / local environment

`docker-compose.yaml` now runs `postgres:16` (healthchecked), `pgadmin`, `mailhog` (profile-gated), and `app` (gunicorn 23.0.0, port 8000, media bind-mounted). The `app` container runs `manage.py migrate --noinput` on every start.

**Mailhog is already in the compose file** under the `mailhog` profile — that is the intended local mail sink for testing the school-inquiry notifications.

### 1.14 Admin UX conventions

`ModelViewSet` with `menu_label`, `menu_icon`, `menu_order`, `add_to_admin_menu`, `form_fields`, `list_display`, `search_fields`. `JobApplicationViewSet` demonstrates the read-only pattern (`add_view_enabled = False`, `edit_view_enabled = False`, `inspect_view_enabled = True`) — directly applicable to school inquiry submissions.

`Orderable` + `InlinePanel` is used throughout: `CoreHomePageSlide`, `FeatureSection`, `AboutSection`, `NewsItem`, `ServiceSection`, `AtelierDate`, `MenuItem`, `ChildInfo`.

---

## 2. Conflicts and Decisions Requiring Sign-Off

### 2.1 `EventPage` name collision — drives the whole app decision

`core.EventPage` already exists with an incompatible shape: a single `date` DateField, a `description` RichTextField, a `link` URLField, and a `upcoming_events()` static method hardcoded to a 180-day window. `core.CalendarBlock` queries it directly.

Pound It needs an `EventPage` with `event_type`, start/end datetimes, venue, poster image, pricing, and relations to faculty/programs/styles. Extending `core.EventPage` would break Alternative Naissance's calendar block and violate the brief's "do not rewrite unrelated applications."

**Recommendation: a new `poundit` Django app.** Model names then namespace cleanly (`poundit.EventPage` vs `core.EventPage`), migrations stay separate, and `core` is untouched. This is not "parallel architecture" in the sense the brief warns about — the shared *infrastructure* (settings framework, snippets, redirects, images, emails, block conventions, Docker) is reused verbatim. What is not shared are `core`'s domain models, which are specific to a French perinatal organisation and have no bearing on a dance studio.

### 2.2 Two sites in one Wagtail instance

`wagtail.sites` is installed, so the clean approach is a second `Site` record with `hostname` pointing at Pound It, rooted on a `PounditHomePage`. Because `SiteSettings` is a `BaseSiteSetting`, each site gets its own settings row automatically — no leakage.

For local demo purposes both sites can be reached via hostnames in your `hosts` file, or Pound It can temporarily be the default site. **Decision needed:** how you want to reach Pound It locally.

### 2.3 Language

The project is `LANGUAGE_CODE = "fr"`. Pound It's content is English. Three options:

- **A.** Leave it. Content is English; the Wagtail admin chrome stays French. Zero risk, slightly odd for Pound It staff.
- **B.** Enable Wagtail i18n (`WAGTAIL_I18N_ENABLED`, `WAGTAIL_CONTENT_LANGUAGES`, `wagtail.locales`, `LocaleMiddleware`) with `fr` and `en` locales. Correct long-term, but it touches shared settings and adds a `locale` column to every page — exactly the kind of shared-infrastructure change the brief asks me not to make casually.
- **C.** Set per-user admin language in Wagtail's account settings. Pound It editors get English admin, AN editors keep French, no settings change.

**Recommendation: C for Phase 1**, revisit B only if Pound It ever needs bilingual content.

### 2.4 Timezone

`TIME_ZONE = "UTC"` with `USE_TZ = True`. Class times are Mountain. Weekly schedule entries should be stored as **naive `TimeField`s** (a 5:15 PM class is 5:15 PM regardless of DST), which sidesteps the issue entirely. Event start/end are `DateTimeField`s and *will* be affected — recommend setting `TIME_ZONE = "America/Edmonton"`, a one-line change with no data impact on a site that currently has no datetime-sensitive content. **Needs your approval** since it is a shared setting.

### 2.5 Sitemaps

`wagtail.contrib.sitemaps` is not installed. For a local-SEO-dependent business this is worth adding — it is additive, affects nothing existing, and costs one `INSTALLED_APPS` line plus one URL. **Recommend adding.**

### 2.6 Training level system — the brief is out of date

The brief (§9) describes four colours: BLACK crew, YELLOW 6–9, RED 10–15, GREEN adult/advanced.

The 2026/27 schedule you supplied shows **nine** categories:

| Legend label | Meaning |
|---|---|
| CREW CLASS | Audition/placement crews |
| 2-3 YEARS | Bambinos |
| 4-5 YEARS | |
| 6-9 YEARS | |
| 10-15 YEARS | |
| PIBA (ADULTS) | Beginner adults |
| OPEN CLASSES | Drop-in / open styles |
| CHOREOGRAPHY | |
| PRIVATE | Private training |

`TrainingLevel` must therefore be a full snippet with nine seeded rows, not a four-value choices field. `colour_identifier` stays semantic (`crew`, `age_2_3`, `piba`, `open`, `private`, …) and Codex maps those to visual tokens.

### 2.7 Studio rooms are real, named, and load-bearing

The schedule runs two rooms in parallel — **"Notorious BIG"** and **"Black & Yellow"**. Room is not an optional note; it is a column of the grid. Recommend a small `StudioRoom` snippet (`name`, `slug`, `sort_order`) rather than a free-text field, so Codex can render the two-column grid reliably.

### 2.8 Instructors vary per session, not per program

"Super Girlz" is Rico **and** Masha. "Boss Mega Crew Adv." is Rico / Dizzy / Breton / Genie. "Red Deer City Breakers" is taught by Dizzylock on Monday and Rico on Wednesday.

So faculty must relate at the **schedule-entry** level, not only the program level. `ProgramScheduleEntry.instructors` (M2M) is required; `Program.faculty` remains as an editorial "who leads this program" convenience.

Note "Breton" and "Genie" appear as instructors on the schedule but are **not** on the faculty page — flagged for review in §9.

### 2.9 Studio rentals and private training are not public programs

`STUDIO RENTALS` and `PRIVATE TRAINING` occupy schedule slots but are not enrollable offerings. They should exist as schedule entries with a non-public program (or an `is_public` flag on `Program`) so the grid renders completely without them appearing in program listings.

---

## 3. Source Content Inventory

| Source URL | Title | Category | Status | Target object | Target URL | Redirect | Assets | Notes |
|---|---|---|---|---|---|---|---|---|
| `/` | Home | Landing | **STRUCTURE** | `PounditHomePage` | `/` | — | Hero, logo, boombox/shoes art | Compositor only; no duplicated program data |
| `/kidsreccrews` | Kids & Teen Rec Crews | Programs | **STRUCTURE** | `ProgramIndexPage` + `Program` rows (KIDS_TEENS_REC) | `/programs/kids-teen/` | 301 | Class photos | Split into individual Program records |
| `/adultreccrews` | Adult Rec Crews | Programs | **STRUCTURE** | `Program` rows (ADULT_REC) | `/programs/adult/` | 301 | | PIBA maps here |
| `/competitivecrews` | Competitive Crews | Programs | **STRUCTURE** | `Program` rows (COMPETITIVE) | `/programs/competitive/` | 301 | | Audition-required flag |
| `/schedule` | Studio Schedule | Schedule | **STRUCTURE** | `SchedulePage` + `ProgramScheduleEntry` | `/schedule/` | keep | Schedule JPG | Page body was JS/portal-gated; **rebuilt from your image** |
| `/faculty` | Faculty | People | **STRUCTURE** | `FacultyMember` snippets + `FacultyIndexPage` | `/faculty/` | keep | 8+ portraits | 8 bios extracted; see §9 |
| `/workshops` | Workshops | Events | **STRUCTURE** | `EventPage` (type=WORKSHOP) | `/events/workshops/` | 301 | Posters | Historic ones → ARCHIVE |
| `/schoolprograms` | School Hip Hop Residencies | Service + form | **CLEAN** | `SchoolProgramsPage` + `SchoolInquiry` | `/school-programs/` | 301 | Gallery | **Duplicated inquiry form — implement once** |
| `/importantdates` | Important Dates | Calendar | **STRUCTURE** | `CalendarEntry` × 20 + `ImportantDatesPage` | `/important-dates/` | 301 | — | Labelled "Tentative"; see §9 |
| `/waiver` | Waiver | Legal | **VERIFY** | Link out (Phase 1) | `/waiver/` | keep | — | See §7 — not a generic form |
| `/afterschool` | After School | Service | **VERIFY** | TBD | TBD | TBD | — | Not reachable in audit; may be retired |
| `/event-tickets` | Events | Events | **STRUCTURE** | `EventIndexPage` | `/events/` | 301 | Posters | Wix ticketing — confirm replacement |
| Privacy / Refund / Terms | Legal | Legal | **KEEP** | `GenericPage` under `/legal/` | `/legal/*` | 301 | — | Copy verbatim, do not edit wording |
| `app.gostudiopro.com/...` | Dancer Portal | External | **KEEP** | `PounditSettings.dancer_portal_url` | external | — | — | Stays external per §21 of brief |

**Extracted and ready to import:** 8 faculty bios with styles and achievements; 20 calendar entries for the 2026–27 season; the complete weekly schedule (≈50 sessions, Appendix A); studio contact block; four social URLs; ten dance styles.

---

## 4. Proposed Architecture

New app `poundit`. Structure mirrors `servicerequests` (models as a package, since this is more than one file's worth):

```
poundit/
    __init__.py
    apps.py                     # registers school-inquiry email templates
    blocks.py                   # Pound It presentation blocks
    models/
        __init__.py
        taxonomies.py           # DanceStyle, TrainingLevel, ProgramCategory, StudioRoom, Season
        faculty.py              # FacultyMember
        programs.py             # Program, ProgramScheduleEntry, ProgramInclusion
        events.py               # EventPage, EventIndexPage
        calendar.py             # CalendarEntry
        pages.py                # PounditHomePage, ProgramIndexPage, SchedulePage,
                                # FacultyIndexPage, SchoolProgramsPage, ImportantDatesPage
        settings.py             # PounditSettings
        inquiries.py            # SchoolInquiry
        importmap.py            # ImportedObject (source→target mapping)
    wagtail_hooks/
        __init__.py
        viewsets.py             # ModelViewSets for faculty, programs, calendar, inquiries
    management/commands/
        import_poundit.py       # --dry-run, idempotent
        seed_poundit_taxonomies.py
    migrations/
    tests/
```

### 4.1 Snippets (taxonomies)

| Model | Fields |
|---|---|
| `DanceStyle` | `name`, `slug`, `short_description`, `sort_order` |
| `TrainingLevel` | `name`, `display_label`, `colour_identifier`, `description`, `age_label`, `age_min`, `age_max`, `sort_order` |
| `ProgramCategory` | `name`, `slug`, `sort_order` — a snippet, not a choices field, so templates never hardcode `KIDS_TEENS_REC` |
| `StudioRoom` | `name`, `slug`, `sort_order` |
| `Season` | `label` ("2026/2027"), `start_date`, `end_date`, `is_current` |

### 4.2 `Program` (snippet, `ClusterableModel`)

Snippet rather than page, because a program appears in the schedule grid, on category pages, on the homepage, and on faculty pages. A page would force one canonical URL per crew — 30+ thin pages nobody links to. Category index pages carry the URLs; programs render inside them.

`title`, `slug`, `category` (FK), `short_description`, `long_description` (RichText), `hero_image`, `age_min`, `age_max`, `age_label`, `level` (FK `TrainingLevel`), `audition_required`, `is_public`, `featured`, `active`, `sort_order`, `season` (FK), `tuition_amount`, `tuition_period`, `tuition_note`, `registration_url`, `registration_cta_label`, `styles` (M2M), `faculty` (M2M), `competition_info` (RichText), plus `InlinePanel` children for inclusions and schedule entries.

Display properties exposed to templates: `age_display`, `tuition_display`, `level_colour`, `schedule_display`.

### 4.3 `ProgramScheduleEntry` (`Orderable`)

`program` (ParentalKey), `weekday` (0–6 IntegerChoices), `start_time`, `end_time`, `label`, `room` (FK `StudioRoom`), `instructors` (M2M `FacultyMember`), `season` (FK), `notes`, `sort_order`.

Properties: `time_display` ("5:15–6:00 PM"), `weekday_display`, `duration_minutes`.

Manager helpers: `for_season(season)`, `grid()` returning `{weekday: {room: [entries]}}` so Codex renders the grid without doing logic in templates.

### 4.4 `FacultyMember` (snippet)

`name`, `dance_name`, `slug`, `portrait`, `role`, `short_bio`, `full_bio` (RichText), `styles` (M2M), `programs` (reverse of `Program.faculty`), `instagram_url`, `featured`, `active`, `sort_order`.

### 4.5 `EventPage` + `EventIndexPage`

`event_type` (FK to an `EventType` snippet — battles, workshops, camps, performances, competitions, festivals, intensives), `short_description`, `body` (StreamField), `hero_image`, `poster_image`, `start_datetime`, `end_datetime`, `venue_name`, `venue_address`, `price_text`, `age_label`, `capacity`, `registration_url`, `external_url`, `related_faculty`, `related_programs`, `related_styles`, `featured`, `status`.

`EventPage.objects.upcoming()` / `.past()` / `.featured()` as **queryset methods on a custom manager**, filtering on `end_datetime` (falling back to `start_datetime`) so multi-day events stay "upcoming" until they actually finish. This is what makes expired events drop off the homepage automatically.

### 4.6 `CalendarEntry` (snippet)

`title`, `start_date`, `end_date`, `category` (CLASS / CLOSURE / BATTLE / COMPETITION / WORKSHOP / SHOW / CAMP / TRYOUT / OTHER), `description`, `related_event` (FK, nullable), `season` (FK), `featured`. Default ordering chronological. `ImportantDatesPage` renders from these — no RichText list.

### 4.7 `PounditSettings` (`BaseSiteSetting`)

Separate from `core.SiteSettings`, leaving that model untouched. Fields per brief §15 plus `dancer_portal_url`, `registration_url`, `tiktok_url`, `youtube_url`, `maps_url`, `current_season` (FK), `alternate_logo`.

### 4.8 `SchoolInquiry` + `ImportedObject`

`SchoolInquiry`: `school_name`, `contact_name`, `email`, `phone`, `preferred_dates`, `message`, `created_at`, `handled`. Exposed read-only through `ModelViewSet` exactly like `JobApplication`. Notifications via `emails.send_templated_email` with scenarios registered in `PounditConfig.ready()`.

`ImportedObject`: `source_url`, `source_identifier`, `content_type`, `object_id`, `import_status`, `last_imported` — the idempotency ledger for `import_poundit`.

---

## 5. Information Architecture

```
PounditHomePage                     /
├── ProgramIndexPage                /programs/
│   ├── (category views)            /programs/kids-teen/  adult/  competitive/  open-training/
├── SchedulePage                    /schedule/
├── FacultyIndexPage                /faculty/
├── EventIndexPage                  /events/
│   └── EventPage                   /events/<slug>/
├── SchoolProgramsPage              /school-programs/
├── ImportantDatesPage              /important-dates/
├── GenericPage (About/Culture)     /about/
├── ContactPage                     /contact/
└── GenericPage (Legal)             /legal/
    ├── waiver, privacy, refund-policy, terms
```

Category pages are routed views on `ProgramIndexPage` rather than separate page models — fewer models, and categories stay editable data.

---

## 6. URL Map

| Legacy (Wix) | New | Action |
|---|---|---|
| `/kidsreccrews` | `/programs/kids-teen/` | 301 |
| `/adultreccrews` | `/programs/adult/` | 301 |
| `/competitivecrews` | `/programs/competitive/` | 301 |
| `/schedule` | `/schedule/` | unchanged |
| `/faculty` | `/faculty/` | unchanged |
| `/workshops` | `/events/workshops/` | 301 |
| `/schoolprograms` | `/school-programs/` | 301 |
| `/importantdates` | `/important-dates/` | 301 |
| `/waiver` | `/legal/waiver/` | 301 |
| `/event-tickets` | `/events/` | 301 |
| `/afterschool` | TBD | pending §9 |

Loaded through `wagtail.contrib.redirects` (already installed) by a data migration, so they are editable in the admin afterwards.

---

## 7. Waiver — Phase 1 Position

Taking **option A**: link out to the existing waiver workflow. The waiver captures a signature and a legal acknowledgement; implementing that as a Wagtail form would produce consent records with no versioned legal text, no evidence trail, and no retention policy. Legal wording will be copied verbatim if it is hosted, and will not be touched by content cleanup. A real e-signature implementation is tracked as a separate feature requiring explicit review.

---

## 8. Template Contract for Codex

Semantic data only. No HTML is generated in Python.

**`ProgramIndexPage`** — `page.categories`, `page.programs_by_category`, `page.featured_programs`
**`Program`** — `.title` `.slug` `.category` `.short_description` `.long_description` `.hero_image` `.age_label` `.age_display` `.level.colour_identifier` `.level.display_label` `.audition_required` `.tuition_display` `.tuition_note` `.registration_url` `.registration_cta_label` `.schedule_entries.all` `.styles.all` `.faculty.all` `.inclusions.all` `.competition_info`
**`ProgramScheduleEntry`** — `.weekday` `.weekday_display` `.start_time` `.end_time` `.time_display` `.label` `.room.name` `.room.slug` `.instructors.all` `.notes`
**`SchedulePage`** — `page.grid` (`{weekday: {room: [entries]}}`), `page.rooms`, `page.weekdays`, `page.levels` (for the legend), `page.season`
**`FacultyMember`** — `.name` `.dance_name` `.portrait` `.role` `.short_bio` `.full_bio` `.styles.all` `.programs.all` `.instagram_url`
**`EventPage`** — `.title` `.event_type.name` `.event_type.slug` `.start_datetime` `.end_datetime` `.hero_image` `.poster_image` `.venue_name` `.venue_address` `.price_display` `.age_label` `.registration_url` `.related_faculty.all` `.related_programs.all`
**`EventIndexPage`** — `page.upcoming` `page.past` `page.featured` `page.event_types`
**`ImportantDatesPage`** — `page.entries_by_month`, `page.season`
**`PounditHomePage`** — `page.hero_title` `.hero_eyebrow` `.hero_image` `.intro_copy` `.featured_programs` `.featured_faculty` `.upcoming_events` `.training_levels` `.announcement`
**Settings** — `{{ settings.poundit.PounditSettings.<field> }}` in any template

Level colours reach Codex as `colour_identifier` slugs (`crew`, `age_2_3`, `age_4_5`, `age_6_9`, `age_10_15`, `piba`, `open`, `choreography`, `private`). No hex values in the database.

---

## 9. Items Requiring Human Review

1. **"Breton" and "Genie"** teach Boss Mega Crew Adv. on the schedule but have no faculty page entry. Add them, or leave as text?
2. **Important Dates is labelled "Tentative."** Import as-is with the tentative flag preserved, or hold?
3. **Faculty count.** The page renders 8 bios; its own heading claims 9. One may be missing or mis-parsed.
4. **`/afterschool`** was not reachable during the audit. Retired, or just unlinked?
5. **`/event-tickets` uses Wix ticketing.** What replaces it — Eventbrite, GoStudioPro, or door sales?
6. **Tuition is nowhere on the public site.** Pricing fields will be modelled but left empty pending your figures.
7. **Image rights.** Faculty portraits and class photos need confirmation before download from the Wix CDN.
8. **Timezone change** (§2.4) and **sitemaps** (§2.5) touch shared settings — need explicit approval.
9. **Season labelling.** The schedule says "2026/2027"; Important Dates says "2026-2027". Normalising to one `Season.label`.

---

## 10. Phase Plan

| Phase | Scope | Commit |
|---|---|---|
| 0 | This document | docs only |
| 1 | `poundit` app skeleton, taxonomies, `PounditSettings`, seed command | `feat(poundit): app scaffold + taxonomies` |
| 2 | `Program`, `ProgramScheduleEntry`, `ProgramInclusion`, admin panels | `feat(poundit): programs and weekly schedule` |
| 3 | `FacultyMember` + index page | `feat(poundit): faculty` |
| 4 | `EventPage`, `EventIndexPage`, `CalendarEntry`, managers | `feat(poundit): events and season calendar` |
| 5 | `PounditHomePage`, `SchedulePage`, content pages, blocks | `feat(poundit): pages and blocks` |
| 6 | `SchoolInquiry`, email scenarios, viewset | `feat(poundit): school inquiry flow` |
| 7 | `import_poundit` + image migration | `feat(poundit): source importer` |
| 8 | Redirects data migration, sitemaps, SEO fields | `feat(poundit): seo and legacy redirects` |
| 9 | Admin UX pass | `refactor(poundit): admin panel grouping` |
| 10 | Tests + QA | `test(poundit): coverage` |

Each phase is reviewable on its own and leaves the repo working. Nothing in `core`, `servicerequests`, `emails`, or `search` is modified except the two shared-settings items in §9.8, which will not be touched without your approval.

---

## Appendix A — Weekly Schedule, 2026/2027 Season

Transcribed from the studio schedule graphic. Rooms: **NB** = Notorious BIG, **BY** = Black & Yellow.

### Monday
| Room | Class | Time | Instructor | Level |
|---|---|---|---|---|
| NB | Studio Rentals | 4:30–5:15 | — | rental |
| NB | Lil Cuz | 5:15–6:00 | Rico | crew |
| NB | Breaking | 6:00–6:45 | Dizzylock | 6-9 |
| NB | Red Deer City Breakers | 7:00–8:00 | Dizzylock | crew |
| NB | Open Locking | 8:00–8:45 | Dizzylock | open |
| NB | Open Waacking | 8:45–9:30 | Dizzylock | open |
| BY | The Broskies | 5:00–6:00 | Nathan | crew |
| BY | La Familia JR | 6:00–7:00 | Rico | crew |
| BY | Lite Feet | 7:00–7:45 | Rico | 10-15 |

### Tuesday
| Room | Class | Time | Instructor | Level |
|---|---|---|---|---|
| NB | Private Training | 4:30–5:15 | — | private |
| NB | La Bandita | 5:15–6:00 | Rico | crew |
| NB | La Familia | 6:00–7:00 | Dizzylock | crew |
| NB | PIBA (Beginner Adults) | 7:00–7:45 | Rico | piba |
| NB | Open Hip Hop | 7:45–8:30 | Dizzylock | open |
| NB | AK42s | 8:30–9:30 | Rico | crew |
| BY | Bambinos (2-3 yrs) | 4:30–5:00 | Rico | 2-3 |
| BY | Chicken Noodle Soup | 5:00–5:30 | Charlee | 4-5 |
| BY | Hip Hop (6-9 yrs) | 5:30–6:15 | Nathan | 6-9 |
| BY | Popping | 7:00–7:45 | Dizzylock | 10-15 |
| BY | Private Training | 7:45–8:30 | — | private |
| BY | Open Breaking | 8:30–9:15 | Dizzylock | open |

### Wednesday
| Room | Class | Time | Instructor | Level |
|---|---|---|---|---|
| NB | Studio Rentals | 4:30–5:15 | — | rental |
| NB | Chicos | 5:15–6:00 | Nathan | crew |
| NB | Choreography | 6:00–7:15 | Allen | choreography |
| NB | Open Atlanta Styles | 7:15–8:00 | Allen | open |
| NB | Lulu 100s | 8:15–9:00 | Rico | crew |
| BY | Hip Hop | 4:30–5:00 | Charlee | 4-5 |
| BY | Red Deer City Breakers | 5:15–6:00 | Rico | crew |
| BY | Riverside Bounce | 6:00–6:45 | Rico | crew |
| BY | Hip Hop | 7:00–7:45 | Nathan | 10-15 |
| BY | Open Jersey Club | 7:45–8:30 | Cody | open |
| BY | PIBA (Beginner Adults) | 8:30–9:15 | Cody | piba |

### Thursday
| Room | Class | Time | Instructor | Level |
|---|---|---|---|---|
| NB | Hip Hop (6-9 yrs) | 4:30–5:15 | Nathan | 6-9 |
| NB | Super Girlz | 5:15–6:15 | Rico / Masha | crew |
| NB | Boss Mega Crew Adv. | 6:15–7:15 | Rico / Dizzy / Breton / Genie | crew |
| NB | Battle Training | 7:15–8:15 | Rico | crew |
| NB | Revolution | 8:15–9:15 | Rico / Dizzy / Allen | crew |
| BY | Open Styles | 4:30–5:15 | Dizzylock | open |
| BY | PIBA (Beginner Adults) | 5:15–6:00 | Masha | piba |
| BY | Open House | 6:00–6:45 | Masha | open |
| BY | Private Training | 6:45–9:00 | — | private |

### Friday
| Room | Class | Time | Instructor | Level |
|---|---|---|---|---|
| NB | Choreography Cleaning | 5:15–7:00 | — | choreography |
| NB | Studio Rentals | 7:30–8:30 | — | rental |
| BY | Private Training | 5:15–9:00 | — | private |

Tagline on the graphic: **ONE LOVE. ONE DANCE. ONE COMMUNITY.**

---

## Appendix B — Extracted Taxonomy Seeds

**Dance styles (10):** Hip Hop, Breaking, Locking, Waacking, House, Litefeet, Dancehall, Choreography, Atlanta Styles, Jersey Club. Also appearing on faculty bios: Popping, Animation, Vogue, Afro, Freestyle, Campbellocking.

**Training levels (9):** crew, age_2_3, age_4_5, age_6_9, age_10_15, piba, open, choreography, private.

**Studio rooms (2):** Notorious BIG, Black & Yellow.

**Studio contact:** 5809 51 Ave #4b, Red Deer, AB T4N 4H8 · (403) 896-7935 · Mon–Thu 4:00–9:00 PM
**Social:** instagram.com/poundithiphopstudios · facebook.com/PoundItHipHopStudio · tiktok.com/@poundithiphopstudio · youtube.com/@poundithiphopstudios3654
**Dancer portal:** app.gostudiopro.com/online/pounditreddeer
