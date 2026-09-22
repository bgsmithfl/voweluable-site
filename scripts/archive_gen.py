#!/usr/bin/env python3
"""Generates /archive/ pages for every completed (yesterday-or-older) board.

Idempotent: rebuilds any missing/changed pages plus the archive index and
sitemap.xml. Never emits a page for today or the future — boards are only
revealed once the day is over.
"""
import os, sys, html, datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from common import (sb_get, derive_board, hn_to_date, display_game_number,
                    load_dictionary, top_findable_words, TATER_RULE_HN)

ET = ZoneInfo("America/New_York")
TODAY_HN = int(datetime.datetime.now(ET).strftime("%Y%m%d"))

rows = sb_get("leaderboard_public?select=hand_number,name,combined_score"
              "&order=hand_number.asc")
by_hand = defaultdict(list)
for r in rows:
    hn = int(r["hand_number"])
    if hn < TODAY_HN:                      # completed days only
        by_hand[hn].append(r)

if not by_hand:
    print("no completed boards; nothing to do"); sys.exit(0)

DICT = load_dictionary()
hands = sorted(by_hand)
os.makedirs("archive", exist_ok=True)

CSS = """
:root{--ink:#131C2E;--gold:#DBB554;--cream:#F6EFDF;--mint:#60BE8C;--muted:#7C8AA5;--felt:#1F5437}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font-family:'Inter',system-ui,sans-serif;line-height:1.6}
.bar{background:var(--ink);padding:14px 16px}.bar a{color:var(--cream);text-decoration:none;font-weight:700;font-size:18px}
.bar a span{color:var(--gold)}.wrap{max-width:650px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:24px;margin:18px 0 2px}.sub{color:var(--muted);font-size:14px;margin-bottom:20px}
.panel{background:var(--ink);color:var(--cream);border-radius:14px;padding:18px;margin:16px 0}
.panel h2{font-size:15px;color:var(--gold);letter-spacing:1px;margin:0 0 12px;text-transform:uppercase}
.tiles{display:flex;gap:8px;flex-wrap:wrap}.tile{width:44px;height:44px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:22px;color:var(--ink)}
.tc{background:#E88C46}.tv{background:var(--cream);border:2px dashed var(--muted)}
.slotrow{margin-top:10px;font-size:14px}.slotrow b{color:var(--gold)}
table{width:100%;border-collapse:collapse;font-size:15px}td,th{padding:7px 4px;text-align:left;border-bottom:1px solid rgba(124,138,165,.25)}
th{color:var(--gold);font-size:12px;letter-spacing:1px;text-transform:uppercase}.pts{text-align:right;color:var(--gold);font-weight:700;font-family:monospace}
.champ{background:linear-gradient(90deg,rgba(219,181,84,.14),rgba(219,181,84,.04));border:1px solid var(--gold);border-radius:12px;padding:12px 16px;margin:16px 0;font-weight:700}
.words{display:flex;flex-wrap:wrap;gap:8px}.w{background:var(--felt);color:var(--cream);border-radius:8px;padding:5px 10px;font-size:14px}.w b{color:var(--gold)}
.nav{display:flex;justify-content:space-between;margin:26px 0 0;font-weight:700}.nav a{color:#B8862A;text-decoration:none}
.cta{display:block;text-align:center;background:var(--gold);color:var(--ink);font-weight:800;border-radius:999px;padding:13px;margin:26px 0 0;text-decoration:none;font-size:17px}
"""

