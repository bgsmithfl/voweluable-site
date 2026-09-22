#!/usr/bin/env python3
"""Yesterday's champion card + Facebook post text -> output/latest/.
Storyline-aware: record / giant-slayer / N-straight / standard."""
import os, sys, math, datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from common import sb_get, display_game_number

ET = ZoneInfo("America/New_York")
yday = datetime.datetime.now(ET).date() - datetime.timedelta(days=1)
HN = int(yday.strftime("%Y%m%d"))

rows = sb_get("leaderboard_public?select=hand_number,name,combined_score&order=hand_number.asc")
by_hand = defaultdict(list)
for r in rows: by_hand[int(r["hand_number"])].append(r)
if HN not in by_hand:
    print(f"nobody played hand {HN}; nothing to post"); sys.exit(0)

def winner(hn): return max(by_hand[hn], key=lambda r: r["combined_score"])
hands = sorted(h for h in by_hand if h <= HN)
champ = winner(HN); name, score = str(champ["name"]), round(champ["combined_score"])
crowns = sum(1 for h in hands if winner(h)["name"] == name)
run = 0
for h in reversed(hands):
    if winner(h)["name"] == name: run += 1
    else: break
prev = [h for h in hands if h < HN]
prev_best = max((round(winner(h)["combined_score"]) for h in prev), default=0)
is_record = score > prev_best
dethroned, their_run = None, 0
if prev and winner(prev[-1])["name"] != name:
    dn = winner(prev[-1])["name"]
    for h in reversed(prev):
        if winner(h)["name"] == dn: their_run += 1
        else: break
    if their_run >= 2: dethroned = str(dn)

PE = {2:"BACK-TO-BACK",3:"THREE-PEAT",4:"FOUR STRAIGHT",5:"FIVE STRAIGHT",6:"SIX STRAIGHT",7:"SEVEN STRAIGHT",8:"EIGHT STRAIGHT",9:"NINE STRAIGHT",10:"TEN STRAIGHT"}
kind = "record" if is_record else "slayer" if dethroned else "peat" if run >= 2 else "plain"
sub = {"record":"NEW ALL-TIME RECORD","slayer":"GIANT SLAYER","peat":PE.get(run,f"{run} STRAIGHT"),"plain":"DAILY CHAMPION"}[kind]

BG=(19,28,46); GOLD=(219,181,84); CREAM=(246,239,223); MINT=(96,190,140)
BILL=(31,84,55); BE=(46,110,74); INK=(12,19,30); RED=(214,106,72)
W=H=1080
img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
FB="fonts/DejaVuSans-Bold.ttf"; FM="fonts/DejaVuSansMono-Bold.ttf"
font=lambda s: ImageFont.truetype(FB,s); mono=lambda s: ImageFont.truetype(FM,s)
bx=200
d.rounded_rectangle([bx,70,bx+96,166],22,fill=GOLD)
d.text((bx+48,118),"$",font=font(58),fill=INK,anchor="mm")
wx=bx+120
d.text((wx,96),"VOWEL",font=font(64),fill=CREAM,anchor="lm")
w1=d.textlength("VOWEL",font=font(64))
d.text((wx+w1,96),"UABLE",font=font(64),fill=GOLD,anchor="lm")
d.text((wx,150),"A NEW FREE DAILY WORD GAME, EVERY MIDNIGHT",font=font(21),fill=MINT,anchor="lm")
cx,cy=W//2,315
if kind=="record":
    for k in range(24):
        a=math.radians(k*15); ln=110 if k%2==0 else 72
        d.line([cx+int(52*math.cos(a)),cy+int(52*math.sin(a)),cx+int((52+ln)*math.cos(a)),cy+int((52+ln)*math.sin(a))],fill=(60,74,105),width=5)
    d.text((cx,cy),str(score),font=font(46),fill=GOLD,anchor="mm")
    d.text((W/2,462),"THE RECORD FALLS",font=font(46),fill=RED,anchor="mm")
