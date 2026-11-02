"""Builds running-plan.ics from the session list below.

Each session is an all-day event. UIDs are derived from the date, so
editing a session updates it in subscribed calendars rather than
creating a duplicate.
"""

from datetime import date, datetime, timedelta, timezone

PACES = (
    "Paces: easy 6:00-6:30/km (HR under ~143) | tempo 5:05-5:15/km | "
    "5k pace 4:50-5:00/km | fast reps 4:35-4:45/km"
)

# (date, title, details)
SESSIONS = [
    # Block 1, week 1
    (date(2026, 11, 5), "Intervals: 6 x 800 m",
     "1.5 km warm-up easy.\n6 x 800 m @ 4:45-4:50/km, 90 s walk between.\n1 km cool-down easy."),
    (date(2026, 11, 7), "parkrun (easy)", "5 km easy, 6:00-6:30/km. Enjoy it."),
    (date(2026, 11, 8), "Long run 10 km", "10 km easy, 6:00-6:30/km."),
    # Week 2
    (date(2026, 11, 10), "Easy 7 km + strides",
     "7 km easy, then 6 x 15 s strides (fast but relaxed), walk back recovery."),
    (date(2026, 11, 12), "Tempo: 2 x 2 km",
     "2 km warm-up easy.\n2 x 2 km @ 5:10/km, 2 min easy jog between.\n1 km cool-down easy."),
    (date(2026, 11, 14), "parkrun (HARD)", "Full effort 5 km. Target 4:55-5:00/km."),
    (date(2026, 11, 15), "Long run 11 km", "11 km easy, 6:00-6:30/km."),
    # Week 3
    (date(2026, 11, 17), "Easy 7 km", "7 km conversational, 6:00-6:30/km."),
    (date(2026, 11, 19), "Intervals: 5 x 1 km",
     "1.5 km warm-up easy.\n5 x 1 km @ 4:50-4:55/km, 90 s walk between.\n1 km cool-down easy."),
    (date(2026, 11, 21), "parkrun (easy)", "5 km easy, 6:00-6:30/km."),
    (date(2026, 11, 22), "Long run 12 km, fast finish",
     "9 km easy, then last 3 km @ 5:20/km."),
    # Week 4 (lighter)
    (date(2026, 11, 24), "Easy 5 km", "5 km easy. Lighter week."),
    (date(2026, 11, 26), "Fartlek: 8 x 1 min",
     "1.5 km warm-up easy.\n8 x (1 min fast ~4:40/km / 1 min easy).\n1 km cool-down easy."),
    (date(2026, 11, 28), "parkrun (HARD - benchmark)",
     "Full effort 5 km. Compare with 14 Nov."),
    (date(2026, 11, 29), "Long run 8 km", "8 km easy. Lighter week."),
]


def esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def fold(line: str) -> str:
    out, b = [], line.encode("utf-8")
    while len(b) > 75:
        cut = 75 if not out else 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode("utf-8"))
        b = b[cut:]
    out.append(b.decode("utf-8"))
    return "\r\n ".join(out)


def build() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//runningplan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Running plan",
        "X-WR-TIMEZONE:Europe/London",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H",
    ]
    for d, title, details in SESSIONS:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{d:%Y%m%d}-run@runningplan",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{esc(title)}",
            f"DESCRIPTION:{esc(details + chr(10) + chr(10) + PACES)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


if __name__ == "__main__":
    with open("running-plan.ics", "w", newline="") as f:
        f.write(build())
    print(f"Wrote {len(SESSIONS)} sessions to running-plan.ics")
