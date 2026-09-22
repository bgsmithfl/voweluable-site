# voweluable-site

The live voweluable.com site **plus** the nightly automation that keeps it fed:

- `index.html`, `service-worker.js`, favicons… — the game (deploying = editing these here)
- `scripts/archive_gen.py` — builds `/archive/`: one SEO page per completed board
  (board letters, era-correct vowel prices, champion, full scoreboard, best findable
  words pulled from the game's own dictionary) + archive index + sitemap.xml
- `scripts/daily_champion.py` — yesterday's champion card + Facebook post text
  → `output/latest/` (records get a starburst card and an AUDIT-FIRST warning;
  dethronings get the toppled crown; streaks get labeled)
- `.github/workflows/nightly.yml` — runs both at 12:30 AM ET, commits, and the
  commit triggers a Netlify deploy. Today's board is never revealed early.

## One-time setup (~15 min)
1. **Create a PRIVATE GitHub repo** named `voweluable-site`; upload everything in
   this folder (drag the whole folder contents into "Add file → Upload files";
   verify `.github/workflows/nightly.yml` survived — if not, create it via
   "Add file → Create new file" and paste).
   NOTE: repo is private, but the SITE is public anyway — private just hides the scripts.
2. **Secrets** — repo → Settings → Secrets and variables → Actions → add
   `SUPABASE_URL` and `SUPABASE_ANON_KEY` (Supabase → Settings → API; anon key,
   NOT service_role).
3. **Link Netlify to the repo** — Netlify → your Voweluable site →
   Site configuration → Build & deploy → "Link repository" → GitHub →
   `voweluable-site`, branch `main`. Build command: none. Publish directory: `.`
   (netlify.toml already says this). From now on every commit deploys;
   drag-and-drop is retired.
4. **First run** — repo → Actions → "Nightly archive + champion card" →
   Run workflow. This BACKFILLS the entire archive (every day ever played),
   rebuilds sitemap.xml, and produces today's card in `output/latest/`.
   Netlify deploys it automatically. Check voweluable.com/archive/.
5. **Tell Google** — Google Search Console (search.google.com/search-console),
   add property voweluable.com (DNS or HTML-file verification), submit
   `https://voweluable.com/sitemap.xml`. This is what makes the archive
   pages start earning search traffic.

## Daily routine after setup
8 AM: open `output/latest/` on your phone → save `champion.png`, copy `post.txt`,
post to Facebook. Everything else is automatic.

## Updating the game itself
Edit `index.html` in GitHub (or upload a replacement), **bump CACHE_NAME in
`service-worker.js`** in the same commit, commit → Netlify deploys.

## Era note
`scripts/common.py` → `TATER_RULE_HN = 20260915` marks the repricing date so old
archive pages show the historically correct prices. If prices ever change again,
add a new era there.
