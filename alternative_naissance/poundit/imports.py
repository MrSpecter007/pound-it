"""
Source-site reference data for the importer.

Legacy URLs each piece of content came from, and a manifest of the images the
site uses. The manifest records the Wix CDN URL for provenance only — nothing
here fetches it. Production pages must not depend on that CDN, so the files are
supplied locally and imported into Wagtail's own image library.
"""

#: Where each kind of content came from on the Wix site.
SOURCE_URLS = {
    "home": "https://www.pounditdj.com/",
    "kids-teen": "https://www.pounditdj.com/kidsreccrews",
    "adult": "https://www.pounditdj.com/adultreccrews",
    "competitive": "https://www.pounditdj.com/competitivecrews",
    "open-training": "https://www.pounditdj.com/schedule",
    "other": "https://www.pounditdj.com/schedule",
    "schedule": "https://www.pounditdj.com/schedule",
    "faculty": "https://www.pounditdj.com/faculty",
    "events": "https://www.pounditdj.com/event-tickets",
    "important-dates": "https://www.pounditdj.com/importantdates",
    "school-programs": "https://www.pounditdj.com/schoolprograms",
    "workshops": "https://www.pounditdj.com/workshops",
    "waiver": "https://www.pounditdj.com/waiver",
}

#: Legacy path -> new path. Phase 8 turns these into Wagtail redirects.
URL_MAP = {
    "/kidsreccrews": "/programs/kids-teen/",
    "/adultreccrews": "/programs/adult/",
    "/competitivecrews": "/programs/competitive/",
    "/schedule": "/schedule/",
    "/faculty": "/faculty/",
    "/workshops": "/events/workshop/",
    "/schoolprograms": "/school-programs/",
    "/importantdates": "/important-dates/",
    "/waiver": "/legal/waiver/",
    "/event-tickets": "/events/",
    # The source page is titled "School Residencies and Afterschool Programs",
    # so afterschool lands there. Flagged for confirmation.
    "/afterschool": "/school-programs/",
}

#: Legacy paths whose destination is an inference rather than a stated mapping.
URL_MAP_NEEDS_CONFIRMATION = ["/afterschool"]

#: Images the source site uses.
#:
#: ``stem`` is the filename the importer looks for in the supplied folder, with
#: any extension. ``aliases`` are other spellings that have actually turned up.
#: ``source_url`` is provenance: where the file came from, so whoever collects
#: them knows which is which.
IMAGE_SOURCES = [
    {
        "stem": "logo",
        "target": "settings",
        "field": "logo",
        "title": "Pound It Hip Hop Studios logo",
        "description": "The Pound It Hip Hop Studios graffiti logo.",
        "source_url": "https://static.wixstatic.com/media/8614f0_1db03c92779041b0a0ae735e3916a496~mv2.png",
    },
    {
        "stem": "rico",
        "target": "faculty",
        "slug": "rico",
        "title": "Rico",
        "description": "Portrait of Rico, studio owner.",
        "source_url": "https://static.wixstatic.com/media/8614f0_ccb8e32ca85849e6a81d266b7a3119f1~mv2.jpg",
    },
    {
        "stem": "cody",
        # The studio's copy of this portrait is filed as "Cory". Confirmed the
        # same instructor, so the misspelling is accepted rather than renamed.
        "aliases": ["cory"],
        "target": "faculty",
        "slug": "cody",
        "title": "Cody",
        "description": "Portrait of Cody, dance instructor.",
        "source_url": "https://static.wixstatic.com/media/8614f0_0f42a65453a84d9da08e352ff97e4722~mv2.jpg",
    },
    {
        "stem": "leiran",
        "target": "faculty",
        "slug": "leiran",
        "title": "Leiran",
        "description": "Portrait of Leiran, dance instructor.",
        "source_url": "https://static.wixstatic.com/media/8614f0_1d7278f2fd284a44afec7a3b5e8e09b1~mv2.jpg",
    },
    {
        "stem": "nathan",
        "target": "faculty",
        "slug": "nathan",
        "title": "Nathan (Deetz)",
        "description": "Portrait of Nathan, who dances as Deetz.",
        "source_url": "https://static.wixstatic.com/media/8614f0_7a25574c01d24a0f89c1c4dfae7ebc85~mv2.jpg",
    },
    {
        "stem": "dizzylock",
        "target": "faculty",
        "slug": "dizzylock",
        "title": "Dany Antoine (Dizzylock)",
        "description": "Portrait of Dany Antoine, who dances as Dizzylock.",
        "source_url": "https://static.wixstatic.com/media/8614f0_29c20383f72c4bb48caae20d7d44aecf~mv2.jpg",
    },
    {
        "stem": "allen",
        "target": "faculty",
        "slug": "allen",
        "title": "Allen Collado",
        "description": "Portrait of Allen Collado, instructor.",
        "source_url": "https://static.wixstatic.com/media/8614f0_0680559bec4c4846a02c998d53141942~mv2.jpg",
    },
    {
        "stem": "charlee",
        "target": "faculty",
        "slug": "charlee",
        "title": "Charlee Martinez (Difficult C)",
        "description": "Portrait of Charlee Martinez, who dances as Difficult C.",
        "source_url": "https://static.wixstatic.com/media/8614f0_f7913ec8468c4769b76bedc7bf77df9b~mv2.jpeg",
    },
]

#: Faculty with no portrait on the source site.
IMAGES_NOT_AVAILABLE = [
    ("breton", "Occasional instructor, no portrait on the source site."),
    ("genie", "Occasional instructor, no portrait on the source site."),
]

#: Two faculty portraits resolve to the same source filename on the Wix CDN
#: (IMG_0507.jpg) under different media ids. Whoever collects the files should
#: check these two are actually different people before importing.
AMBIGUOUS_IMAGES = ["nathan", "allen"]
