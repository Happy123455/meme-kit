"""Level every meme sound to one steady loudness so no meme jumps out over the narration.
  python3 tools/level_audio.py            → leveled/<same path>.mp3 for greenscreen/*.mp3 and sounds/**/*  (skips up-to-date files)
  python3 tools/level_audio.py --force    → redo all
A gentle compressor first (music inside a clip can't swell), then one gain to LEVEL LUFS and a -2 dB limiter.
memekit.py plays these files automatically and sets one kit-wide volume from your voice-over (Kit(voice=...)),
so meme sound sits ~3 dB under the voice: clearly audible, never on top of it."""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(KIT)
LEVEL = -18.0
COMP = "acompressor=threshold=-26dB:ratio=3:attack=8:release=200"


def sources():
    for f in sorted(os.listdir("greenscreen")):
        if f.endswith(".mp3"): yield f"greenscreen/{f}"
    for sub in ("meme", "basic"):
        for f in sorted(os.listdir(f"sounds/{sub}")):
            if f.endswith((".mp3", ".wav")): yield f"sounds/{sub}/{f}"


def lufs(f, loops=0):
    r = subprocess.run(["ffmpeg", "-nostats", "-stream_loop", str(loops), "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    v = [l.split()[1] for l in r.splitlines() if l.strip().startswith("I:")]
    return float(v[-1]) if v and v[-1] != "-inf" else None


def level(src, force=False):
    out = "leveled/" + src.rsplit(".", 1)[0] + ".mp3"
    if not force and os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src): return None
    os.makedirs(os.path.dirname(out), exist_ok=True); tmp = out + ".tmp.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", COMP, "-ar", "44100", "-ac", "2", tmp], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", tmp], capture_output=True, text=True).stdout or 1)
    i = lufs(tmp, loops=int(4 / max(d, .2)) if d < 4 else 0)  # short hits: measure them looped, silence padding would fool the meter
    g = max(-12, min(18, LEVEL - i)) if i is not None else 0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={g:.2f}dB,alimiter=limit=0.79:attack=3:release=60:level=disabled",
                    "-c:a", "libmp3lame", "-q:a", "3", out], check=True)
    os.remove(tmp); return out


if __name__ == "__main__":
    force = "--force" in sys.argv
    with ThreadPoolExecutor(6) as ex: done = [o for o in ex.map(lambda s: level(s, force), sources()) if o]
    print(f"leveled {len(done)} files → leveled/ (target {LEVEL} LUFS)")
