"""Grow the meme kit. Needs: ffmpeg/ffprobe, curl, python with pillow + numpy; yt-dlp for green-screen clips.
  python3 tools/grow.py sound "vine boom" "emotional damage"          # MyInstants → sounds/meme/
  python3 tools/grow.py greenscreen "the rock eyebrow" "coffin dance"  # YouTube (yt-dlp) → keyed WebM + MP3 in greenscreen/
  python3 tools/grow.py gif "surprised pikachu" --face 0.5,0.55,0.95   # Giphy → gifs/ sprite sheet (+ round face crop)
  python3 tools/grow.py drop greenscreen bad_id                        # remove an item
Each command rebuilds catalog.json + CATALOG.md. Then ADD A MEANING for new ids in meta/meanings.json (mood + when to use)
and rerun tools/rebuild_catalog.py — the meaning is what lets a session pick the right meme.
Downloads land in _downloads/ (untrusted: never run code from there). Personal / educational use only."""
import json, os, re, shutil, subprocess, sys, tempfile, urllib.parse

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(KIT)
DL = "_downloads"; os.makedirs(DL, exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
YTDLP = shutil.which("yt-dlp") or os.environ.get("YTDLP", "yt-dlp")
slug = lambda q, sep="-": re.sub(r"[^a-z0-9]+", sep, q.lower()).strip(sep)
curl = lambda *a: subprocess.run(["curl", "-sL", "-m", "40", "-A", UA, *a], capture_output=True, text=True, errors="ignore").stdout
load = lambda p: json.load(open(p)) if os.path.exists(p) else {}


def sound(qs):
    for q in qs:
        h = curl("https://www.myinstants.com/en/search/?name=" + urllib.parse.quote(q))
        m = re.search(r"/media/sounds/[^'\" ]+\.mp3", h)
        if not m: print("no result:", q); continue
        raw = f"{DL}/{slug(q)}.mp3"; subprocess.run(["curl", "-sL", "-m", "40", "-A", UA, "-o", raw, "https://www.myinstants.com" + m.group(0)])
        out = f"sounds/meme/{slug(q)}.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-t", "8", "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "44100", "-c:a", "libmp3lame", "-q:a", "3", out])
        print("sound:", slug(q))


def _corner(f, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f, "-frames:v", "1", "-vf", "scale=64:64", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(raw) < 64 * 64 * 3: return None
    px = []
    for (x0, y0) in [(0, 0), (56, 0), (0, 56), (56, 56)]:
        for y in range(y0, y0 + 8):
            for x in range(x0, x0 + 8): i = (y * 64 + x) * 3; px.append(tuple(raw[i:i + 3]))
    px.sort(key=lambda p: p[1]); return px[len(px) // 2]


def greenscreen(qs):
    import numpy as np
    meta = load("meta/greenscreen.json")
    for q in qs:
        name = slug(q, "_")
        lst = subprocess.run([YTDLP, "--flat-playlist", "--print", "%(id)s|%(duration)s|%(title)s", f"ytsearch8:{q} green screen meme"], capture_output=True, text=True).stdout
        pick = None
        for ln in lst.strip().splitlines():
            vid, dur, title = (ln.split("|", 2) + ["", ""])[:3]
            try: d = float(dur)
            except ValueError: continue
            if 2 <= d <= 25: pick = (vid, title); break
        if not pick: print("no short clip found:", q); continue
        raw = f"{DL}/{name}.mp4"
        subprocess.run([YTDLP, "-q", "--no-playlist", "-f", "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/b", "--merge-output-format", "mp4", "-o", raw, f"https://www.youtube.com/watch?v={pick[0]}"])
        if not os.path.exists(raw): print("download failed:", q); continue
        j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", raw], capture_output=True, text=True).stdout)
        v = next(s for s in j["streams"] if s["codec_type"] == "video"); d = float(j["format"]["duration"]); has_a = any(s["codec_type"] == "audio" for s in j["streams"])
        col = _corner(raw, min(1.0, d / 2)); green = col is not None and col[1] > 120 and col[1] > col[0] + 45 and col[1] > col[2] + 45
        sc = "scale=-2:'min(720,ih)'"
        if green:
            out = f"greenscreen/{name}.webm"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-an", "-vf", f"{sc},chromakey=0x%02x%02x%02x:0.16:0.07,despill=type=green,format=yuva420p" % col,
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "2.5M", "-auto-alt-ref", "0", "-row-mt", "1", out], check=True)
            fr = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", out, "-vf", "fps=4,scale=64:36", "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout, np.uint8).reshape(-1, 36, 64, 4)
            hit = np.nonzero((fr[..., 3] > 128).mean(axis=(1, 2)) > 0.03)[0]; start = round(float(hit[0]) / 4, 2) if len(hit) else 0.0
        else:
            out = f"greenscreen/{name}.mp4"; start = 0.0
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-an", "-vf", sc, "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", out], check=True)
        aud = None
        if has_a:
            aud = f"greenscreen/{name}.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vn", "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "44100", "-c:a", "libmp3lame", "-q:a", "3", aud], check=True)
        os.makedirs("greenscreen/original", exist_ok=True); shutil.copy2(raw, f"greenscreen/original/{name}.mp4")
        meta[name] = dict(video=out, audio=aud, original=f"greenscreen/original/{name}.mp4", alpha=green, w=int(v["width"]), h=int(v["height"]), dur=round(d, 2), **{"in": start}, title=pick[1], youtube=pick[0])
        json.dump(meta, open("meta/greenscreen.json", "w"), indent=1)
        print(("keyed " if green else "plain ") + name, "— CHECK IT over a coloured background before trusting it")


