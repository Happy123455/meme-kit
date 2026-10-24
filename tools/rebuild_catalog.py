"""Scan the kit folders + meta/*.json and write catalog.json (machine) and CATALOG.md (grouped by mood).
Run after adding anything:  python3 tools/rebuild_catalog.py"""
import json, os, subprocess

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(KIT)
M = json.load(open("meta/meanings.json"))
GSM = json.load(open("meta/greenscreen.json")) if os.path.exists("meta/greenscreen.json") else {}
GIFM = json.load(open("meta/gifs.json")) if os.path.exists("meta/gifs.json") else {}
PHM = json.load(open("meta/photos.json")) if os.path.exists("meta/photos.json") else {}
LAY = json.load(open("meta/photo_layouts.json")) if os.path.exists("meta/photo_layouts.json") else {}
RAT = json.load(open("meta/ratings.json")) if os.path.exists("meta/ratings.json") else {}  # from tools/dashboard.py
AUTO = json.load(open("meta/pairs_auto.json")) if os.path.exists("meta/pairs_auto.json") else {}  # tools/find_pairs.py
RANK = {"favorite": 0, "good": 1, None: 2, "meh": 3, "never": 4}
MARK = {"favorite": "❤️ ", "good": "👍 ", "meh": "😐 ", "never": "🚫 ", None: ""}


def dur(f):
    try: return round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout), 2)
    except ValueError: return None


def mean(group, k):
    v = M.get(group, {}).get(k); return (v[0], v[1]) if v else ("misc", "")


items = []
for k, g in sorted(GSM.items()):
    mood, what = mean("greenscreen", k)
    items.append(dict(id=k, type="greenscreen", mood=mood, what=what, video=g["video"], audio=g.get("audio"), alpha=g["alpha"], w=g["w"], h=g["h"],
                      dur=g["dur"], start=g.get("in", 0), usable=round(g["dur"] - g.get("in", 0), 2), original=g.get("original"), source=g.get("title")))
for k, g in sorted(GIFM.items()):
    mood, what = mean("gifs", k)
    items.append(dict(id=k, type="gif", mood=mood, what=what, sheet=f"gifs/{k}.jpg", face=f"gifs/{k}_face.png" if g.get("face") else None, mp4=f"gifs/{k}.mp4" if os.path.exists(f"gifs/{k}.mp4") else None,
                      frames=g["n"], cols=g["cols"], rows=g["rows"], fw=g["fw"], fh=g["fh"], fps=g["fps"], source=g.get("src")))
for sub in ("meme", "basic"):
    for f in sorted(os.listdir(f"sounds/{sub}")):
        if not f.endswith((".mp3", ".wav")): continue
        k = f.rsplit(".", 1)[0]; mood, what = mean("sounds", k)
        items.append(dict(id=k, type="sound", kind=sub, mood=mood if what else ("misc" if sub == "meme" else "sfx"), what=what or k.replace("-", " "), file=f"sounds/{sub}/{f}", dur=dur(f"sounds/{sub}/{f}")))
for k, p in PHM.items():
    mood, what = mean("photos", k)
    items.append(dict(id=k, type="photo", mood=mood, what=what or p.get("name", k), file=p["file"], w=p["w"], h=p["h"], boxes=p.get("boxes"), layout=LAY.get(k)))

CFX = json.load(open("meta/camfx.json")) if os.path.exists("meta/camfx.json") else {}
for k, f in CFX.items():  # camera effects — code in hyperframes/camfx.js, previews in tools/dashboard/camfx.html
    if k.startswith("_"): continue
    items.append(dict(id=k, type="camfx", cat=f["cat"], mood=f["mood"], what=f["what"], d=f["d"], sound=f.get("sound", []), hold=f.get("hold", False), cap=f.get("cap", False)))

for i in items:  # the user's own review (dashboard) — favourites first, "never" = do not use
    r = RAT.get(f"{i['type']}:{i['id']}", {}); i["rating"] = r.get("rating"); i["note"] = r.get("note")
    for f in ("trim", "mute", "pair", "screen"): i[f] = r.get(f)   # the user's edits — memekit.py applies them
    if i["type"] == "greenscreen": i["same_audio"] = AUTO.get(f"greenscreen:{i['id']}", [])
