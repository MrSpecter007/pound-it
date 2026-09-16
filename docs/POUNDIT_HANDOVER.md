# Pound It Hip Hop Studio — Backend Handover

**Repo:** `Alternative-Naissance` · **App:** `poundit` · Wagtail 7.0 / Django 5.2.2 / Python 3.12 / PostgreSQL 16
**Phases 0–10 complete.** 286 tests passing. No missing migrations.
**Owner of presentation:** Codex — see §9.

---

## 1. Architecture summary

Pound It lives in its own `poundit` Django app inside the existing repo, served as a second Wagtail `Site` that is now the default. It reuses the project's shared infrastructure — `wagtail.contrib.settings`, snippets, redirects, images, the `emails` app, the `Orderable`/`InlinePanel` conventions, the Docker stack — and shares none of `core`'s domain models.

The separate app was not a stylistic preference. `core.EventPage` already exists, and Django derives the multi-table-inheritance reverse accessor from the model name, so two `EventPage` classes both claimed `Page.eventpage` and the app would not start. Pound It's parent link is named `poundit_eventpage`, resolving it entirely on this side. `core`, `servicerequests`, `emails` and `search` are unmodified.

The data model follows one rule: **anything factual is structured, and lives in exactly one place.** Programs carry price, age and level. Sessions carry day, time, room and instructors. Faculty carry identity and styles. Settings carry contact details. Pages carry editorial copy and reference the rest. Editing a program updates the home page, the category listing and the schedule grid together, because none of them hold a copy.

Three shared settings changed, each approved: `LANGUAGE_CODE` `fr` → `en-ca`, `TIME_ZONE` `UTC` → `America/Edmonton`, and three additive `INSTALLED_APPS` entries (`poundit`, `wagtail.contrib.sitemaps`, `wagtail.contrib.routable_page`, plus `django.contrib.sitemaps`).

---

## 2. Models

**Taxonomies (snippets).** `Season`, `ProgramCategory`, `TrainingLevel`, `DanceStyle`, `StudioRoom`, `EventType`, `CalendarCategory`. Vocabularies rather than `choices` fields, so staff edit them without a developer and templates never hardcode an identifier.

**Programs.** `Program` (clusterable snippet) with `ProgramInclusion`, `ProgramTuitionOption` and `ProgramScheduleEntry` as inline children. A program is a snippet, not a page, because it appears in the schedule grid, on category listings, on the home page and on faculty profiles; giving forty crews their own URLs would create thin pages nobody links to.

**Faculty.** `FacultyMember` (clusterable snippet), related to programs at program level *and* at session level.

**Events and calendar.** `EventPage`, `EventIndexPage`, `CalendarEntry`.

**Pages.** `PounditHomePage`, `ProgramIndexPage`, `SchedulePage`, `FacultyIndexPage`, `ImportantDatesPage`, `SchoolProgramsPage`, `ContentPage`.

**Operations.** `PounditSettings` (per-site), `SchoolInquiry`, `ImportedObject`.

Twenty-five models in all: seven page types, eighteen models and snippets.

### Relationships that carry weight

`ProgramScheduleEntry.instructors` is many-to-many to `FacultyMember` **at the session level**, not the program level. Red Deer City Breakers is led by Dizzylock on Monday and Rico on Wednesday; Supergirlz is co-taught. A program-level relation alone would lose that. `Program.faculty` remains as the editorial "who leads this program".

`Program.is_public` separates offerings from schedule occupancy. Studio rentals and private training occupy cells in the grid but are not enrollable, so they render in the admin and drop out of every public listing.

`TrainingLevel.colour_identifier` is a semantic token — `crew`, `piba`, `age-6-9` — never a colour value. Codex maps tokens to visual tokens, so the palette changes without a migration.

---

## 3. Migrations

Nine, all applied, `makemigrations --check` clean:

| # | Contents |
|---|---|
| 0001 | Taxonomies and `PounditSettings` |
| 0002 | `Program`, `ProgramScheduleEntry`, `ProgramInclusion`, `ProgramTuitionOption` |
| 0003 | `FacultyMember`, plus the program and session faculty relations |
| 0004 | `FacultyMember.short_name` |
| 0005 | Data migration removing a departed faculty member |
| 0006 | `EventPage`, `EventIndexPage`, `CalendarEntry` |
| 0007 | The six remaining page types |
| 0008 | `SchoolInquiry`, `SchoolProgramsPage` |
| 0009 | `ImportedObject` |

---

## 4. Source → destination URL map

Eleven 301s, created by `seed_poundit_redirects`, verified end to end.

| Legacy | New | Note |
|---|---|---|
| `/kidsreccrews` | `/programs/kids-teen/` | |
| `/adultreccrews` | `/programs/adult/` | |
| `/competitivecrews` | `/programs/competitive/` | |
| `/schedule` | `/schedule/` | |
| `/faculty` | `/faculty/` | |
| `/workshops` | `/events/workshop/` | |
| `/schoolprograms` | `/school-programs/` | |
| `/importantdates` | `/important-dates/` | |
| `/waiver` | `/legal/waiver/` | links out, see §11 |
| `/event-tickets` | `/events/` | ticketing provider undecided |
| `/afterschool` | `/school-programs/` | **inferred, needs confirmation** |

