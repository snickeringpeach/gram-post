# Posting now runs through Metricool (Oct 1 2026)

Meta's developer-app hookup was abandoned. The Gazette's Instagram and Facebook posts are
scheduled in Metricool (app.metricool.com, signed in as lfreaney@gmail.com), which publishes
them itself. Each Metricool post pulls its slides at publish time from this repo's
`images/<slug>/NN.jpg` via raw.githubusercontent.com, so:

- do NOT delete or rename anything in `images/` until the posts using it have gone out
- `queue.json` is emptied so the GitHub workflow never double-posts if Meta secrets are added later

October 2–15 are scheduled in Metricool at 7:30 AM ET. Free plan: 20 posts a month.
