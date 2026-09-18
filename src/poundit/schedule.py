"""Presentation data for studios sharing one time axis per day."""


def build_timelines(schedule):
    timelines = []
    for day in schedule:
        entries = [entry for room in day["rooms"] for entry in room["entries"]]
        if not entries:
            continue

        def minutes(time):
            return time.hour * 60 + time.minute

        # Every start and end is a grid boundary, including off-quarter times.
        boundaries = sorted({
            minutes(time)
            for entry in entries
            for time in (entry.start_time, entry.end_time)
        })
        rows = {minute: index + 1 for index, minute in enumerate(boundaries)}
        ticks = []
        for minute in boundaries:
            hour, minute_part = divmod(minute, 60)
            ticks.append({
                "row": rows[minute],
                "label": f"{hour % 12 or 12}:{minute_part:02d} {'AM' if hour < 12 else 'PM'}",
            })
        timelines.append({
            "weekday": day["weekday"],
            "label": day["label"],
            "ticks": ticks,
            "row_sizes": " ".join(
                f"minmax({(end - start) * 3}px, auto)"
                for start, end in zip(boundaries, boundaries[1:])
            ) + " 2rem",
            "rooms": [
                {
                    "room": column["room"],
                    "column": index + 2,
                    "sessions": [
                        {
                            "entry": entry,
                            "start_row": rows[minutes(entry.start_time)],
                            "end_row": rows[minutes(entry.end_time)],
                        }
                        for entry in column["entries"]
                    ],
                }
                for index, column in enumerate(day["rooms"])
            ],
        })
    return timelines