Category and event-type paths are real URLs resolved against the database, so a category added in the admin routes immediately. Unknown slugs 404 rather than rendering an empty page. The old `?category=` and `?type=` parameters still work, so links already in the wild keep resolving.

Alternative Naissance's five existing redirects are scoped to its own site and unaffected.

---

## 5. Imported content

| | Count |
|---|---|
| Programs | 34 (32 public, 2 schedule occupancy) |
| Weekly sessions | 44 |
| Faculty | 9 |
| Calendar entries | 20 |
| Taxonomy rows | 49 |
| Pages | 14 |
| Redirects | 11 |
| Ledger entries | 63 |

Sources: the 2026/27 schedule graphic for days, times, rooms and instructors; the rec and competitive crew pages for tuition, auditions, categories and descriptions; the faculty page for names, roles and styles; the Important Dates page for the season.

Every object traces back to its source page through `ImportedObject`, visible in the admin under **Import ledger**.

---

## 6. Imported media

**None yet, by design.** Image binaries could not be fetched from this environment, and the brief rules out pointing production pages at the Wix CDN. The pipeline instead ingests a local folder:

```
manage.py import_poundit_images --list
manage.py import_poundit_images --source-dir <folder> --dry-run
manage.py import_poundit_images --source-dir <folder>
```

Nine files expected: `logo`, `rico`, `cody`, `leiran`, `nathan`, `dizzylock`, `allen`, `charlee`. It deduplicates by content hash using Wagtail's own `hash_filelike`, writes alt text, attaches portraits to faculty and the logo to site settings, and never overwrites an image already set by hand.

---

## 7. Archived and skipped

- **The duplicated school inquiry form.** The source page renders the same form twice. One is implemented.
- **Studio rentals and private training.** Kept as schedule occupancy, excluded from public listings.
- **Faculty biographies.** Deliberately empty. The source bios are long-form editorial in the studio's voice; only paraphrase was extractable, and seeding that would have quietly rewritten the studio's copy. One-line factual summaries render listings in the meantime.
- **School Programs descriptive copy.** Same reasoning. Facts only: grades K–9, four-day format.
- **Legal pages.** Waiver, Privacy, Refund, Terms exist as empty shells for verbatim wording.
- **Breton and Genie portraits.** No portrait published on the source site; recorded as skipped, not pending.
- **Wix ticketing.** Not reimplemented. Registration stays external and configurable.

---

## 8. Needs a human

Surfaced three ways: the **Import ledger** in the admin, the **"Pound It: needs a person"** dashboard panel, and the review notes each seed prints.

**Blocking a launch**

1. **Faculty biographies** — nine, to paste in verbatim.
2. **Three sessions have no instructor** — PIBA Thursday 5:15–6:00, Open House Thursday 6:00–6:45, Choreography Cleaning Friday 5:15–7:00.
3. **Legal wording** — four pages empty.
4. **Studio email** — unset, so inquiry notifications fall back to `ADMIN_EMAIL`.

**Decisions**

5. **Two crews have no source page** — The Broskies (Mon 5:00–6:00) and Boss Mega Crew Adv. (Thu 6:15–7:15) sit in "Other" pending a category.
6. **Three schedule conflicts** — the crew pages disagree with the 2026/27 graphic on Red Deer City Breakers (Mon 6:45 vs 7:00, Wed 5:00 vs 5:15), La Familia Jr. (Mon 7:45 vs 6:00) and PIBA Wednesday (8:15 vs 8:30). The graphic was used, being the one labelled with this season. The Wix pages are likely stale.
7. **`/afterschool`** — the one inferred redirect.
8. **`One For Then City Edmonton`** — copied verbatim, reads like a typo for "One For The City".
9. **Twenty tentative dates** — flagged as published, to confirm individually.
10. **Wednesday 4:30 "Hip Hop" (ages 4–5)** — seeded as Chicken Noodle Soup's second session, per the kids rec page.
11. **Nathan's and Allen's portraits** share a source filename on the old host; confirm they are different people.
12. **Guest instructors teaching weekly** — the faculty page calls Dizzylock and Allen guest instructors; the schedule has them teaching every week. Seeded as "Instructor".
13. **Leiran** appears on the faculty page but on no session.
14. **Program leads are derived** from each session's first instructor; the source never published them.
15. **Tuition for open-training classes** is not published anywhere; those programs have no price.

---

## 9. Template contract for Codex

Semantic data only. A test asserts no display property emits markup.

**`Program`** — `.title` `.slug` `.category` `.short_description` `.long_description` `.hero_image` `.age_display` `.level_colour` `.audition_required` `.tuition_display` `.has_tiered_tuition` `.tuition_note` `.schedule_display` `.registration_url` `.registration_cta_label` `.schedule_entries.all` `.styles.all` `.faculty.all` `.inclusions.all` `.tuition_options.all` `.competition_info`

**`ProgramScheduleEntry`** — `.weekday` `.weekday_display` `.start_time` `.end_time` `.time_display` `.duration_minutes` `.display_label` `.room.name` `.room.slug` `.instructors.all` `.instructor_display` `.level_colour` `.notes`

