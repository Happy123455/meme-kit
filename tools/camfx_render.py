"""Put meme camera effects on ANY video (talking head, lecture, gameplay…) and render it with HyperFrames.

  python3 tools/camfx_render.py talk.mp4 -o talk_fx.mp4 --fx zoom_punch@3.2 --fx "earthquake@7.5:k=1.4" --fx "freeze_gray@12:cap=Yup, that's me."
  python3 tools/camfx_render.py talk.mp4 --focus 46,38 --fx dark_zoom@4 --snap 4.5,6     # just check frames (PNG), no render

--fx  id@seconds[:key=value,...]   keys: d (length), k (intensity), x, y (focus %), cap (caption), sound (0 = no meme sound), vol
--focus x,y   default focus point (the face) in % of the frame for every effect (default 50,42)
Effect ids and meanings: CATALOG.md → "Camera effects", or the Camera FX dashboard. Project kept in _work/<name>/ for tweaking."""
import argparse, json, os, subprocess, sys
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "hyperframes")); import memekit as mk
HF = ["npx", "--yes", "hyperframes@0.8.185"]


def probe(f):
    o = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json", f],
                                  capture_output=True, text=True, check=True).stdout)
    v = next(s for s in o["streams"] if s["codec_type"] == "video")
    return v["width"], v["height"], float(o["format"]["duration"]), any(s["codec_type"] == "audio" for s in o["streams"])


def parse_fx(s, focus):
    head, _, opts = s.partition(":")
    fid, _, t = head.partition("@")
    o = dict(x=focus[0], y=focus[1])
    for kv in filter(None, opts.split(",") if "cap=" not in opts else _split_cap(opts)):
        k, _, v = kv.partition("="); k = k.strip()
        o[k] = v if k == "cap" else float(v)
    return fid.strip(), float(t), o


def _split_cap(opts):  # cap text may contain commas: everything after cap= is the caption
    pre, _, cap = opts.partition("cap=")
    return [x for x in pre.split(",") if x] + ["cap=" + cap]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("-o", "--out"); ap.add_argument("--fx", action="append", default=[])
    ap.add_argument("--focus", default="50,42"); ap.add_argument("--snap"); ap.add_argument("--name")
    a = ap.parse_args()
    src = os.path.abspath(a.input); name = a.name or os.path.splitext(os.path.basename(src))[0]
    W, H, D, has_audio = probe(src)
    if H != 1080: W, H = round(W * 1080 / H / 2) * 2, 1080
    focus = [float(v) for v in a.focus.split(",")]
    P = os.path.join(KIT, "_work", name); os.makedirs(f"{P}/assets", exist_ok=True)
    for link, to in ((f"{P}/assets/memekit", KIT), (f"{P}/assets/input{os.path.splitext(src)[1]}", src)):
        if os.path.islink(link): os.remove(link)
        os.symlink(to, link)
    media = f"assets/input{os.path.splitext(src)[1]}"
    kit = mk.Kit(url_root="assets/memekit"); parts = []
    for s in a.fx:
        fid, t, o = parse_fx(s, focus)
        parts.append(kit.camfx(fid, t, target="#stage", dur=o.get("d"), x=o["x"], y=o["y"], k=o.get("k", 1.0), cap=o.get("cap"),
                               sound=o.get("sound", 1) != 0, vol=o.get("vol")))
    audio = f'<audio id="srcaudio" class="clip" src="{media}" data-start="0" data-duration="{D:.3f}" data-track-index="2"></audio>' if has_audio else ""
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width={W}, height={H}">
<script src="assets/memekit/hyperframes/vendor/gsap.min.js"></script>
<link rel="stylesheet" href="assets/memekit/hyperframes/memekit.css">
<style>html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}} #root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#000}}
#stage{{position:absolute;inset:0}} #stage video{{width:100%;height:100%;object-fit:cover;display:block}}</style>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{D:.3f}" data-width="{W}" data-height="{H}">
  <div id="stage"><video id="srcvideo" class="clip" src="{media}" muted playsinline data-start="0" data-duration="{D:.3f}" data-track-index="1"></video></div>
  {audio}
{chr(10).join(h for h, _ in parts)}
</div>
<script src="assets/memekit/hyperframes/camfx.js"></script>
<script>window.MEMEKIT = {json.dumps([x for _, x in parts if x])};</script>
<script src="assets/memekit/hyperframes/memekit.js"></script>
<script>
const tl = gsap.timeline({{ paused: true }});
tl.to({{}}, {{ duration: {D:.3f} }}, 0);
MemeKit.animate(tl);
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
</script>
</body></html>
"""
    open(f"{P}/index.html", "w").write(doc)
    json.dump({"paths": {"assets": "assets"}}, open(f"{P}/hyperframes.json", "w"))
    json.dump({"id": f"camfx-{name}", "name": f"CamFX {name}"}, open(f"{P}/meta.json", "w"))
    if a.snap:
        out = os.path.abspath(a.out or f"{P}/snaps")
        subprocess.run(HF + ["snapshot", P, f"--at={a.snap}", "--no-end", "-o", out, "--describe", "false", "--timeout", "20000"], check=True)
        print("frames in", out); return
    out = os.path.abspath(a.out or os.path.splitext(src)[0] + "_camfx.mp4")
    subprocess.run(HF + ["render", "-o", out], cwd=P, check=True)
    print("rendered", out)


if __name__ == "__main__":
    main()
