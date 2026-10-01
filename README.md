# gram-post — the Gazette's posts, on a schedule, without the Mac

Every morning at 7:30 New York time a GitHub run posts whatever `queue.json` has for
that day to Instagram (carousel) and the Facebook Page, through Meta's own API, and
records the post ids in `posted.json`. Nothing is clicked in a browser.

    ./queue                                   what's lined up, what went out
    ./queue <slug> <YYYY-MM-DD> [HH:MM]       add one carousel from the Gazette repo
    ./queue --from <file.json>                add a run of them (gram/oct-scheduled.json works)
    ./queue --remove <slug>

Slides come from `~/Projects/quackery-gazette/gram/carousels/<slug>/` and are converted
to JPEG (the API takes nothing else). The images are public in this repo the moment
they're queued, so queue a piece only once it's cleared to post.

Rules the script keeps: one post per item per platform, ever; nothing posts before its
date and time; anything whose day passed unposted is reported as MISSED, never posted
late (re-date it with `./queue`). Without the Meta secrets every run is a dry run.

## One-time hookup (about ten minutes, at the Mac)

1. developers.facebook.com → My Apps → **Create App**. Use case: **Other**; type:
   **Business**. Name it anything ("Gazette poster"). Leave it in development mode —
   as the app's own admin you can post to your own Page and Instagram without review.
2. In the app: Settings → Basic → copy the **App ID** and **App Secret**.
3. developers.facebook.com/tools/explorer → pick the app → **Get User Access Token**
   with these permissions: `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`,
   `business_management`. When Facebook asks which Pages and Instagram accounts, tick the
   Gazette's. Copy the token.
4. In Terminal: `cd ~/Projects/gram-post && ./connect` — paste the three values when
   asked (they aren't shown or saved). It finds the Page and the linked Instagram account,
   converts the token to one that doesn't expire, and stores it as repo secrets.
5. Check it: GitHub → Actions → post → Run workflow (dry run ticked). The log should say
   anything due, and whether its images are reachable at their public URLs.

If the Instagram account isn't linked to the Page, `./connect` says so; link it in Business
Suite → Settings → Instagram accounts, then rerun.

## Files
- `post.py` — the daily run (stdlib only). `--dry-run` posts nothing.
- `queue` — the Mac-side tool. Commits and pushes on every change.
- `connect` — the one-time token hookup.
- `.github/workflows/post.yml` — 11:32 and 12:32 UTC daily; the second run is a no-op
  when the first posted (covers EDT and EST).
