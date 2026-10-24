# Season and Episode Scores Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every episode and season gets a score. The scores are shown on the show's page, and Non-stop Favs: TV leans towards the better episodes.

**Architecture:**
- **Storing:** TMDB's per-episode rating and vote count are stored by the existing season fetch (`enrich_episode_titles`).
- **Working out:** the scores are computed on demand from what's loaded (`episode_scores`, `season_scores`) and passed to the page by `show_detail`.
- **The channel:** the favourites channel repeats better episode blocks in its loop before shuffling.

**Tech Stack:** Python stdlib and SQLite (`nextup.py`), with the PAGE HTML/JS embedded in `nextup.py`. Tests use the repo's own `check()` style, against a `devserve.isolate` sandbox.

**Spec:** `docs/superpowers/specs/2026-10-24-episode-scores-design.md`

## Global Constraints

- **Your rating wins:** an episode rating you've given overrides everything.
- **Few votes:** below 20 TMDB votes, an episode's rating is blended with the neighbouring episodes either side in the same season, weighted by votes. With no votes it uses the season average, then the show's TMDB rating.
- **Your show rating** moves the score a quarter of the way from the show's TMDB average towards your rating.
- **Rewatches:** watched to the end more than once adds +0.3 per extra time, up to +0.9.
- **Clamp** to 1–10, with one decimal place.
- **A season's score** is the vote-weighted average of its episodes' scores. An episode you've rated counts as 100 votes. Season 0 (specials) is scored but never counts towards the show.
- **Scores are never stored.** They're worked out when the show's page is asked for.
- **Only Non-stop Favs: TV changes.** It's weighted by `(score − 4)²` with a floor of 1, and stays deterministic per day (`channel_rng`). No other channel changes, and neither do Now or Continue.
- PAGE is a raw string: in HTML markup use real characters; `\u` escapes only inside JS strings.
- On the phone, a `let` read before its line has run crashes the page, so new top-level page variables are `var`.

## Review Focus

1. **A show with no TMDB ratings at all** (an obscure show, or no TMDB key): no chips, no scores, no "Best episodes" row. The page must look exactly as it does today, with no "0.0" anywhere. *Task 3 tests this.*
2. **Season 0 specials** with high votes mustn't count towards the show's scores or become "Best episodes". *Task 2 and Task 3 test this.*
3. **The PC's library on the phone:** a greyed show from the PC has no stored ratings, and its page must still open. *Task 3 tests that `show_detail` copes when every rating is missing.*
4. **A favourites channel with only one show, or with episodes that have no scores:** the schedule must still build and every block must still appear. *Task 4 tests this.*
5. **The backfill must not refetch every season on every scan.** Once a season has `tmdb_votes`, it's left alone. *Task 1 tests this.*

---

### Task 1: Store TMDB's episode ratings

**Files:**
- Modify: `nextup.py`:
  - the column migrations list, near `("episodes", "last_played", "TEXT")`;
  - `enrich_episode_titles`;
  - `Library._episode`.
- Test: `tests/episode_scores_test.py` (new, with `isolate(n, tempfile.gettempdir()/"nextup_epscores")`).
- Add `("episode scores", "episode_scores_test.py")` to `tests/run_all.py`.

**Interfaces:**
- Produces:
  - new columns `episodes.tmdb_rating REAL` and `episodes.tmdb_votes INTEGER`;
  - the `LIB.episodes` dicts carry `"tmdb_rating"` (float, 0 when unknown) and `"tmdb_votes"` (int, 0).

- [ ] **Step 1: Write the failing test.** Stub `n.tmdb`: for a path `/tv/<id>/season/1`, return `{"episodes": [{"episode_number": 1, "name": "A", "overview": "", "still_path": None, "runtime": 30, "vote_average": 8.4, "vote_count": 120}, {"episode_number": 2, ..., "vote_average": 6.1, "vote_count": 3}]}`. Record each call made. Insert a show (with `tmdb_id`) and its two episodes, then run `n.enrich_episode_titles(conn)`.
  - `check("episode ratings are stored", ...)`: episode 1 has `tmdb_rating == 8.4` and `tmdb_votes == 120`.
  - `check("a season with ratings isn't fetched again", ...)`: after a second `enrich_episode_titles`, there are no new calls.
  - `check("the library carries them", ...)`: after `n.LIB.loaded_at = 0`, the `LIB.episodes` dict has `tmdb_rating == 8.4`.
