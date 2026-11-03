"""Builds running-plan.ics from the session list below.

Each session is an all-day event. UIDs are derived from the date, so
editing a session updates it in subscribed calendars rather than
creating a duplicate.
"""

from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

from workouts import slug

RAW = "https://raw.githubusercontent.com/Jorggs/runningplan/main/workouts/"

# Which Apple Watch workout goes with each session (by date)
WORKOUT_FOR = {
    date(2026, 11, 5): "Intervals 6x800m",
    date(2026, 11, 7): "Easy 5k",
    date(2026, 11, 8): "Easy 10k",
    date(2026, 11, 10): "Easy 7k + strides",
    date(2026, 11, 12): "Tempo 2x2k",
    date(2026, 11, 14): "parkrun hard",
    date(2026, 11, 15): "Easy 11k",
    date(2026, 11, 17): "Easy 7k",
    date(2026, 11, 19): "Intervals 5x1k",
    date(2026, 11, 21): "Easy 5k",
    date(2026, 11, 22): "Long 12k fast finish",
    date(2026, 11, 24): "Easy 5k",
    date(2026, 11, 26): "Fartlek 8x1min",
    date(2026, 11, 28): "parkrun hard",
    date(2026, 11, 29): "Easy 8k",
}

# (date, title, details)
SESSIONS = [
    # Block 1, week 1
    (date(2026, 11, 5), "Intervals: 6 x 800m",
     "1.5k warm-up at 6:00-6:30\nRepeat 6 times:\n800m at 4:45-4:50\n90s walk\n1k warm down"),
    (date(2026, 11, 7), "parkrun (easy)", "5k at 6:00-6:30"),
    (date(2026, 11, 8), "Long run 10k", "10k at 6:00-6:30"),
    # Week 2
    (date(2026, 11, 10), "Easy 7k + strides",
     "7k at 6:00-6:30\nRepeat 6 times:\n15s stride at 4:30-4:50\nWalk back"),
    (date(2026, 11, 12), "Tempo: 2 x 2k",
     "2k warm-up at 6:00-6:30\nRepeat 2 times:\n2k at 5:10\n2 min easy jog\n1k warm down"),
    (date(2026, 11, 14), "parkrun (HARD)", "5k full effort at 4:55-5:00"),
    (date(2026, 11, 15), "Long run 11k", "11k at 6:00-6:30"),
    # Week 3
    (date(2026, 11, 17), "Easy 7k", "7k at 6:00-6:30"),
    (date(2026, 11, 19), "Intervals: 5 x 1k",
     "1.5k warm-up at 6:00-6:30\nRepeat 5 times:\n1k at 4:50-4:55\n90s walk\n1k warm down"),
    (date(2026, 11, 21), "parkrun (easy)", "5k at 6:00-6:30"),
    (date(2026, 11, 22), "Long run 12k, fast finish",
     "9k at 6:00-6:30\n3k at 5:20"),
    # Week 4 (lighter)
    (date(2026, 11, 24), "Easy 5k", "5k at 6:00-6:30"),
    (date(2026, 11, 26), "Fartlek: 8 x 1 min",
     "1.5k warm-up at 6:00-6:30\nRepeat 8 times:\n1 min at 4:40\n1 min easy\n1k warm down"),
    (date(2026, 11, 28), "parkrun (HARD - benchmark)",
     "5k full effort at 4:55-5:00\nCompare with 14 Nov"),
    (date(2026, 11, 29), "Long run 8k", "8k at 6:00-6:30"),
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
        extra = []
        if d in WORKOUT_FOR:
            url = RAW + slug(WORKOUT_FOR[d]) + ".workout"
            sc = ("shortcuts://run-shortcut?name=Open%20Workout&input=text&text="
                  + quote(url, safe=""))
            details += (f"\n\nLoad on Apple Watch: {sc}"
                        f"\n\nWorkout file: {url}")
            extra = [f"URL:{sc}", f"ATTACH;FMTTYPE=application/octet-stream:{url}"]
        lines += [
            "BEGIN:VEVENT",
            f"UID:{d:%Y%m%d}-run@runningplan",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{esc(title)}",
            f"DESCRIPTION:{esc(details)}",
            *extra,
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


if __name__ == "__main__":
    with open("running-plan.ics", "w", newline="") as f:
        f.write(build())
    print(f"Wrote {len(SESSIONS)} sessions to running-plan.ics")
