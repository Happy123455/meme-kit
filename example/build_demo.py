"""Smallest working example: a 12-second HyperFrames composition made only from MemeKit pieces.
  python3 example/build_demo.py && cd example && npx hyperframes check && npx hyperframes render -o demo.mp4"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "hyperframes"))
import memekit as mk

# the kit must be reachable from the project as assets/memekit (symlink or copy)
os.makedirs(f"{HERE}/assets", exist_ok=True)
if not os.path.exists(f"{HERE}/assets/memekit"): os.symlink("../..", f"{HERE}/assets/memekit")

kit = mk.Kit(url_root="assets/memekit")
parts, anims = [], []
for h, a in [
    kit.photo("drake-hotline-bling", start=0.3, dur=3.6, pos="left", labels=["Studying the night before", "Watching meme videos instead"]),
    kit.sound("vine-boom", start=0.4),
    kit.gif("pikachu", start=4.2, dur=3.0, pos="right", cap="Me seeing the exam paper:"),
    kit.sound("gasp", start=4.2),
    kit.greenscreen("the_rock_eyebrow_raise", start=7.4, pos="center"),
]:
    parts.append(h); anims.append(a)

doc = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920, height=1080">
<link rel="stylesheet" href="assets/memekit/hyperframes/memekit.css">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#f4efe6}} #root{{position:relative;width:1920px;height:1080px}}</style>
</head><body>
<div id="root" data-composition-id="demo" data-start="0" data-duration="12" data-width="1920" data-height="1080">
{chr(10).join(parts)}
</div>
<script>window.MEMEKIT = {json.dumps([a for a in anims if a])};</script>
<script src="assets/memekit/hyperframes/memekit.js"></script>
<script>
const tl = gsap.timeline({{ paused: true }});
MemeKit.animate(tl);
window.__timelines = window.__timelines || {{}};
window.__timelines["demo"] = tl;
</script>
</body></html>
"""
open(f"{HERE}/index.html", "w").write(doc)
for f in ("hyperframes.json", "meta.json"):
    if not os.path.exists(f"{HERE}/{f}"): json.dump({"id": "memekit-demo", "name": "MemeKit demo"} if f == "meta.json" else {"paths": {"assets": "assets"}}, open(f"{HERE}/{f}", "w"))
print("wrote example/index.html")
