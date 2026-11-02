"""Builds Apple Workout app custom workouts (.workout files).

The format was worked out from a workout exported from the Workout app.
It is a protobuf message:

  9: UUID string
  11: custom workout
      1: activity type (37 = running)
      2: location (3 = outdoor)
      3: display name
      4: warm-up step
      5: block (repeated)
          1: interval (repeated)
              1: purpose (1 = work, 2 = recovery)
              2: step
          2: iterations
      6: cool-down step
  1000: 1, 1002: 5 (format markers, copied as-is)

  step:  1: goal   2: alert (optional)
  goal:  distance -> {1: 3, 4: {1: 1, 2: metres}}
         time     -> {1: 1, 2: {1: 1, 2: seconds}}
  alert: {1: 2, 2: 2, 4: {2: {1: min speed, 2: max speed}}}
         speed  -> {1: {1: 1, 2: metres}, 2: {1: 1, 2: 1.0 seconds}}

Run `python3 workouts.py` to write every workout into workouts/.
"""

import os
import struct
import uuid

# ---------- protobuf encoding ----------

def varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def f_varint(field: int, n: int) -> bytes:
    return varint(field << 3) + varint(n)


def f_double(field: int, x: float) -> bytes:
    return varint(field << 3 | 1) + struct.pack("<d", x)


def f_bytes(field: int, b: bytes) -> bytes:
    return varint(field << 3 | 2) + varint(len(b)) + b


# ---------- workout pieces ----------

def quantity(value: float) -> bytes:
    return f_varint(1, 1) + f_double(2, value)


def pace_to_speed(pace: str) -> float:
    m, s = pace.split(":")
    return 1000.0 / (int(m) * 60 + int(s))


def speed(mps: float) -> bytes:
    return f_bytes(1, quantity(mps)) + f_bytes(2, quantity(1.0))


def pace_alert(fast: str, slow: str) -> bytes:
    rng = f_bytes(1, speed(pace_to_speed(slow))) + f_bytes(2, speed(pace_to_speed(fast)))
    return f_varint(1, 2) + f_varint(2, 2) + f_bytes(4, f_bytes(2, rng))


def dist(metres: float) -> bytes:
    return f_varint(1, 3) + f_bytes(4, quantity(metres))


def secs(seconds: float) -> bytes:
    return f_varint(1, 1) + f_bytes(2, quantity(seconds))


def step(goal: bytes, pace=None) -> bytes:
    out = f_bytes(1, goal)
    if pace:
        out += f_bytes(2, pace_alert(*pace))
    return out


WORK, RECOVERY = 1, 2


def block(intervals, iterations: int) -> bytes:
    out = b""
    for purpose, st in intervals:
        out += f_bytes(1, f_varint(1, purpose) + f_bytes(2, st))
    return out + f_varint(2, iterations)


def workout(name: str, blocks, warmup=None, cooldown=None, uid=None) -> bytes:
    body = f_varint(1, 37) + f_varint(2, 3) + f_bytes(3, name.encode())
    if warmup:
        body += f_bytes(4, warmup)
    for b in blocks:
        body += f_bytes(5, b)
    if cooldown:
        body += f_bytes(6, cooldown)
    uid = uid or str(uuid.uuid5(uuid.NAMESPACE_URL, "runningplan/" + name)).upper()
    return (f_bytes(9, uid.encode()) + f_bytes(11, body)
            + f_varint(1000, 1) + f_varint(1002, 5))


# ---------- the plan's workouts ----------

EASY = ("6:00", "6:30")


def single(name, metres, pace):
    return workout(name, [block([(WORK, step(dist(metres), pace))], 1)])


def build_all():
    w = {}
    w["Intervals 6x800m"] = workout(
        "Intervals 6x800m",
        [block([(WORK, step(dist(800), ("4:45", "4:50"))),
                (RECOVERY, step(secs(90)))], 6)],
        warmup=step(dist(1500), EASY), cooldown=step(dist(1000)))
    w["Tempo 2x2k"] = workout(
        "Tempo 2x2k",
        [block([(WORK, step(dist(2000), ("5:05", "5:15"))),
                (RECOVERY, step(secs(120)))], 2)],
        warmup=step(dist(2000), EASY), cooldown=step(dist(1000)))
    w["Intervals 5x1k"] = workout(
        "Intervals 5x1k",
        [block([(WORK, step(dist(1000), ("4:50", "4:55"))),
                (RECOVERY, step(secs(90)))], 5)],
        warmup=step(dist(1500), EASY), cooldown=step(dist(1000)))
    w["Fartlek 8x1min"] = workout(
        "Fartlek 8x1min",
        [block([(WORK, step(secs(60), ("4:35", "4:45"))),
                (RECOVERY, step(secs(60)))], 8)],
        warmup=step(dist(1500), EASY), cooldown=step(dist(1000)))
    w["Easy 7k + strides"] = workout(
        "Easy 7k + strides",
        [block([(WORK, step(dist(7000), EASY))], 1),
         block([(WORK, step(secs(15))), (RECOVERY, step(secs(45)))], 6)])
    w["Long 12k fast finish"] = workout(
        "Long 12k fast finish",
        [block([(WORK, step(dist(9000), EASY)),
                (WORK, step(dist(3000), ("5:15", "5:25")))], 1)])
    w["parkrun hard"] = single("parkrun hard", 5000, ("4:55", "5:00"))
    for km in (5, 7, 8, 10, 11):
        w[f"Easy {km}k"] = single(f"Easy {km}k", km * 1000, EASY)
    return w


def slug(name: str) -> str:
    return "-".join("".join(c if c.isalnum() else " " for c in name.lower()).split())


if __name__ == "__main__":
    os.makedirs("workouts", exist_ok=True)
    for old in os.listdir("workouts"):
        os.remove(os.path.join("workouts", old))
    for name, data in build_all().items():
        with open(os.path.join("workouts", slug(name) + ".workout"), "wb") as f:
            f.write(data)
        print("wrote", name)
