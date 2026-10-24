# Season and episode scores

**Date:** 2026-10-24
**Asked for:** today every episode of a show is treated alike: one rating, one show. Seasons and episodes vary, though. A weak season, a classic episode, one you'd happily watch again, one you've never seen but that sits among ones you love. Something should reflect that. Where (the user's choice, from four): **mainly shown on the show's page** so you can choose for yourself. On top of that, **Non-stop Favs: TV** should lean towards the better episodes. Channels otherwise stay random.

## What it is

Every episode gets **its score**, and every season gets one made from its episodes. They're shown on the show's page. One channel uses them as a weight. Nothing else in the app changes: Now, the other channels and Continue keep going in order.

## Where the numbers come from

1. **TMDB, per episode.** TMDB rates each episode (`vote_average`, `vote_count`). Next Up already fetches each season once to fill in titles, plots, pictures and lengths (`enrich_episode_titles`). The same reply carries the ratings, so the two get stored too: new columns `episodes.tmdb_rating` and `episodes.tmdb_votes`.
   - A backfill reads the seasons already stored. These answers are cached, so it costs nothing extra for seasons already seen.
   - Its condition becomes "no `tmdb_votes` yet" alongside "no title or length".
2. **You.** `episodes.userrating` already exists. A rating you've given an episode overrides everything else.
3. **How often you've watched it.** Every completed sitting is in `history`, so rewatches are already recorded.

## The score (out of 10)

For an episode of a show:

- **Your rating, if you've given one.** That's the score, full stop.
- **Otherwise, start from TMDB's rating for the episode.** Episodes with only a handful of votes are unreliable. Below 20 votes, the rating is blended with its neighbours: the episodes either side of it in the same season, weighted by their own vote counts. With no votes at all it's the season's average. With nothing anywhere it's the show's own TMDB rating.
- **Shift it towards how you feel about the show.** If you've rated the show, move the score a quarter of the way from TMDB's average for the show towards your rating. A show you love lifts all of its episodes a little, but the good ones stay above the weak ones.
- **Rewatched counts in its favour.** Watched to the end more than once adds +0.3 per extra time, up to +0.9.
- **Clamp it to 1–10** and keep one decimal place.

**A season's score** is the vote-weighted average of its episodes' scores. Episodes you've rated count as if they had 100 votes. Season 0 (specials) shows scores but never counts towards the show.

Worked out when the show's page is asked for (`show_detail`), from data already loaded. The scores are not stored, so a new rating or a rewatch shows up straight away. One helper, `episode_scores(show_id) -> {episode_id: score}`, plus `season_scores(...)`.

## On the show's page

- **Season tabs:** each tab shows its season's score as a small chip, e.g. `S3 · 7.9`. The strongest season gets the accent colour and the weakest is shown dimmer. Seasons with too little to go on (no votes and nothing rated) show no chip rather than a guess.
- **Episodes:** each row has a small score on the right, coloured on the same scale as the library's rating badges.
  - ★ if you've rated it 8 or more, or rewatched it.
  - A muted "?" mark on unwatched episodes that score in the top fifth of the show: "good in theory".
- **Best episodes:** a short row of the five highest-scoring episodes across the whole show, at the top of the episode list. Each one plays with a tap, here or on the PC as usual.
- **The phone:** the same show page works on the phone, including picks from the PC's library, which uses the PC's numbers.

## Non-stop Favs: TV

Still random: each programme block is still chosen at random. Better episodes just come up more often. Each episode's chance is weighted by `(score − 4)²`, with a floor so that nothing reaches zero. The schedule stays deterministic for the day (`channel_rng`), so restarting the app doesn't reshuffle it. All other channels are untouched.

## Not in this

- Rating individual episodes from the Rate tab, or prompting for episode ratings. Episodes can already be rated wherever that's offered now; this only reads those ratings.
- Changing what Now or Continue pick. Watching in order stays in order.
- A season or episode chart, beyond the chips and the Best episodes row.

## Testing

- **The score maths:** your rating overrides; few votes blend with the neighbours; no votes falls back to the season and then the show; a rewatch adds to the score and is capped; the result is clamped.
- **Seasons:** a vote-weighted average; specials are left out of the show.
- **The backfill:** the ratings are stored from a season reply (using a fake `tmdb()`), and a season with ratings isn't fetched again.
- **The show page:** carries the season chips, the episode scores, the ★ and "?" marks, and Best episodes.
- **Non-stop Favs: TV:**
  - Over many days, a high-scoring episode comes up more often than a low-scoring one in the same show.
  - Every episode still comes up sometimes.
  - The same day gives the same schedule.

## Changed after first use (2026-10-24)

The score as first built started from TMDB's rating of the episode and nudged it a quarter of the way towards your rating of the show. A show the user loves (I Think You Should Leave, rated 8.5) has episodes only 4–10 people voted on, harshly, so its episodes came out at about 6. The user asked for the score to weigh towards their rating.

The score now starts from your rating of the show, or the show's usual (the vote-weighted mean of its episodes) if you haven't rated it. TMDB then moves it up or down by how that episode compares with the show's usual, scaled by `votes / (votes + 20)`, so a handful of votes barely moves it. Neighbours no longer come into it. Your own episode rating still wins, and rewatches still add.

You can rate an episode yourself by clicking its score on the show's page. It's meant for the odd one the score has wrong.
