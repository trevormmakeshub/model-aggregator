This repo ranks NFL, college football, NBA, and college basketball games by the mean z-score of many outside spread models against the posted line.

ThePredictionTracker files are line columns. They are not final scores and they are not live book prices.

data/scores is the completed-game feed through 2026-11-14. python scripts/pull_scores.py rewrites it. NFL rows are the nflverse schedule: 137 games, 2026-09-09 through 2026-11-12. NBA rows are ESPN finals: 188 games, 2026-10-20 through 2026-11-14. College football rows are ESPN finals: 748 games, 2026-08-29 through 2026-11-14. College basketball rows are ESPN scoreboard finals: 110 games, 2026-11-01 through 2026-11-14. That scoreboard is the public daily board, not a claim that every college game is listed.

ESPN abbreviations are stored as the scoreboard returns them. No spread or total is copied. These files do not price a bet.
