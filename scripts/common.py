"""Shared game logic: board derivation, pricing eras, scoring, Supabase access."""
import os, json, datetime, urllib.request, urllib.parse

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

HARD = ['F','H','V','W','Y','K','J','X','Q','Z']
EASY = ['L','N','S','T','R','D','G','B','C','M','P']
VOWELS = ['A','E','I','O','U']
PTS = {3:10, 4:25, 5:50, 6:90, 7:150}

# Pricing eras. The Tater Rule (flat, study-calibrated prices; no 2nd-vowel
# premium) took effect with hand 20260915. Earlier boards used launch pricing
# plus a $0.75 premium on the second purchased vowel.
TATER_RULE_HN = 20260915
OLD_COSTS = {'A':2.75,'E':3.50,'I':1.75,'O':2.75,'U':2.00}
NEW_COSTS = {'A':4.75,'E':5.75,'I':2.00,'O':2.50,'U':1.50}

def slot_prices(hn, vowel_order):
    """Price for each purchasable slot (index 0-2), era-aware."""
    if hn >= TATER_RULE_HN:
        return [NEW_COSTS[v] for v in vowel_order]
    return [OLD_COSTS[v] + (0.75 if i == 1 else 0) for i, v in enumerate(vowel_order)]

def mulberry32(seed):
    state = seed & 0xFFFFFFFF
    def rng():
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return rng

def shuffled(arr, rng):
    a = list(arr)
    for i in range(len(a)-1, 0, -1):
        j = int(rng() * (i+1))
        a[i], a[j] = a[j], a[i]
    return a

def derive_board(hn):
    """Replicates generateRound() for an official hand."""
    rng = mulberry32(hn)
    hard = shuffled(HARD, rng)[0]
    easy = shuffled(EASY, rng)[:5]
    base = shuffled([hard] + easy[:2], rng)
    fallback = easy[2:5]
    v = shuffled(VOWELS, rng)
    return {
        "base": base, "auto": v[0],
        "slots": list(zip(v[1:4], fallback)),
        "prices": slot_prices(hn, v[1:4]),
    }

def hn_to_date(hn):
    return datetime.date(hn//10000, hn//100 % 100, hn % 100)

def display_game_number(hn):
    d = hn_to_date(hn)
    return f"{d.year % 100}{d.timetuple().tm_yday}"

def sb_get(path):
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def load_dictionary(index_html="index.html"):
    """Pulls the embedded word list straight from the live game file."""
    src = open(index_html, encoding="utf-8").read()
    i = src.find('WORD_LIST_RAW = "') + len('WORD_LIST_RAW = "')
    j = src.find('"', i)
    words = src[i:j].split("\\n")
    return [w for w in words if 3 <= len(w) <= 7 and w.isalpha() and len(set(w)) == len(w)]

def top_findable_words(board, dictionary, limit=12):
    """Best-scoring words playable on at least one legal 7-tile build."""
    combos = []
    for pick in range(8):
        tiles = [c.lower() for c in board["base"]] + [board["auto"].lower()]
        for k, (v, cons) in enumerate(board["slots"]):
            tiles.append((v if pick >> k & 1 else cons).lower())
        combos.append(frozenset(tiles))
    seen = {}
    for w in dictionary:
        ws = set(w)
        if any(ws <= c for c in combos):
            seen[w] = PTS[len(w)]
    ranked = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:limit], len(seen)
