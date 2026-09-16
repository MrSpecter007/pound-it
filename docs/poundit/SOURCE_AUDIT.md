# Source audit and asset provenance

Audited September 12–13, 2026. Brand source: https://www.pounditdj.com/ . Read the actual public pages and rendered DOM/styles; do not interpret this as a pixel-identical reconstruction.

## Observed design

The homepage uses a dark header, centered gold fist logo, hamburger navigation (including desktop), green outlined registration action, full-width dance video with large pale Syne ExtraBold type, a separate season announcement, three program photography links, training-color key, culture stories, studio video/tour, faculty artwork and contact/footer.

Measured homepage CSS palette includes `#131514` (ink), `#27261F` (dark olive), `#EFF0EB` (paper), `#EBF0D2` (pale type), `#FEFF01` (electric yellow), `#FFCB05` (gold), `#ED1C24` (red), `#39FF6D` (bright green), `#1C7D33` (deep green). Source includes additional flyer/accent colors; these are not all promoted to primary UI tokens.

Measured font families: `syne-extrabold` (main hero/section headings), `anton` (season announcement), `madefor-display`, `madefor-display-bold`, `madefor-text` (mixed cards/body/faculty), `fahkwang` (workshop title). Example rendered desktop sizes included ~79px Syne hero, ~35px Anton announcement, 21px Madefor culture headings, and 76px Madefor faculty heading. Sizes vary with Wix viewport scaling.

The reconstruction uses freely licensed Anton as the display face and Arial/Helvetica as a calm system body stack. No Wix-only or proprietary font files were copied. Anton font and OFL were fetched from https://github.com/google/fonts/tree/main/ofl/anton .

## Representative pages

| Page inspected | Evidence / design implication |
| --- | --- |
| `/` | Strong source identity, real dancers, mixed type/color rhythm, separate season line; program links exposed as “Close” in accessibility tree. Give links descriptive labels. |
| `/kidsreccrews` | Program names, ages, times, tuition and inclusions largely embedded in prose; no h1/h2/h3 in inspected main content. Introduce structured facts and heading hierarchy. |
| `/adultreccrews` | LULU 100s and PIBA content; long copy beside promotional images, multiple membership options. Separate schedule/tuition without inventing prices or flattening pricing choices. |
| `/competitivecrews` | Crew imagery and long program paragraphs; no semantic program headings in inspected markup. Keep audition status explicit and independently supplied. |
| `/schedule` | Class timetable is artwork (`8614f0_ea67315a78954f76af46cbdb0c92b553~mv2.png`). Provide real schedule text and mobile day cards. |
| `/faculty` | Portrait/flyer assets, widely varying bios, names sometimes in artwork, large whitespace and leftover Wix placeholder text. Store names and disciplines separately. |
| `/workshops` | Expressive posters, changing fonts, extensive descriptions and registration forms; past sessions remain mixed into the page. Preserve posters intact alongside structured metadata/archive state. |
| `/schoolprograms` | Residency narrative, image-based sample schedule, school/contact inquiry fields, duplicate form content in the extracted DOM. Use one backend form, clear outcomes and a structured sample week. |
| `/importantdates` | Tentative season dates in an unstructured list. Render date objects with semantic time elements and retain tentative context. |
| `/waiver` | Very large heading with awkward word wrapping in the inspected layout; legal body and acceptance form. Use restrained readable type, preserve backend-approved text and processing. |

The source was observed at narrow and desktop viewport sizes. The narrow homepage consent UI occupies much of the first screen; it was dismissed with Deny for the audit. Desktop source navigation also uses a hamburger. Media loading/animations can delay content appearing in screenshots, and the studio video reported unable-to-play in the accessibility tree. The new homepage uses eagerly loaded still photography and visible initial content.

Other source issues observed: duplicate home/contact h1s, generic filename alt text, phone link pointing to a Google search rather than a tel URI, a Terms & Conditions link pointing to the homepage, and leftover editor placeholder copy. These were not carried into the new shell. Navigation now uses the installed local pages. Empty legal pages provide verified source links pending approved migrated copy.

## Source assets retained locally

All media IDs below were read from rendered source image metadata. Original URL prefix: `https://static.wixstatic.com/media/`. The IDs are provenance, not a production content database. These are Pound It source assets reused for the requested reconstruction; broader distribution rights were not independently adjudicated.

| Local file in `static/poundit/images/` | Original media ID | Observed role |
| --- | --- | --- |
| `logo.png` | `8614f0_1db03c92779041b0a0ae735e3916a496~mv2.png` | Gold fist logo, header/footer |
| `crew.jpg` | `8614f0_430fe2e872b54c84bac7cc65e6095289~mv2.jpg` | Revolution crew, performance stage |
| `kids.jpg` | `8614f0_1bb83ff338324d76abdac2a3657ddd4d~mv2.jpg` | Chicos image, kids program entry |
| `adults.jpg` | `8614f0_2f5d8ec6bd484daf929b1f7b98002a7b~mv2.jpg` | Adult crew entry |
| `training.jpg` | `8614f0_a12912a925ed478ebac6b6235bd5dd3e~mv2.jpg` | Difficult C / training |
| `battles.jpeg` | `8614f0_1a1ab974de5d4e82b4047c577623a9f6~mv2.jpeg` | Battle/community circle |
| `competitions.jpg` | `8614f0_845edfdbd96145bb9763dbae8ad34894~mv2.jpg` | Competition community |
| `performances.jpeg` | `8614f0_069120f2a7654e0f90ea9b855e4c43af~mv2.jpeg` | Community performance |
| `community.jpeg` | `8614f0_69409f0219194cd1b2b8f5b85db0b04e~mv2.jpeg` | Community moment |
| `studio.jpg` | `8614f0_f5f86ba8ddf24033be90fff4e73217a0f001.jpg` | Source studio-video poster |
| `faculty.jpg` | `8614f0_0dd5fb725f0241348880ebed19962d9e~mv2.jpg` | Source faculty promotional artwork |

The logo uses the source CDN's 160×160 delivery rendition. Adult, performance and community images use source CDN fit-within-1440px delivery renditions at q85. The remaining images were downloaded from original media URLs. No image-generation replacement, invented dancer, or unauthorized font asset was introduced. The four smaller delivery assets save approximately 7.25 MB compared with their initial downloads. In production, replace editorial static fallbacks with Wagtail image renditions after media import.

Useful source focal-point metadata, percentages: Chicos (49,32), adult entry (51,49), competitive entry (51,39), Difficult C (55,49), competition (49,32), battle (57,24), performance (49,32), faculty artwork (49,33). Apply these as starting points and visually review the different target ratios.

Verified action destinations: registration https://app.gostudiopro.com/online/pounditreddeer ; studio tour https://www.tiktok.com/@poundithiphopstudio/video/7413249064138968326 . Source contact: 5809 51 Ave #4b, Red Deer, AB T4N 4H8; (403) 896-7935; Monday–Thursday 4–9 pm. These defaults need editorial confirmation during migration.