- [ ] **Step 2:** Run `PYTHONIOENCODING=utf-8 python tests/episode_scores_test.py`. Expected: FAIL, because there is no `tmdb_rating` column.
- [ ] **Step 3:** Add the two columns to the migration list.
  - In `enrich_episode_titles`, also write `vote_average` to `tmdb_rating` and `vote_count` to `tmdb_votes`.
  - Add `OR e.tmdb_votes IS NULL` to the season query's WHERE clause, so stored libraries get backfilled once.
  - Store `0` for an episode that has no votes, so it isn't fetched again.
  - In `_episode`, add the two keys, reading them with `r["tmdb_rating"] or 0` and `r["tmdb_votes"] or 0`.
- [ ] **Step 4:** Run the test. Expected: PASS.
- [ ] **Step 5:** Commit: "Episode scores: store TMDB's rating and votes per episode".

### Task 2: The scores

**Files:**
- Modify: `nextup.py`. New functions go just above `show_detail`.
- Test: `tests/episode_scores_test.py`.

**Interfaces:**
- Consumes: the `LIB.episodes` keys from Task 1, plus `userrating`, `season`, `episode`, `tvshowid`; `LIB.shows` `rating` (TMDB) and `userrating`; `history` rows with `event='watched'` and `kind='episode'`, keyed by `item_id`.
- Produces:
  - `episode_scores(show_id: int) -> dict[int, float]`, mapping episode id to a score. Episodes with nothing to go on (no rating of yours, no votes anywhere in the show, and no show TMDB rating) are left out.
  - `season_scores(show_id: int, scores: dict) -> dict[int, float]`, mapping season number to a score. Season 0 is included, but `show_score` isn't.
  - Constants: `EPISODE_FEW_VOTES = 20`, `EPISODE_REWATCH_STEP = 0.3` and `EPISODE_REWATCH_MAX = 0.9`.

- [ ] **Step 1: Write failing tests.** Build one show (TMDB rating 7.0) with season 1, episodes 1–4, using `tmdb_rating`/`tmdb_votes` of (8.0, 500), (9.5, 3), (6.0, 400) and (0, 0). Add a season 0 special at (9.9, 900).
  - **Your rating wins:** set episode 3's `userrating` to 10, then `episode_scores()[ep3] == 10.0`.
  - **Few votes blend:** episode 2's score is strictly between 8.0 and 9.5, and closer to the neighbours' vote-weighted mean than to 9.5.
  - **No votes falls back to the season:** episode 4's score equals the season's vote-weighted mean of the TMDB ratings, within 0.05.
  - **Your show rating nudges:** with show `userrating` 9 against TMDB 7.0, episode 1 scores 8.0 + 0.25×(9 − 7.0) = 8.5.
  - **Rewatches:** insert 3 `watched` history rows for episode 1, which adds 0.6. Insert 6, and it's capped at +0.9.
  - **Clamp:** a fake rating of 12 gives 10.0.
  - **Seasons are vote-weighted, and specials don't count:** `season_scores` gives season 1 the vote-weighted mean (episode 3 counting as 100 votes). Season 0 is present, and isn't averaged into anything.
  - **Nothing to go on:** a show with no votes anywhere, no ratings of yours and no TMDB rating gives `{}`.
- [ ] **Step 2:** Run the tests. Expected: FAIL with `AttributeError: episode_scores`.
- [ ] **Step 3:** Implement both functions. Do the rewatch count with one SQL query per call: `SELECT item_id, COUNT(*) FROM history WHERE kind='episode' AND event='watched' AND item_id IN (...) GROUP BY item_id`. "Neighbours" means the nearest episodes either side in the same season (±1), weighted by votes. Below `EPISODE_FEW_VOTES`, blend as `(r·v + N·nv) / (v + nv)`, where N is the neighbours' vote-weighted mean and nv is `EPISODE_FEW_VOTES − v`. Round to one decimal place.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Commit: "Episode scores: the score, from TMDB, your ratings and rewatches; seasons from their episodes".

### Task 3: On the show's page