def page(hn, prev_hn, next_hn):
    d = hn_to_date(hn); disp = display_game_number(hn)
    day = d.strftime("%A, %B %-d, %Y")
    board = derive_board(hn)
    entries = sorted(by_hand[hn], key=lambda r: -r["combined_score"])
    champ = entries[0]
    top, total = top_findable_words(board, DICT)
    era = "Tater Rule pricing" if hn >= TATER_RULE_HN else "launch pricing (+$0.75 on the 2nd vowel bought)"

    tiles = "".join(f'<div class="tile tc">{c}</div>' for c in board["base"])
    tiles += f'<div class="tile tv">{board["auto"]}</div>'
    slots = "".join(
        f'<div class="slotrow">Slot {i+1}: buy <b>{v}</b> for <b>${p:.2f}</b> — or take the free consonant <b>{c}</b></div>'
        for i, ((v, c), p) in enumerate(zip(board["slots"], board["prices"])))
    scoreboard = "".join(
        f'<tr><td>{i+1}</td><td>{html.escape(str(r["name"]))}</td><td class="pts">{round(r["combined_score"])} pts</td></tr>'
        for i, r in enumerate(entries))
    words = "".join(f'<span class="w">{w.upper()} <b>+{p}</b></span>' for w, p in top)
    nav_prev = f'<a href="/archive/{prev_hn}.html">&larr; #{display_game_number(prev_hn)}</a>' if prev_hn else "<span></span>"
    nav_next = f'<a href="/archive/{next_hn}.html">#{display_game_number(next_hn)} &rarr;</a>' if next_hn else '<a href="/">Today\'s board &rarr;</a>'
    champ_name = html.escape(str(champ["name"]))
    desc = (f"Voweluable #{disp} ({day}): board letters, vowel prices, best words and answers, "
            f"and the daily champion — {champ_name} with {round(champ['combined_score'])} points.")

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Voweluable #{disp} — {day} board, answers &amp; champion</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="https://voweluable.com/archive/{hn}.html">
<link rel="icon" type="image/png" href="/favicon-32.png" sizes="32x32">
<style>{CSS}</style></head><body>
<div class="bar"><a href="/">VOWEL<span>UABLE</span> · Board Archive</a></div>
<div class="wrap">
<h1>Voweluable #{disp}</h1><div class="sub">{day} · {era}</div>
<div class="champ">🏆 Daily Champion: {champ_name} — {round(champ["combined_score"])} pts</div>
<div class="panel"><h2>The Board</h2>
<div class="tiles">{tiles}</div>
<div class="slotrow" style="margin-top:14px;color:var(--muted)">3 free consonants + free auto vowel <b>{board["auto"]}</b>, then three choices:</div>
{slots}</div>
<div class="panel"><h2>Final Scoreboard</h2><table><tr><th>#</th><th>Player</th><th class="pts">Score</th></tr>{scoreboard}</table></div>
<div class="panel"><h2>Best Findable Words</h2>
<div class="words">{words}</div>
<div class="slotrow" style="margin-top:12px;color:var(--muted)">{total} words were findable across all builds of this board.</div></div>
<div class="nav">{nav_prev}{nav_next}</div>
<a class="cta" href="/">Play today's board free →</a>
</div></body></html>"""

# --- write day pages -------------------------------------------------------
written = 0
for idx, hn in enumerate(hands):
    prev_hn = hands[idx-1] if idx > 0 else None
    next_hn = hands[idx+1] if idx+1 < len(hands) else None
    html_out = page(hn, prev_hn, next_hn)
    path = f"archive/{hn}.html"
    if not os.path.exists(path) or open(path, encoding="utf-8").read() != html_out:
        open(path, "w", encoding="utf-8").write(html_out); written += 1

# --- archive index ---------------------------------------------------------
items = []
for hn in reversed(hands):
    champ = max(by_hand[hn], key=lambda r: r["combined_score"])
    d = hn_to_date(hn)
    items.append(f'<tr><td><a href="/archive/{hn}.html" style="color:#B8862A;font-weight:700;text-decoration:none">'
                 f'#{display_game_number(hn)}</a></td><td>{d.strftime("%b %-d, %Y")}</td>'
                 f'<td>{html.escape(str(champ["name"]))}</td><td class="pts">{round(champ["combined_score"])}</td></tr>')
index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Voweluable Board Archive — every past board, champion &amp; answers</title>
<meta name="description" content="Every past Voweluable daily board: letters, vowel prices, champions, scores, and the best findable words for each day.">
<link rel="canonical" href="https://voweluable.com/archive/">
<link rel="icon" type="image/png" href="/favicon-32.png" sizes="32x32">
<style>{CSS}</style></head><body>
<div class="bar"><a href="/">VOWEL<span>UABLE</span> · Board Archive</a></div>
<div class="wrap"><h1>Board Archive</h1>
<div class="sub">One page per day: the board, the champion, the scores, and the best words. New boards join the morning after they close.</div>
<div class="panel"><table><tr><th>Game</th><th>Date</th><th>Champion</th><th class="pts">Score</th></tr>{''.join(items)}</table></div>
<a class="cta" href="/">Play today's board free →</a>
</div></body></html>"""
open("archive/index.html", "w", encoding="utf-8").write(index_html)

# --- sitemap ---------------------------------------------------------------
today = datetime.datetime.now(ET).strftime("%Y-%m-%d")
urls = ['<url><loc>https://voweluable.com/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
        '<url><loc>https://voweluable.com/archive/</loc><changefreq>daily</changefreq><priority>0.8</priority></url>',
        '<url><loc>https://voweluable.com/privacy-policy.html</loc><priority>0.2</priority></url>']
urls += [f'<url><loc>https://voweluable.com/archive/{hn}.html</loc><lastmod>{hn_to_date(hn).isoformat()}</lastmod></url>'
         for hn in hands]
open("sitemap.xml", "w").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(urls) + "\n</urlset>\n")

print(f"archive: {written} page(s) written/updated, {len(hands)} total days, index + sitemap rebuilt")
