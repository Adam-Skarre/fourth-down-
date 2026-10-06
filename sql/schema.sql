-- All values are normalized by Python before insert. Composite keys prevent double counting.
CREATE TABLE player_games (
    player_id TEXT NOT NULL,
    name TEXT NOT NULL,
    position TEXT NOT NULL CHECK (position IN ('QB','RB','WR','TE')),
    team TEXT NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL CHECK (week BETWEEN 1 AND 18),
    opponent TEXT NOT NULL,
    standard_points REAL NOT NULL,
    receptions INTEGER NOT NULL CHECK (receptions >= 0),
    PRIMARY KEY (player_id, season, week)
);
CREATE INDEX history_lookup ON player_games(season, week, player_id);