**Files:**
- Modify: `nextup.py`:
  - `show_detail`;
  - the page's `seasonBrowser` and `episodeRow`, plus the CSS next to `.seasontab`.
- Test: `tests/episode_scores_test.py` and `tests/android_core_test.py`, where the page checks go.

**Interfaces:**
- Consumes: `episode_scores` and `season_scores` from Task 2.
- Produces:
  - **On each episode in `show_detail`:**
    - `"score"`: a float, or None;
    - `"star"`: a bool, true when your rating is ≥ 8 or there are ≥ 2 `watched` rows;
    - `"gem"`: a bool, true when unwatched and in the top fifth of the show's season > 0 scores, needing at least 5 scored episodes.
  - **On each season:** `"score"`, a float or None.
  - **Top level:** `"best"`, a list of up to 5 episode dicts. They come from seasons > 0, are sorted by score, and only appear when at least 5 episodes are scored.

- [ ] **Step 1: Write failing tests.**
  - `check("show_detail: scores on episodes and seasons", ...)` on the Task 2 show.
  - `check("best: five, no specials", ...)`.
  - `check("star for rewatched", ...)` and `check("gem for an unwatched high-scorer", ...)`.
  - `check("a show with nothing to go on looks as it did", ...)`: every `score` is None, `best == []`, and no season has a score.
  - Page checks in `android_core_test.py`:
    - `'seasonscore'` and `'epscore'` and `'bestrow'` are in `page_src`;
    - the text `"Best episodes"` is in `page_src`.
- [ ] **Step 2:** Run both test files. Expected: FAIL.
- [ ] **Step 3: Implement.**
  - **Season tab:** append `<span class="seasonscore">7.9</span>` when the season has a score. The highest-scoring season (above 0) gets the class `top`, and the lowest gets `low` (dimmer). Only mark them when two or more seasons have scores.
  - **Episode row:** add `<span class="epscore">8.4</span>` before PLAY, coloured with `--h: hueFor(score)`, the library badge scale. Show `★` when `star`. Show a muted `?` when `gem`, with the title "Good in theory: you haven't seen it".
  - **Best episodes:** when `d.best.length`, show a row above the season bar, headed "Best episodes". It holds up to 5 compact rows built with the same `episodeRow`.
- [ ] **Step 4:** Run both. Expected: PASS. Check visually in the phone sandbox (`tests/phone_serve.py`, at 360 wide) on a show with several seasons.
- [ ] **Step 5:** Commit: "Show page: season and episode scores, marks, and Best episodes".

### Task 4: Non-stop Favs: TV leans to the better episodes

**Files:**
- Modify: `nextup.py`, in the `ctype in ("favourites", "watchlist")` branch of `channel_blocks`.
- Test: `tests/episode_scores_test.py`.

**Interfaces:**
- Consumes: `episode_scores`.
- Produces: a channel flag, `"weight_by_score": True`, on the `favstv` channel only.

- [ ] **Step 1: Write failing tests.** Favourite the Task 2 show, then build `channel_blocks(favstv)`.
  - `check("better blocks come round more often", ...)`: the block holding episode 3 (score 10) appears more times than the block holding the lowest-scoring episode.
  - `check("every block still comes round", ...)`: every block id from the unweighted list is present at least once.
  - `check("the same day, the same order", ...)`: two calls are equal.
  - `check("a show with no scores builds as before", ...)`: with no scores, the block count equals the unweighted count.
  - `check("only the TV favourites channel is weighted", ...)`: `favs` (Films) and `watchlist` have no `weight_by_score`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3: Implement.**
  - For a channel with `weight_by_score`, give each episode block the mean score of its episodes.
  - Then `copies = min(3, max(1, round((max(score, 4) − 4)² / 4)))`. A block with no score gets 1.
  - Repeat each block `copies` times before the existing sort and `channel_rng(channel).shuffle`.
  - Add `"weight_by_score": True` to the `favstv` entry in `CHANNELS`, with a one-line comment.
- [ ] **Step 4:** Run the tests. Expected: PASS. Then run the full `tests/run_all.py`. Expected: every suite passes.
- [ ] **Step 5:** Commit: "Non-stop Favs: TV comes round to the better episodes more often". Add a CHANGELOG line under 0.2.1.
