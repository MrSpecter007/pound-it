# Installed backend integration

These templates now consume the backend implemented in `alternative_naissance/poundit/`. No duplicate models, migrations or frontend data store were added by the design work.

## Shared shell

`{% get_settings %}` reads `settings.poundit.PounditSettings`, aliased to `studio` around the page content. Site-aware `home_url` comes from the current Wagtail site's root page.

Fields used: studio_name, tagline, logo, address, maps_url, phone_number, public_email, opening_hours, registration_url, registration_cta_label, dancer_portal_url, waiver_url, instagram_url, facebook_url, tiktok_url, youtube_url, show_announcement, announcement_text, announcement_url, announcement_button_text, footer_copy.

Navigation uses the backend's seeded site-relative slugs: programs (kids-teen/adult/competitive/open-training), schedule, faculty, events, important-dates, school-programs, about and legal children. Keep these slugs stable or update navigation when changing them.

## Page contexts

| Template | Actual backend context/fields |
| --- | --- |
| home | hero_eyebrow, hero_title, hero_text, hero_image, hero_video_url, primary_cta_label/url, intro_copy, section titles/text, body; featured_programs, featured_faculty, upcoming_events, upcoming_dates, training_levels, season |
| program index | introduction/body; all_categories, programs_by_category tuples, active_category |
| faculty index | introduction/body; faculty, occasional_faculty |
| schedule | introduction/body, show_legend; season, levels, schedule containing weekday/label/rooms, room entries |
| event index | introduction/body; event_types, active_type, upcoming, past |
| important dates | introduction/body; season, categories, active_category, entries_by_month, has_tentative |
| school programs | introduction, hero_image, grade_range, duration_label, body, inquiry headings/button/success text, show_inquiry_form; form, submitted |
| content | introduction, hero_image, body, live children |

## Snippets and detail behavior

Program cards read title, slug, category, level_colour, age_display, short_description, schedule_display, tuition_display and audition_required. Expanded details show long_description, level.display_label, schedule_entries with time/room/instructor, styles, faculty, inclusions, tuition_options, tuition_note and competition_info. Registration uses the program URL or the studio setting. Program facts are never parsed from rich text.

Program links point to `/programs/<category>/#program-<slug>`. Faculty links point to `/faculty/#faculty-<slug>`. Faculty cards read display_name, portrait, role, short_bio, full_bio, styles, availability_note, instagram_url and website_url. Full biography uses the Wagtail richtext filter rather than marking arbitrary HTML safe.

Schedule entries retain the backend's grouping by day and room. The day select is a progressive enhancement; all sessions remain in HTML without JavaScript.

Calendar entries use date_display/start_date, title, description, related_event, is_tentative and is_past. EventPage uses start/end_datetime, date_display, venue, price_display, age_label, capacity, hero_image, poster_image, related_faculty/styles and body. Registration is shown only when the event is future/current and status is scheduled; sold-out, postponed, cancelled and past states suppress that event's registration button.

## Forms, blocks and images

SchoolInquiryForm remains the existing backend form. The frontend preserves CSRF, hidden honeypot, required fields, server error relationships, posted values, the backend action and submitted confirmation. Django 5 `as_field_group` supplies labels and accessible errors. No successful inquiry was submitted to the live installation during frontend QA.

Styled StreamField block contracts match the existing HeadingBlock, RichTextBlock, ImageBlock, GalleryBlock, VideoEmbedBlock and CTASectionBlock. CTA URLs fall back to the actual Pound It settings.

The shared image component supports responsive Wagtail renditions, desktop/mobile hero crops, portraits, landscape images and uncropped posters. Source photography is the fallback where no CMS image is attached. Complete image import and focal-point review before launch.

## Optional backend follow-up, not required to apply the design

1. Expose homepage category photography, training photo, culture stories and their copy as image fields or ordered editorial blocks if staff need to edit them. Currently these source-based design sections are template content.
2. Complete image relationships/focal points, approved legal copy, school residency narrative, map URL, video URL and inquiry recipient settings.
3. Review the program-detail session collection for retired-season entries if multiple seasons coexist: the frontend follows the current backend's `program.schedule_entries.all` relationship. SchedulePage itself already uses the backend's current-season grouping.
4. Review long-term navigation ownership if editors need to rename seeded slugs or add menu items.
