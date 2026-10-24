"""Contact sheet of green-screen clips over pink (5 moments each) — look at it before trusting new clips.
  python3 tools/check_greenscreen.py [id ...]   (no ids = all)   → _downloads/check_greenscreen.jpg
Needs pillow. Bad clips: python3 tools/grow.py drop greenscreen <id>"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(KIT)
meta = json.load(open("meta/greenscreen.json")); ids = sys.argv[1:] or sorted(meta)
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 14)
except OSError: font = ImageFont.load_default()
TW, TH = 240, 135; sheet = Image.new("RGB", (5 * (TW + 2) + 220, len(ids) * (TH + 2)), "black"); d = ImageDraw.Draw(sheet)
tmp = tempfile.mkdtemp()
for r, k in enumerate(ids):
    v = meta[k]; y = r * (TH + 2)
    d.text((6, y + 6), f"{k}\n{'transparent' if v['alpha'] else 'plain'} · {v['dur']}s\nstarts {v.get('in', 0)}s", fill="white", font=font)
    for c, f in enumerate([0.1, 0.3, 0.5, 0.7, 0.9]):
        out = f"{tmp}/x.png"; dec = ["-c:v", "libvpx-vp9"] if v["video"].endswith(".webm") else []
        subprocess.run(["ffmpeg", "-v", "error", "-y", *dec, "-ss", str(v["dur"] * f), "-i", v["video"], "-frames:v", "1", "-vf", f"scale={TW}:{TH}:force_original_aspect_ratio=decrease", "-pix_fmt", "rgba", out])
        bg = Image.new("RGBA", (TW, TH), (255, 60, 200, 255))
        if os.path.exists(out): im = Image.open(out).convert("RGBA"); bg.alpha_composite(im, ((TW - im.width) // 2, (TH - im.height) // 2)); os.remove(out)
        sheet.paste(bg.convert("RGB"), (220 + c * (TW + 2), y))
os.makedirs("_downloads", exist_ok=True); sheet.save("_downloads/check_greenscreen.jpg", quality=80); print("→ _downloads/check_greenscreen.jpg")
