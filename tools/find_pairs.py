"""Find green-screen clips whose audio is (part of) a sound that is also in the sound library, e.g. wasted_gta ↔ wasted.
  python3 tools/find_pairs.py          → meta/pairs_auto.json  {"greenscreen:<id>": [{"sound": id, "score": 0.93, "at": 1.2}]}
`at` = where in the clip the library sound lines up (seconds). The dashboard shows these as "🔁 same audio as …" suggestions;
nothing is paired until the user accepts one. Method: 24-band log spectrogram fingerprints, best sliding match (cosine)."""
import json, os, subprocess
import numpy as np

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(KIT)
SR, HOP, NFFT, BANDS = 11025, 256, 1024, 24
EDGES = np.geomspace(120, 5000, BANDS + 1)
STRONG, NAMED = 0.92, 0.80   # accept a strong match, or a weaker one when the names share a word
STOP = {"the", "a", "of", "meme", "sound", "1", "2"}


def feat(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if len(x) < NFFT * 2: return None, None
    n = 1 + (len(x) - NFFT) // HOP
    fr = np.lib.stride_tricks.as_strided(x, (n, NFFT), (x.strides[0] * HOP, x.strides[0])) * np.hanning(NFFT)
    S = np.abs(np.fft.rfft(fr, axis=1)) ** 2
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    B = np.stack([S[:, (f >= a) & (f < b)].sum(1) for a, b in zip(EDGES[:-1], EDGES[1:])], 1)
    loud = B.sum(1)
    F = np.log(B + 1e-9); F -= F.mean(1, keepdims=True)
    F /= np.linalg.norm(F, axis=1, keepdims=True) + 1e-9
    return F, loud > np.percentile(loud, 30) * 1.0  # frames that carry sound


def match(A, a_on, B, b_on):
    """Best cosine match of the shorter fingerprint slid along the longer one (silent frames ignored)."""
    swap = len(A) < len(B)
    L, l_on, Sh, s_on = (B, b_on, A, a_on) if swap else (A, a_on, B, b_on)
    n = len(Sh)
    if n < 25 or s_on.sum() < 40: return 0.0, 0   # needs ≈1 s of real sound, short blips match anything
    W = np.lib.stride_tricks.sliding_window_view(L, (n, BANDS))[:, 0]          # (offsets, n, bands)
    sims = np.einsum("knb,nb->kn", W, Sh)[:, s_on].mean(1)
    k = int(np.argmax(sims)); return float(sims[k]), (0 if swap else k)


if __name__ == "__main__":
    gs = json.load(open("meta/greenscreen.json"))
    snd = {f.rsplit(".", 1)[0]: f"sounds/{sub}/{f}" for sub in ("meme", "basic") for f in sorted(os.listdir(f"sounds/{sub}")) if f.endswith((".mp3", ".wav"))}
    SF = {k: feat(v) for k, v in snd.items()}
    out = {}
    for gid, g in sorted(gs.items()):
        if not g.get("audio"): continue
        A, a_on = feat(g["audio"])
        if A is None: continue
        hits = []
        for sid, (B, b_on) in SF.items():
            if B is None: continue
            s, k = match(A, a_on, B, b_on)
            shared = (set(gid.split("_")) & set(sid.split("-"))) - STOP
            if s >= STRONG or (s >= NAMED and shared): hits.append(dict(sound=sid, score=round(s, 3), at=round(k * HOP / SR, 2)))
        if hits:
            out[f"greenscreen:{gid}"] = sorted(hits, key=lambda h: -h["score"])[:3]
            print(f"{gid:34s} → " + ", ".join(f"{h['sound']} ({h['score']:.2f} @ {h['at']}s)" for h in out[f"greenscreen:{gid}"]))
    json.dump(out, open("meta/pairs_auto.json", "w"), indent=1)
    print(len(out), "clips with a matching library sound → meta/pairs_auto.json")
