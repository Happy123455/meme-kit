"""MemeKit for HyperFrames — find memes and emit the timed HTML for them.

    import sys; sys.path.insert(0, "path/to/meme-kit/hyperframes"); import memekit as mk
    kit = mk.Kit(url_root="assets/memekit", voice="audio/voiceover.wav")   # voice → meme sound sits ~3 dB under it
    kit.find(mood="shock")                            # → list of catalog items
    kit.pick("shock", type="gif")                     # → one id, variety-aware (not used yet in this video / recent videos)
    html, anims = kit.greenscreen("the_rock_eyebrow_raise", start=12.4, pos="left")
    html, anims = kit.gif("pikachu", start=5, cap="Me when the buffalo appears")
    html, anims = kit.photo("drake-hotline-bling", start=8, labels=["wrong way", "right way"])
    html, anims = kit.sound("vine-boom", start=8)
    html, anims = kit.camfx("zoom_punch", start=8, target="#stage", x=48, y=38)   # camera effect + its sound (load camfx.js)
    face = kit.face_entry("pikachu", start=5, dur=3, anchor="driver")   # for memekit3d.js (Three.js scenes)
    kit.report(total=95)                              # density + variety check — run it before rendering
    html = kit.render_stem("audio/memes.wav", total=95, voice="audio/voiceover.wav")   # with stem=True: one smooth meme-audio track
    kit.log_usage("my-video")                         # remember what this video used, so the next one picks different memes

Put every `html` string inside your root composition, collect every `anims` dict into `window.MEMEKIT = [...]`,
load hyperframes/memekit.css + memekit.js, and call `MemeKit.animate(tl)` before registering your GSAP timeline.
All elements are timed with data-start/data-duration (HyperFrames rule), ids are unique (mk1, mk2, …).

Audio: every meme sound plays from leveled/ (all at -18 LUFS, compressed — tools/level_audio.py) at ONE kit-wide volume,
so no meme is ever louder than the narration. Per-call `vol=` is ignored on purpose; use `trim=` (dB, -6…+3) for a rare exception.
Kit(stem=True) goes further: no <audio> per meme — every meme sound is mixed into one WAV by render_stem() with a 12 ms fade-in,
a 120 ms fade-out (hard visual cuts never click), a gentle dip while the narrator speaks, and a soft limiter. Smoothest result.
Kit(strict=True) only allows items the user rated ❤️ favorite or 👍 good (raises on anything else).
Memes end on a hard cut (meme-edit style); `enter="cut"` also removes the quick pop-in."""
import html as _h, json, os, random, re, subprocess

W, H = 1920, 1080
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVEL = -18.0          # loudness of the files in leveled/
UNDER_VOICE = 3.0      # meme sound sits this many dB under the narration
RANK = {"favorite": 0, "good": 1, None: 2, "meh": 3, "never": 4}


def loudness(path):
    """Integrated loudness (LUFS) of an audio/video file, or None."""
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    v = [l.split()[1] for l in r.splitlines() if l.strip().startswith("I:")]
    try: return float(v[-1])
    except (IndexError, ValueError): return None