elif kind=="slayer":
    pts=[(-70,40),(-70,-8),(-35,17),(0,-30),(35,17),(70,-8),(70,40),(70,60),(-70,60)]
    a=math.radians(38)
    rot=[(cx+int(x*math.cos(a)-y*math.sin(a)),cy+int(x*math.sin(a)+y*math.cos(a))) for x,y in pts]
    d.polygon(rot,fill=(150,124,60))
    d.text((W/2,462),"THE REIGN IS OVER",font=font(46),fill=RED,anchor="mm")
else:
    d.polygon([(cx-90,cy+50),(cx-90,cy-10),(cx-45,cy+22),(cx,cy-38),(cx+45,cy+22),(cx+90,cy-10),(cx+90,cy+50)],fill=GOLD)
    d.rectangle([cx-90,cy+58,cx+90,cy+74],fill=GOLD)
    d.text((W/2,462),"DAILY CHAMPION",font=font(46),fill=GOLD,anchor="mm")
px0,px1=110,W-110; py0,py1=520,820
d.rounded_rectangle([px0,py0,px1,py1],24,fill=BILL,outline=GOLD if kind=="record" else BE,width=6 if kind=="record" else 5)
d.text((px0+34,py0+34),"$",font=font(40),fill=GOLD)
d.text((px1-34,py1-70),"$",font=font(40),fill=GOLD)
d.text((px1-34,py0+40),f"VB {display_game_number(HN)}",font=mono(24),fill=(150,200,170),anchor="rm")
d.text((W/2,py0+66),sub,font=font(26),fill=MINT,anchor="mm")
sz=92
while d.textlength(name,font=font(sz))>(px1-px0-120) and sz>40: sz-=4
d.text((W/2,py0+145),name,font=font(sz),fill=CREAM,anchor="mm")
d.text((W/2,py0+230),f"{score} pts",font=font(62),fill=GOLD,anchor="mm")
tag=[yday.strftime("%A").upper(), f"CROWN #{crowns}"]
if kind=="record": tag.append(f"OLD RECORD {prev_best}")
d.text((px0+34,py1-52)," · ".join(tag),font=mono(20),fill=(150,200,170))
foot={"record":"The bar has moved. Chase it.","slayer":"The throne is open again."}.get(kind,"A new game is live right now.")
d.text((W/2,900),foot,font=font(34),fill=CREAM,anchor="mm")
d.text((W/2,965),"Take the crown at voweluable.com",font=font(38),fill=MINT,anchor="mm")
os.makedirs("output/latest",exist_ok=True); os.makedirs(f"output/{HN}",exist_ok=True)
for p in (f"output/{HN}/champion.png","output/latest/champion.png"): img.save(p)

disp=display_game_number(HN); L=[]
if kind=="record":
    L.append(f"🚨 RECORD ALERT. {name} — {score:,} points. The all-time record falls (old mark: {prev_best:,}).")
    L.append("⚠️ COMMISSIONER: run the word-by-word audit BEFORE posting this one. The tape gets reviewed, every time.")
elif kind=="slayer":
    L.append(f"⚔️ THE REIGN IS OVER. {name} — {score} pts — ends {dethroned}'s {their_run}-day run.")
elif kind=="peat":
    L.append(f"👑 Voweluable #{disp} Champion: {name} — {score} pts. {sub.title()} — crown #{crowns}.")
else:
    L.append(f"👑 Voweluable #{disp} Champion: {name} — {score} pts. Crown #{crowns}.")
L.append(f"📖 Yesterday's full board, scores & best words: https://voweluable.com/archive/{HN}.html")
L.append("⚔️ Today's board is live. Play it, then hit Challenge a friend — they get your exact board, no account needed.")
L.append("One official shot per day: voweluable.com")
L.append("🎮 New here? Free practice round — Vowel Bucks are play money, nothing to buy, ever.")
post="\n\n".join(L)
for p in (f"output/{HN}/post.txt","output/latest/post.txt"): open(p,"w").write(post+"\n")
print(f"card: {name} {score} kind={kind} crowns={crowns} run={run}")
