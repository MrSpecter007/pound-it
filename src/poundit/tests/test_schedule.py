from datetime import time
from types import SimpleNamespace

from django.test import SimpleTestCase

from poundit.schedule import build_timelines


class TimelineTests(SimpleTestCase):
    def timeline(self, first, second):
        return build_timelines([{
            "weekday": 0, "label": "Monday",
            "rooms": [
                {"room": "Notorious BIG", "entries": first},
                {"room": "Black & Yellow", "entries": second},
            ],
        }])[0]

    def entry(self, start, end):
        return SimpleNamespace(start_time=time(*start), end_time=time(*end))

    def test_simultaneous_classes_share_start_and_end_rows(self):
        day = self.timeline(
            [self.entry((17, 15), (18, 0))],
            [self.entry((17, 15), (18, 0))],
        )
        left, right = day["rooms"]
        self.assertNotEqual(left["column"], right["column"])
        self.assertEqual(left["sessions"][0]["start_row"], right["sessions"][0]["start_row"])
        self.assertEqual(left["sessions"][0]["end_row"], right["sessions"][0]["end_row"])

    def test_partial_overlap_and_gaps_use_actual_time_boundaries(self):
        day = self.timeline(
            [self.entry((17, 15), (18, 0)), self.entry((18, 15), (19, 0))],
            [self.entry((17, 0), (18, 0)), self.entry((18, 0), (18, 45))],
        )
        left, right = day["rooms"]
        self.assertGreater(left["sessions"][0]["start_row"], right["sessions"][0]["start_row"])
        self.assertEqual(left["sessions"][0]["end_row"], right["sessions"][0]["end_row"])
        self.assertEqual(right["sessions"][0]["end_row"], right["sessions"][1]["start_row"])
        self.assertGreater(left["sessions"][1]["start_row"], left["sessions"][0]["end_row"])

    def test_non_quarter_hour_times_are_not_rounded(self):
        day = self.timeline([self.entry((17, 10), (17, 55))], [self.entry((17, 20), (18, 0))])
        self.assertEqual([tick["label"] for tick in day["ticks"]], ["5:10 PM", "5:20 PM", "5:55 PM", "6:00 PM"])
        self.assertTrue(day["row_sizes"].startswith("minmax(30px, auto)"))

    def test_empty_studio_remains_alongside_other_studio(self):
        day = self.timeline([self.entry((17, 15), (18, 0))], [])
        self.assertEqual(len(day["rooms"]), 2)
        self.assertEqual(day["rooms"][1]["sessions"], [])

    def test_empty_schedule(self):
        self.assertEqual(build_timelines([]), [])