items.sort(key=lambda i: (["greenscreen", "gif", "sound", "photo", "camfx"].index(i["type"]), RANK[i["rating"]], i["id"]))
json.dump(dict(version=1, root="paths are relative to the meme-kit folder", count=len(items),
               ratings="favorite > good > unrated > meh; never = do not use", items=items), open("catalog.json", "w"), indent=1)

# CATALOG.md: by type, then by mood, with meaning — the file a session reads to pick memes
L = ["# Meme catalog", "", f"{len(items)} items. Paths are relative to this folder. Machine-readable version: `catalog.json`.", "",
     "Moods: " + ", ".join(f"`{m}`" for m in M["_moods"]), "",
     "**User ratings** (from the review dashboard): ❤️ favourite — prefer these · 👍 good · 😐 meh — only if nothing else fits · "
     "🚫 never — listed at the end, DO NOT USE. Unmarked = not reviewed yet.",
     "**User edits** (dashboard): ✂️ trim, 🔇 muted clip audio, 🔗 paired sound, ⛶/▣ full-screen rule — `memekit.py` applies them automatically. "
     "A USER NOTE belongs to that one meme only: read it before using the meme and do what it says.", ""]
for t, title in [("greenscreen", "Green-screen clips with sound (transparent WebM + MP3)"), ("gif", "Reaction GIF clips (sprite sheets; ✓face = round face crop)"),
                 ("sound", "Sounds"), ("photo", "Photo memes (captioned or with panel labels)"),
                 ("camfx", "Camera effects (hyperframes/camfx.js · `kit.camfx(id, start, target=…, x=, y=)` · moves the shot itself)")]:
    sel = [i for i in items if i["type"] == t and i["rating"] != "never"]; L += [f"## {title} — {len(sel)}", ""]
    by = {}
    for i in sel: by.setdefault(i["mood"], []).append(i)
    for mood in sorted(by):
        L.append(f"**{mood}**"); L.append("")
        for i in by[mood]:
            extra = ""
            if t == "greenscreen": extra = f" · {i['usable']}s{' · transparent' if i['alpha'] else ' · card'}{f' · starts {i[chr(115)+chr(116)+chr(97)+chr(114)+chr(116)]}s' if i['start'] else ''}"
            if t == "gif": extra = f" · {i['frames']} frames{' · ✓face' if i['face'] else ''}"
            if t == "sound": extra = f" · {i['dur']}s · {i['kind']}"
            if t == "photo" and i.get("layout"): extra = f" · {len(i['layout'])} label slots"
            if t == "camfx": extra = f" · {i['cat']} · {i['d']}s" + (" · caption" if i["cap"] else "") + (" · holds" if i["hold"] else "") + (f" · 🔊 {', '.join(x[0] for x in i['sound'])}" if i["sound"] else "")
            ed = []
            if i.get("trim"): ed.append(f"✂️ uses {i['trim'][0]}–{i['trim'][1]} s only")
            if i.get("mute"): ed.append("🔇 clip audio muted")
            if i.get("pair"): ed.append(f"🔗 with sound `{i['pair']['sound']}` at {i['pair'].get('at', 0)} s" + (f" ({i['pair']['note']})" if i['pair'].get('note') else ""))
            if i.get("screen"): ed.append("⛶ ALWAYS full screen" if i["screen"] == "full" else "▣ NEVER full screen")
            L.append(f"- {MARK[i['rating']]}`{i['id']}`{extra} — {i['what']}" + (f" · **{' · '.join(ed)}**" if ed else "")
                     + (f" _(USER NOTE — read and follow: {i['note']})_" if i.get("note") else ""))
        L.append("")
bad = [i for i in items if i["rating"] == "never"]
if bad:
    L += [f"## 🚫 Do not use — {len(bad)}", "", "The user reviewed these and does not want them in videos.", ""]
    L += [f"- `{i['type']}:{i['id']}`" + (f" — {i['note']}" if i.get("note") else "") for i in bad]
open("CATALOG.md", "w").write("\n".join(L) + "\n")
print("catalog:", len(items), "items")