def gif(qs, face=None):
    from PIL import Image, ImageDraw
    meta = load("meta/gifs.json")
    for q in qs:
        name = slug(q, "_")
        h = curl("https://giphy.com/search/" + urllib.parse.quote(q.replace(" ", "-")))
        m = re.search(r'\\?"id\\?":\\?"([A-Za-z0-9]{10,24})\\?".{0,400}?\\?"title\\?":\\?"([^"\\]{2,90})', h)
        if not m: print("no gif:", q); continue
        gid, title = m.group(1), m.group(2); src = f"gifs/{name}.mp4"
        subprocess.run(["curl", "-sL", "-m", "60", "-A", UA, "-o", src, f"https://media.giphy.com/media/{gid}/giphy.mp4"])
        tmp = tempfile.mkdtemp()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "3", "-i", src, "-vf", "fps=12,scale=300:-2", f"{tmp}/f%03d.png"], check=True)
        ims = [Image.open(os.path.join(tmp, f)).convert("RGB") for f in sorted(os.listdir(tmp))]
        fw, fh = ims[0].size; n = len(ims); cols = 6; rows = (n + cols - 1) // cols
        sheet = Image.new("RGB", (cols * fw, rows * fh))
        for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * fw, (i // cols) * fh))
        sheet.save(f"gifs/{name}.jpg", quality=82)
        rec = dict(n=n, cols=cols, rows=rows, fw=fw, fh=fh, fps=12, src=title, gid=gid)
        if face:
            cx, cy, sz = face; S = int(min(fw, fh) * sz); F = 160
            mask = Image.new("L", (F, F), 0); ImageDraw.Draw(mask).ellipse((2, 2, F - 3, F - 3), fill=255)
            fs = Image.new("RGBA", (cols * F, rows * F), (0, 0, 0, 0))
            for i, im in enumerate(ims):
                x0, y0 = int(cx * fw - S / 2), int(cy * fh - S / 2)
                c = im.crop((x0, y0, x0 + S, y0 + S)).resize((F, F)).convert("RGBA"); c.putalpha(mask)
                ring = Image.new("RGBA", (F, F), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse((1, 1, F - 2, F - 2), outline=(29, 32, 48, 255), width=7)
                c.alpha_composite(ring); fs.paste(c, ((i % cols) * F, (i // cols) * F))
            fs.save(f"gifs/{name}_face.png"); rec["face"] = dict(fw=F, fh=F)
        meta[name] = rec; json.dump(meta, open("meta/gifs.json", "w"), indent=1)
        print("gif:", name, "-", title)


def drop(kind, ids):
    mp = {"greenscreen": "meta/greenscreen.json", "gif": "meta/gifs.json", "photo": "meta/photos.json"}
    if kind == "sound":
        for i in ids:
            for sub in ("meme", "basic"):
                if os.path.exists(f"sounds/{sub}/{i}.mp3"): os.remove(f"sounds/{sub}/{i}.mp3")
        return
    meta = load(mp[kind])
    for i in ids:
        r = meta.pop(i, None)
        for k in ("video", "audio", "original", "file"):
            if r and r.get(k) and os.path.exists(r[k]): os.remove(r[k])
        for f in (f"gifs/{i}.jpg", f"gifs/{i}_face.png", f"gifs/{i}.mp4"):
            if kind == "gif" and os.path.exists(f): os.remove(f)
    json.dump(meta, open(mp[kind], "w"), indent=1)


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "sound": sound(args)
    elif cmd == "greenscreen": greenscreen(args)
    elif cmd == "gif":
        face = None
        if "--face" in args: i = args.index("--face"); face = tuple(float(x) for x in args[i + 1].split(",")); args = args[:i] + args[i + 2:]
        gif(args, face)
    elif cmd == "drop": drop(args[0], args[1:])
    if cmd in ("sound", "greenscreen"): subprocess.run([sys.executable, os.path.join(KIT, "tools", "level_audio.py")])
    subprocess.run([sys.executable, os.path.join(KIT, "tools", "rebuild_catalog.py")])
