"""Write completed 2026 scores from nflverse and ESPN.

NFL rows come from the nflverse schedule. NBA, college football, and
college basketball rows come from ESPN scoreboards. A game is stored
only when the source marks it final, the Eastern date is on or before
2026-11-14, and the score is not 0-0. Lines are not copied. This does
not price a bet.
"""

from __future__ import annotations

import csv
import io
import json
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

AS_OF = date(2026, 11, 14)
EASTERN = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "scores"
NFL_SOURCE = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={ymd}&limit=300"
COLUMNS = ["game_id", "date", "away", "home", "away_score", "home_score", "status"]


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/csv"},
    )
    last_error: Exception | None = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {403, 429, 500, 502, 503}:
                raise
        except urllib.error.URLError as exc:
            last_error = exc
    if last_error is None:
        raise RuntimeError(url)
    raise last_error


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def nfl_rows() -> list[dict]:
    text = fetch(NFL_SOURCE).decode("utf-8")
    rows = []
    for row in csv.DictReader(io.StringIO(text)):
        if str(row.get("season")) != "2026":
            continue
        played = str(row.get("gameday") or "")
        if not played or date.fromisoformat(played) > AS_OF:
            continue
        away = row.get("away_score")
        home = row.get("home_score")
        if away in (None, "") or home in (None, ""):
            continue
        rows.append(
            {
                "game_id": row.get("game_id") or "",
                "date": played,
                "away": row.get("away_team") or "",
                "home": row.get("home_team") or "",
                "away_score": str(int(float(away))),
                "home_score": str(int(float(home))),
                "status": "final",
            }
        )
    rows.sort(key=lambda item: (item["date"], item["game_id"]))
    if len(rows) < 100 or len({row["game_id"] for row in rows}) != len(rows):
        raise SystemExit(f"nflverse score check failed: {len(rows)} rows")
    return rows


def espn_rows(sport: str, league: str, start: date, end: date) -> list[dict]:
    rows = []
    seen = set()
    day = start
    while day <= end:
        payload = json.loads(fetch(SCOREBOARD.format(sport=sport, league=league, ymd=day.strftime("%Y%m%d"))))
        for event in payload.get("events") or []:
            competition = event["competitions"][0]
            status = competition.get("status", {}).get("type", {}).get("name") or ""
            if status != "STATUS_FINAL":
                continue
            stamp = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(EASTERN)
            if stamp.date() > AS_OF:
                continue
            home = next((side for side in competition["competitors"] if side.get("homeAway") == "home"), None)
            away = next((side for side in competition["competitors"] if side.get("homeAway") == "away"), None)
            if home is None or away is None:
                continue
            away_score = score_value(away.get("score"))
            home_score = score_value(home.get("score"))
            if away_score is None or home_score is None or (away_score == 0 and home_score == 0):
                continue
            game_id = str(event.get("id") or "")
            if game_id in seen:
                continue
            seen.add(game_id)
            rows.append(
                {
                    "game_id": game_id,
                    "date": stamp.date().isoformat(),
                    "away": away["team"].get("abbreviation") or "",
                    "home": home["team"].get("abbreviation") or "",
                    "away_score": str(away_score),
                    "home_score": str(home_score),
                    "status": "final",
                }
            )
        day += timedelta(days=1)
    rows.sort(key=lambda item: (item["date"], item["game_id"]))
    return rows


def score_value(score: object) -> int | None:
    if isinstance(score, dict):
        score = score.get("displayValue", score.get("value"))
    if score in (None, ""):
        return None
    return int(float(score))


def main() -> None:
    nfl = nfl_rows()
    nba = espn_rows("basketball", "nba", date(2026, 10, 20), AS_OF)
    ncaa = espn_rows("football", "college-football", date(2026, 8, 20), AS_OF)
    ncaab = espn_rows("basketball", "mens-college-basketball", date(2026, 11, 1), AS_OF)
    write_rows(OUT_DIR / "nfl_2026.csv", nfl)
    write_rows(OUT_DIR / "nba_2026.csv", nba)
    write_rows(OUT_DIR / "ncaa_football_2026.csv", ncaa)
    write_rows(OUT_DIR / "ncaab_2026.csv", ncaab)
    if len(nba) < 50 or len(ncaa) < 100:
        raise SystemExit(f"ESPN score check failed nba {len(nba)} ncaa {len(ncaa)}")
    print(f"nfl {len(nfl)} {nfl[0]['date']} {nfl[-1]['date']}")
    print(f"nba {len(nba)} {nba[0]['date']} {nba[-1]['date']}")
    print(f"ncaa football {len(ncaa)} {ncaa[0]['date']} {ncaa[-1]['date']}")
    print(f"ncaab {len(ncaab)}")


if __name__ == "__main__":
    main()