**`FacultyMember`** — `.name` `.dance_name` `.short_name` `.display_name` `.grid_name` `.portrait` `.role` `.short_bio` `.full_bio` `.biography` `.styles.all` `.programs_taught` `.is_occasional` `.availability_note` `.instagram_url`

**`EventPage`** — `.title` `.event_type.name` `.event_type.slug` `.start_datetime` `.end_datetime` `.date_display` `.is_multi_day` `.is_past` `.hero_image` `.poster_image` `.venue_name` `.venue_address` `.price_display` `.age_label` `.capacity` `.status` `.registration_url` `.related_faculty.all` `.related_programs.all` `.related_styles.all`

**`CalendarEntry`** — `.title` `.start_date` `.end_date` `.date_display` `.is_multi_day` `.is_past` `.is_tentative` `.category_slug` `.description` `.related_event`

**Page context**

- `PounditHomePage` — `featured_programs` `featured_faculty` `upcoming_events` `upcoming_dates` `training_levels` `season`, plus its own hero and section fields
- `SchedulePage` — `schedule` (a finished nested list: `[{weekday, label, rooms: [{room, entries}]}]`), `grid` (the dict form for Python), `rooms`, `levels`, `season`
- `ProgramIndexPage` — `programs_by_category` `all_categories` `featured_programs` `active_category`
- `EventIndexPage` — `upcoming` `past` `featured` `event_types` `active_type`
- `FacultyIndexPage` — `faculty` `occasional_faculty`
- `ImportantDatesPage` — `entries_by_month` `categories` `active_category` `has_tentative` `season`
- `SchoolProgramsPage` — `form` `submitted`, plus `grade_range` and `duration_label`

**Settings** — `{% load wagtailsettings_tags %}{% get_settings %}` then `{{ settings.poundit.PounditSettings.<field> }}`. This project has **no settings context processor**; `core` uses the tag and so does Pound It.

**Templates** are at `templates/poundit/`, unstyled and structural. Six content blocks in `poundit/blocks.py`: heading, rich text, image, gallery, video, CTA. Replace the markup freely; the context contract above is what to rely on.

---

## 10. Tests

286 passing, `wagtail.test.utils`/`django.test` via `manage.py test`, matching the project's existing convention.

| File | Tests | Covers |
|---|---|---|
| `test_taxonomies.py` | 19 | Vocabularies, season invariant, legend filter, seed idempotency |
| `test_programs.py` | 37 | Display properties, querysets, grid shape, schedule seed |
| `test_faculty.py` | 32 | Names, session instructors, roster seed |
| `test_events.py` | 36 | Upcoming/past logic, date display, calendar |
| `test_pages.py` | 42 | Tree rules, composition, page context, site seed |
| `test_inquiries.py` | 22 | One form, redirect-after-post, notifications, mail failure |
| `test_importer.py` | 25 | Ledger, idempotency, image dedup and attachment |
| `test_redirects.py` | 26 | Routable paths, the child-page guard, 301s, sitemap |
| `test_admin.py` | 16 | Menu grouping, dashboard panel, no regression for the other site |
| `test_success_criteria.py` | 26 | Every criterion in §29 of the brief, as executable checks |

Worth calling out: `test_success_criteria.py` turns the brief's definition of success into assertions, so those properties keep holding as the site changes. And `test_an_event_page_is_never_shadowed_by_a_type_of_the_same_slug` pins the sharpest edge in the routing — `RoutablePageMixin` tries its own routes before child pages.

**Pre-existing, not mine:** `servicerequests/tests.py` has 11 errors from drift between its tests and the `Deuil` model, which references `deceased_name`, `deceased_date` and `additional_notes` that the model does not have. Untouched.

---

## 11. Remaining work

**Before launch**

- Supply the nine images and run the import.
- Paste the nine faculty biographies and the four legal pages in verbatim.
- Assign instructors to the three unstaffed sessions.
- Set the studio's public email, maps URL and waiver URL in Pound It settings.
- Work through §8.
- Codex's presentation pass.

**Deliberately out of scope**

- **Waiver.** Phase 1 links out to the existing workflow. A real e-signature feature needs versioned legal text, submission timestamps, signatory and participant records, signature representation, consent evidence, retention, security and privacy — a separate reviewed feature, not content cleanup.
- **Registration and dancer management.** Stays on GoStudioPro, configurable per program and studio-wide.
- **Event ticketing.** Provider undecided.
- **Bilingual content.** The project is single-locale. Wagtail i18n would add a `locale` column to every page across both sites; not needed while Pound It is English-only.

**Operational notes**

- The app container runs `migrate` on start. Never run `manage.py migrate` by hand while it is starting — two concurrent migrations will fail on duplicate tables. Wait for `Starting gunicorn` in the logs.
- `manage.py import_poundit` runs the whole import; each seed stays runnable alone. All are idempotent, all support `--dry-run`, and all preserve admin edits unless passed `--update`.
- Alternative Naissance answers on `alternative-naissance.localhost`. Add it to your hosts file to reach it.