class Kit:
    def __init__(self, url_root="assets/memekit", track_base=60, voice=None, voice_lufs=None, under_voice=UNDER_VOICE, seed=7,
                 strict=False, stem=False):
        """voice: path to the narration (or voice_lufs=-23.9) → one meme volume that sits `under_voice` dB below it.
        Without either, assumes a -20 LUFS voice. strict: only ❤️/👍 items. stem: collect audio for render_stem()."""
        self.strict, self.stem, self.events, self.noted = strict, stem, [], set()
        self.root = url_root.rstrip("/")
        self.cat = {(i["type"], i["id"]): i for i in json.load(open(os.path.join(KIT, "catalog.json")))["items"]}
        self.n = 0; self.track = track_base; self.used = []; self.rng = random.Random(seed)
        if voice_lufs is None and voice: voice_lufs = loudness(voice)
        self.voice_lufs = voice_lufs if voice_lufs is not None else -20.0
        self.bus = min(1.0, 10 ** ((self.voice_lufs - under_voice - LEVEL) / 20))

    # ---------- search ----------
    def find(self, mood=None, text=None, type=None, include_never=False, min_rating=None):
        """Search; favourites first. 'never' items (user said do not use) are skipped unless include_never."""
        out = []
        for i in self.cat.values():
            if i.get("rating") == "never" and not include_never: continue
            if min_rating and RANK[i.get("rating")] > RANK[min_rating]: continue
            if type and i["type"] != type: continue
            if mood and i["mood"] != mood: continue
            if text and text.lower() not in (i["id"] + " " + i.get("what", "")).lower(): continue
            out.append(i)
        return sorted(out, key=lambda i: RANK[i.get("rating")])

    def pick(self, mood, type=None, n=1, text=None):
        """Variety-aware pick: favourites/good weigh most, anything already used in this video is skipped,
        anything used in the last few videos (meta/usage.json) is pushed down. Returns an id (n=1) or a list of ids."""
        recent = {}
        for age, v in enumerate(reversed(_load(os.path.join(KIT, "meta/usage.json"), [])[-4:])):
            for k in v["items"]: recent.setdefault(k, age)
        here = {f"{t}:{i}" for t, i, _ in self.used}
        pool = []
        for i in self.find(mood=mood, type=type, text=text):
            k = f"{i['type']}:{i['id']}"
            if k in here: continue
            w = {0: 6, 1: 4, 2: 2, 3: 0.4}[RANK[i.get("rating")]]
            if k in recent: w *= 0.15 + 0.2 * recent[k]
            pool.append((i["id"], w))
        out = []
        while pool and len(out) < n:
            r = self.rng.random() * sum(w for _, w in pool)
            for j, (i, w) in enumerate(pool):
                r -= w
                if r <= 0: out.append(i); pool.pop(j); break
        return (out[0] if out else None) if n == 1 else out

    def get(self, type, id):
        if (type, id) not in self.cat: raise KeyError(f"no {type} '{id}' — see CATALOG.md")
        i = self.cat[(type, id)]
        if i.get("rating") == "never": print(f"memekit: warning — the user marked {type} '{id}' as NEVER USE ({i.get('note') or 'no note'})")
        if self.strict and i.get("rating") not in ("favorite", "good"):
            raise ValueError(f"memekit strict: {type} '{id}' is rated {i.get('rating') or 'unrated'} — only ❤️/👍 allowed")
        if i.get("note") and (type, id) not in self.noted:  # the user's note belongs to this one meme: always surface it
            self.noted.add((type, id)); print(f"memekit NOTE for {type}:{id} — read and follow: {i['note']}")
        return i

    def _id(self):
        self.n += 1; return f"mk{self.n}"

    def _u(self, p): return f"{self.root}/{p}"

    def _aud(self, p):
        """The leveled copy of an audio file when it exists (tools/level_audio.py)."""
        lv = "leveled/" + p.rsplit(".", 1)[0] + ".mp3"
        return lv if os.path.exists(os.path.join(KIT, lv)) else p

    def _vol(self, trim=0.0):
        return round(min(1.0, self.bus * 10 ** (max(-6.0, min(3.0, trim)) / 20)), 3)

    def _use(self, type, id, t, warn=True):
        if warn and any(u[:2] == (type, id) for u in self.used):
            print(f"memekit: '{id}' is used twice in this video — kit.pick() finds a fresh one")
        self.used.append((type, id, t))

    # ---------- elements ----------
    def greenscreen(self, id, start, dur=None, pos="right", w=None, x=None, y=None, vol=None, trim=0.0, mute=False, z=37, pop=None, enter="pop", rate=1.0, skip=0.0):
        """Transparent meme clip + its own sound. pos: left/right/center/full. Ends on a hard cut. (trim = gain in dB.)
        The user's dashboard edits are applied here: the trimmed section only, muted clip audio, the paired library sound,
        and the full-screen rule ("full" = always full screen, "window" = never full screen)."""
        g = self.get("greenscreen", id); e = self._id(); self._use("greenscreen", id, start)
        cut = g.get("trim") or [g["start"], g["dur"]]; ms, end = cut[0] + skip, min(cut[1], g["dur"])   # skip = start later in the clip
        rate = max(.5, min(2.0, rate))   # rate < 1 = slow motion (e.g. the GTA "wasted" feel); sound keeps its pitch
        d = min(dur or (end - ms) / rate - 0.05, (end - ms) / rate - 0.02)
        pr = f' data-playback-rate="{rate:g}"' if rate != 1 else ""
        if g.get("screen") == "full" and pos != "full": print(f"memekit: '{id}' is always full screen (user rule) — using pos='full'"); pos = "full"
        if g.get("screen") == "window" and pos == "full": print(f"memekit: '{id}' must never be full screen (user rule) — using pos='center'"); pos, w = "center", w or 900
        mute = mute or bool(g.get("mute"))
        w = w or (760 if g["alpha"] else 560); h = int(w * g["h"] / g["w"])
        if pos == "full": w, h, x, y = W, H, 0, 0
        x = x if x is not None else {"left": 90, "right": W - 90 - w, "center": (W - w) // 2}.get(pos, W - 90 - w)
        y = y if y is not None else (H - h - 60 if g["alpha"] else max(140, (H - h) // 2))  # bottom stays inside the 90% action-safe box
        self.track += 1
        out = (f'<div id="{e}" class="mk-gs{"" if g["alpha"] else " mk-card"}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;z-index:{z}">'
               f'<video id="{e}-v" class="clip" src="{self._u(g["video"])}" muted playsinline data-start="{start:.3f}" data-duration="{d:.3f}" data-media-start="{ms:.3f}"{pr} data-track-index="{self.track}"></video></div>')
        if g.get("audio") and not mute and self.stem:
            self.events.append((self._aud(g["audio"]), start, ms, d, self._vol(trim), rate))
        elif g.get("audio") and not mute:
            out += f'\n<audio id="{e}-a" class="clip" src="{self._u(self._aud(g["audio"]))}" data-start="{start:.3f}" data-duration="{d:.3f}" data-media-start="{ms:.3f}"{pr} data-track-index="{self.track + 40}" data-volume="{self._vol(trim)}"></audio>'
        if g.get("pair"):  # the user's chosen library sound, lined up where they put it in the clip
            pr = g["pair"]; off = float(pr.get("at") or 0) - ms
            h, _ = self.sound(pr["sound"], start + max(0.0, off) - 0.033, dur=max(0.1, d - max(0.0, off)), trim=trim, _paired=True, _skip=max(0.0, -off))
            out += ("\n" + h) if h else ""
        return out, dict(kind="gs", id=e, t=start, d=d, pop=(pos != "full" if pop is None else pop) and enter != "cut")

    def gif(self, id, start, dur=3.0, pos="right", w=480, cap=None, x=None, y=None, z=35, enter="pop"):
        """Animated reaction card (sprite sheet stepped frame by frame)."""
        g = self.get("gif", id); e = self._id(); h = int(w * g["fh"] / g["fw"]); self._use("gif", id, start)
        x = x if x is not None else {"left": 110, "right": W - 110 - w - 32, "center": (W - w - 32) // 2}[pos]
        y = y if y is not None else max(150, (H - h - 120) // 2)
        capd = f'<div class="mk-cap" style="width:{w}px">{_rich(cap)}</div>' if cap else ""
        out = (f'<div id="{e}" class="clip mk-meme" data-start="{start:.3f}" data-duration="{dur:.3f}" style="z-index:{z}"><div class="mk-in" style="left:{x}px;top:{y}px">{capd}'
               f'<div class="mk-sheet" style="width:{w}px;height:{h}px;background-image:url({self._u(g["sheet"])});background-size:{g["cols"] * 100}% {g["rows"] * 100}%"></div></div></div>')
        return out, dict(kind="card", id=e, t=start, d=dur, pos=pos, enter=enter, sheet=dict(n=g["frames"], cols=g["cols"], rows=g["rows"], fps=g["fps"]))

    def photo(self, id, start, dur=3.6, pos="right", w=620, cap=None, labels=None, x=None, y=None, z=35, label_gap=0.9, enter="pop"):
        """Photo meme: caption on top (modern style) and/or labels in its panels (layouts for known templates)."""
        p = self.get("photo", id); e = self._id(); ar = p["h"] / p["w"]; self._use("photo", id, start)
        cap_h = 0 if not cap else 60 + 44 * (len(cap) // 34)
        if w * ar > 800 - cap_h: w = int((800 - cap_h) / ar)
        x = x if x is not None else {"left": 110, "right": W - 110 - w - 32, "center": (W - w - 32) // 2}[pos]
        y = y if y is not None else max(150, int((H - (w * ar + cap_h + 32)) // 2))
        labs, times = "", []
        for i, txt in enumerate(labels or []):
            if not p.get("layout") or i >= len(p["layout"]): break
            lx, ly, lw, lh, *st = p["layout"][i]; bw, bh = w * lw / 100, w * ar * lh / 100
            fs = (bw * bh / (max(4, len(txt)) * 0.58 * 1.25)) ** 0.5 * 0.92
            fs = int(max(22, min(64, fs, (bw - 12) / (max(len(w) for w in re.sub(r"<[^>]+>", "", str(txt)).split() or [""]) * 0.72 + .1))))  # longest word fits the slot
            labs += (f'<div id="{e}-l{i}" class="mk-lab{" mk-dark" if st and st[0] == "dark" else ""}" style="left:{lx}%;top:{ly}%;width:{lw}%;height:{lh}%;font-size:{fs}px">{_rich(txt)}</div>')
            times.append(round(start + 0.35 + i * label_gap, 3))
        capd = f'<div class="mk-cap" style="width:{w}px">{_rich(cap)}</div>' if cap else ""
        out = (f'<div id="{e}" class="clip mk-meme" data-start="{start:.3f}" data-duration="{dur:.3f}" style="z-index:{z}"><div class="mk-in" style="left:{x}px;top:{y}px">{capd}'
               f'<div class="mk-img" style="width:{w}px"><img src="{self._u(p["file"])}" alt="">{labs}</div></div></div>')
        return out, dict(kind="card", id=e, t=start, d=dur, pos=pos, enter=enter, labs=times)

    def sound(self, id, start, vol=None, dur=None, trim=0.0, _paired=False, _skip=0.0):
        """A meme sound (trim = gain in dB). Uses only the section the user selected in the dashboard, if any."""
        s = self.get("sound", id); e = self._id(); self.track += 1
        cut = s.get("trim") or [0.0, s["dur"]]; ms = cut[0] + _skip; L = max(0.05, cut[1] - ms)
        d = min(dur or L, L)
        if not _paired: self._use("sound", id, start, warn=False)  # punch sounds (vine boom…) may repeat
        if self.stem: self.events.append((self._aud(s["file"]), start + 0.033, ms, d, self._vol(trim))); return "", None
        return (f'<audio id="{e}" class="clip" src="{self._u(self._aud(s["file"]))}" data-start="{start + 0.033:.3f}" data-duration="{d:.3f}" data-media-start="{ms:.3f}" data-track-index="{self.track + 40}" data-volume="{self._vol(trim)}"></audio>', None)

    def camfx(self, id, start, target="#stage", dur=None, x=50, y=45, k=1.0, cap=None, sound=True, vol=None, trim=0.0, hold=None, z=None):
        """Camera effect on the element holding your shot (a wrapper div — CamFX owns its transform/filter).
        x, y = focus point (face) in % of the target; k = intensity; cap = caption text for effects that have one.
        Its paired meme sound(s) come along unless sound=False. Needs hyperframes/camfx.js loaded before memekit.js runs."""
        f = self.get("camfx", id); d = dur or f["d"]; out = []; self._use("camfx", id, start, warn=False)  # effects may repeat
        for sid, at, _v in (f.get("sound") or []) if sound else []:
            if self.strict and self.cat.get(("sound", sid), {}).get("rating") not in ("favorite", "good"): continue  # paired sfx not rated ❤️/👍
            out.append(self.sound(sid, start + at * d, trim=trim, _paired=True)[0])
        a = dict(kind="camfx", fx=id, t=round(start, 3), d=d, target=target, x=x, y=y, k=k, hold=f.get("hold", False) if hold is None else hold)
        if cap is not None: a["cap"] = cap
        if z: a["z"] = z
        return "\n".join(out), a

    def face_entry(self, id, start, dur, anchor, size=1.6, dy=0.0, billboard=False):
        """Entry for memekit3d.js: a round face (or a rectangular billboard screen) that follows a 3D anchor."""
        g = self.get("gif", id); face = g["face"] and not billboard; self._use("gif", id, start)
        return dict(src=self._u(g["face"] if face else g["sheet"]), kind="face" if face else "tv", t=start, d=dur, anchor=anchor, size=size, dy=dy,
                    n=g["frames"], cols=g["cols"], rows=g["rows"], fps=g["fps"], ar=g["fh"] / g["fw"])

    # ---------- one smooth meme-audio stem (stem=True) ----------
    def render_stem(self, out_wav, total, voice=None, duck_db=3.0, fade_in=.012, fade_out=.12, url=None, sr=48000):
        """Mix every collected meme sound into one stereo WAV: per-clip fades (no clicks at hard cuts), a gentle dip of
        `duck_db` while the narrator speaks (voice = narration WAV), and a soft limiter at −1 dBFS.
        Returns the <audio> tag to put in the root composition (src = url or out_wav)."""
        import numpy as np
        N = int(total * sr) + sr; mix = np.zeros((N, 2), np.float32)
        for f, t0, ms, d, g, *r in self.events:
            rate = r[0] if r else 1.0
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ms:.3f}", "-t", f"{d * rate:.3f}", "-i", os.path.join(KIT, f), "-ac", "2", "-ar", str(sr),
                                  *(["-af", f"atempo={rate:g}"] if rate != 1 else []), "-f", "f32le", "-"], capture_output=True).stdout
            x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
            if not len(x): continue
            n = len(x); a = min(n, int(fade_in * sr)); b = min(n, int(fade_out * sr))
            x[:a] *= np.linspace(0, 1, a)[:, None]; x[n - b:] *= np.linspace(1, 0, b)[:, None]
            i = int(t0 * sr); j = min(N, i + n); mix[i:j] += x[:j - i] * g
        if voice and duck_db > 0:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", voice, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
            v = np.frombuffer(raw, np.float32); hop = sr // 50
            rms = np.sqrt(np.convolve(v ** 2, np.ones(hop) / hop, "same"))[::hop]
            on = (rms > 0.15 * np.percentile(rms, 95)).astype(np.float32)
            target = np.where(on > 0, 10 ** (-duck_db / 20), 1.0); env = np.empty_like(target); e = 1.0
            for k, tg in enumerate(target):  # 40 ms attack, 350 ms release (per 20 ms hop)
                e += (tg - e) * (0.5 if tg < e else 0.055); env[k] = e
            env = np.interp(np.arange(N) / hop, np.arange(len(env)), env, right=1.0).astype(np.float32)
            mix *= env[:, None]
        ceil = 10 ** (-1 / 20); mix = ceil * np.tanh(mix / ceil)  # soft limiter
        import wave
        w = wave.open(out_wav, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(mix[:int(total * sr)], -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
        return f'<audio id="memes" class="clip" src="{url or out_wav}" data-start="0" data-duration="{total:.3f}" data-track-index="8"></audio>'

    # ---------- pacing / variety ----------
    def report(self, total, max_gap=9.0):
        """Print meme density, long quiet stretches, repeats and the type mix. Informational: the pace is natural (jokes, not a quota)."""
        ts = sorted(t for _, _, t in self.used); n = len(ts); vis = [u for u in self.used if u[0] in ("greenscreen", "gif", "photo")]
        print(f"memekit: {n} meme moments in {total:.0f}s ({60 * n / max(total, 1):.1f}/min), {len(vis)} visual; meme volume {self.bus:.2f} "
              f"(voice {self.voice_lufs:.1f} LUFS) — natural pace: memes only where a joke lands, no quota")
        edges = [0.0] + ts + [total]; gaps = sorted(((b - a, a) for a, b in zip(edges, edges[1:]) if b - a > max_gap), reverse=True)
        for g, a in gaps[:6]: print(f"  · {g:.1f}s without a meme from {a:.1f}s — fine unless a joke belongs there")
        types = {}
        for t, i, _ in self.used: types.setdefault(t, set()).add(i)
        print("  mix (distinct): " + ", ".join(f"{t} {len(v)}" for t, v in types.items()))
        dup = sorted({i for t, i, _ in self.used if t in ("greenscreen", "gif", "photo") and sum(1 for u in self.used if u[:2] == (t, i)) > 1})
        if dup: print("  repeats:", ", ".join(dup))
        return dict(moments=n, per_min=60 * n / max(total, 1), gaps=gaps, repeats=dup)

    def log_usage(self, name):
        """Append what this video used to meta/usage.json so the next videos rotate to fresh memes."""
        p = os.path.join(KIT, "meta/usage.json"); log = [v for v in _load(p, []) if v["video"] != name]
        log.append(dict(video=name, items=sorted({f"{t}:{i}" for t, i, _ in self.used if t != "camfx"})))
        json.dump(log[-30:], open(p, "w"), indent=1)


def _load(p, d):
    try: return json.load(open(p))
    except (OSError, ValueError): return d


def _rich(s):
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _h.escape(str(s), quote=True))
    return out.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
