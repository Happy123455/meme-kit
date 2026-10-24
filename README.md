# MemeKit — a universal meme library for funny explainer videos

**For Claude (or any editor) making fun, meme-packed educational videos on ANY subject.** Hand this folder to a new session and
say "use the meme kit". Personal / educational use only — the memes belong to their creators; never publish videos made with them
commercially or re-share the files.

## What's inside (648 items incl. 2025–26 memes, ~400 MB)

| folder | what | count |
|---|---|---|
| `greenscreen/` | meme clips **with sound**, green already removed → transparent `.webm` (VP9 alpha) + `.mp3`; plain ones are `.mp4`. Originals with green in `greenscreen/original/` for CapCut / Premiere / DaVinci | 68 |
| `gifs/` | reaction GIF clips: `<id>.mp4` (original), `<id>.jpg` sprite sheet (12 fps, 6 columns), `<id>_face.png` round face crops for face-swaps | 60 (36 with faces) |
| `sounds/meme/` | meme sound effects (vine boom, bruh, emotional damage, FBI open up, moye moye, rasode mein kaun tha, …), loudness-matched | 90 |
| `sounds/basic/` | clean SFX: whoosh, pop, impact, ding, crash, horns, typing, … (CC0/CC BY, credits in `CREDITS.md`) | 42 |
| `photos/` | photo meme templates (imgflip top 100 + memegen), 29 with known panel-label layouts | 308 |
| `camfx/` + `hyperframes/camfx.js` | **43 camera effects**: zoom punch, crash/dramatic/triple zoom, Rock eyebrow, dark Spider-Man zoom, earthquake, bass boosted, whip pans, spin, dutch tilt, deep fry, freeze-gray "Yup, that's me", VHS, glitch, TV-off, anime speed lines, sus red, emotional damage, thug life… each paired with its meme sound | 43 |
| `leveled/` | every meme sound re-levelled to −18 LUFS + compressed (`tools/level_audio.py`) — memekit plays these | |
| `catalog.json` | every item: id, type, **mood**, **what it means / when to use it**, files, size, duration, start point, layouts | |
| `CATALOG.md` | the same, grouped by type → mood, easy to read | |
| `hyperframes/` | drop-in code for HyperFrames videos: `memekit.py`, `memekit.css`, `memekit.js`, `memekit3d.js`, fonts | |
| `tools/` | `grow.py` (add more memes), `rebuild_catalog.py` | |
| `example/` | a working 12-second demo (`build_demo.py` → `index.html` → `demo.mp4`) | |

Includes popular **Indian memes** (Hera Pheri, TMKOC/Jethalal, rasode mein kaun tha, moye moye, Ashneer Grover) — great for Indian students.

## Review dashboard (your ratings steer every future video)

Double-click **`Open Meme Dashboard.command`** (or `python3 tools/dashboard.py`) → a page opens in the browser with every clip, GIF,
sound and photo. Click to play (with sound), rate **❤️ Fav / 👍 Good / 😐 Meh / 🚫 Never** and add notes. Keys: `1`–`4` rate, `0` clear,
`space` play, arrows move, `n` note. **▶ Review unrated** plays them one by one and moves on after each rating.
**Edit each green-screen clip / sound on its card:** drag on the waveform to keep only the part you want (✂️, double-click = whole
clip), 🔇 mute the clip's own audio, pick the screen rule (**AI decides / Always full / Never full**), and 🔗 pair a library sound with a
start time and a comment ("these go together"). Clips whose audio *is* a library sound show a green **🔁 same audio as …** button
(`tools/find_pairs.py`) — one click pairs it and mutes the clip. Every note is saved on that one meme only, and `memekit.py` prints
it the moment that meme is used, so the editor has to read it. Filters **✂️ edited** / **📝 notes** list everything you changed.
Ratings save instantly to `meta/ratings.json`; **Save to catalog** writes them into `catalog.json` / `CATALOG.md`.
Sessions must then: prefer ❤️, use 😐 only if nothing else fits, and **never use 🚫** (listed under "Do not use";
`memekit.find()` skips them and `kit.get()` warns).

## Camera FX (meme camera moves + edit effects)

Double-click **`Open Camera FX Dashboard.command`** (or `python3 tools/dashboard.py --camfx`; the meme dashboard links to it too). Every effect plays
live on a talking-person sample (Kokilaben, Steven He, a 3D edu clip) or **📁 your own video**. 🎯 Set focus = click the face; intensity slider; optional
caption text; meme sound on/off. Rate ❤️ 👍 😐 🚫 + notes exactly like the memes (same `meta/ratings.json`, keys `camfx:<id>`; **Save to catalog**).

- **In a HyperFrames video:** wrap the shot in a dedicated element (`<div id="stage">…</div>` — CamFX owns its transform/filter; keep text/memes outside
  it if they should not shake). Load `hyperframes/camfx.js` before `memekit.js`, then
  `html, anim = kit.camfx("zoom_punch", start=12.3, target="#stage", x=48, y=36)` (x, y = face in % of the stage; `k=` intensity, `dur=`, `cap="WHAT?!"`,
  `sound=False`). The paired meme sound comes with it. Effects stack (a zoom + a shake mix), all seek-safe.
  Plain JS: `CamFX.add(tl, {fx, t, d, target, x, y, k, cap})`.
- **On any video file (no coding):**
  `python3 tools/camfx_render.py talk.mp4 -o talk_fx.mp4 --focus 46,38 --fx zoom_punch@3.2 --fx "earthquake@7.5:k=1.4" --fx "freeze_gray@12:cap=Yup, that's me."`
  (`--snap 3.4,8` only saves check frames). Project kept in `_work/<name>/`. Example output: `camfx/demo_kokilaben.mp4`.
- Picking: `CATALOG.md` → "Camera effects" (category, mood, length, paired sound). Same rule: one effect per punchline, prefer ❤️, never 🚫.
  `freeze_gray` is the freeze *look* (B&W + record scratch + caption); for a true freeze, cut/pause the footage there.

## How a session should use it (do this in order)

1. **Read `CATALOG.md`** (≈500 lines). Every item has a mood, a one-line meaning and the user's rating (❤️ 👍 😐; 🚫 ones are listed separately — do not use them). Moods: shock, confusion, fail, success, sad,
   laugh, cool, suspicious, angry, waiting, hype, ending, warning, agree, disagree, thinking, money, chaos, cringe, proud, romance,
   dance, intro, calm, compare, pain, smart, dumb.
2. **Write the script first**, then place memes on the beats where the *meaning* matches the moment (a mistake → `fail`,
   a trick question → `suspicious`/`thinking`, the right method → `compare` (Drake), the end → `ending`).
3. **Make every meme carry a fact.** The meme is the memory hook, so the label or caption must restate the concept
   ("Drake: no to *using f = 0.8 directly*, yes to *f × efficiency, then f − n*"). Random jokes are fun but forgettable.
4. **Pace — natural, comedy first (user's rule, updated Oct 2026):** NO quota. A meme only where a real joke or a real
   reaction lands — a punchline, a mistake, a surprising fact. Roughly one meme every 15–30 s is typical; quiet stretches are fine.
   Never add a meme or a meme song just to fill a gap — random memes kill the laugh. Every meme restates the fact it sits on.
5. **Variety:** never reuse the same green-screen / GIF / photo in one video; mix all types (green-screen, GIF, photo, camera FX,
   sound) and pull in the **new 2025–26 memes** (brainrot, aura farming, chill guy, cooked, 6 7, absolute cinema…). Use `kit.pick(mood)` — it
   prefers ❤️/👍, skips what this video already used and what the last videos used (`kit.log_usage(name)` after each video).
6. `kit.report(total)` shows repeats and the mix; its gap list is only a hint — leave a gap if no joke belongs there.
7. **Cuts, not fades:** memes pop in fast (0.16 s) and end on a **hard cut** — that's how meme edits look. `enter="cut"` for a straight cut in.
8. **Audio:** pass the narration — `mk.Kit(..., voice="audio/voiceover.wav")`. All meme sounds come from `leveled/` (same loudness,
   compressed) at one volume ~3 dB under the voice: always clear enough to get the joke, never louder than the narration. Don't hand-tune
   `vol=` (ignored); `trim=-3` / `trim=+2` (dB) only for a real exception.
9. Check a few frames before rendering (`npx hyperframes snapshot`), then render.

### Creative recipes that worked very well

- **Face-swap:** put a round reaction face (`gifs/*_face.png`) on a 3D/animated character's head when they react
  (driver sees a buffalo → `pikachu`; nervous engineer → `sweating`; unbothered animal → `deal_with_it`).
- **Billboard in the world:** a GIF on a screen standing in the 3D scene (`mr_bean_wait` over concrete curing).
- **Green-screen pop-up from the bottom edge** with its sound after a sus line: `the_rock_eyebrow_raise`, `side_eye`, `suspicious_cat`.
- **Ending:** freeze-frame (grayscale) + record scratch + `to_be_continued` full-screen (its music plays).
- **Fail / success stamps:** `wasted_gta` on a wrong answer, `mission_passed_respect` on the right one.
- **Comparison memes with labels:** `drake-hotline-bling`, `buff-doge-vs-cheems`, `two-buttons`, `distracted-boyfriend`, `expanding-brain` (4 levels).
- **Sounds:** `vine-boom` on punch words, `rimshot` after a pun, `censor-beep` on a double meaning, `sad-trombone`/`bruh` on mistakes,
  `ka-ching` on cost, `crickets` after a bad joke.

## Using it in a HyperFrames project (tested)

```bash
ln -s /path/to/meme-kit  your-project/assets/memekit      # or copy it there
```
```python
import sys; sys.path.insert(0, "/path/to/meme-kit/hyperframes"); import memekit as mk
kit = mk.Kit(url_root="assets/memekit")
kit.find(mood="shock")                                    # search by mood / text / type
html, anim = kit.greenscreen("the_rock_eyebrow_raise", start=12.4, pos="left")    # pos: left/right/center/full; vol=, dur=, w=, x=, y=
html, anim = kit.gif("pikachu", start=5, dur=3, cap="Me seeing the exam paper:")  # reaction card (sprite sheet stepped)
html, anim = kit.photo("drake-hotline-bling", start=8, labels=["wrong way", "right way"])   # labels in the template's panels
html, anim = kit.photo("ancient-aliens", start=9, top="I'm not saying it was overkill", bottom="but it was overkill")
# Classic meme style is the default: the raw image + Impact top/bottom text with a black outline, no white card
# (Kit(meme_style="card") brings back the old caption card). Impact comes from the system; fonts/Anton-Regular.ttf is the open fallback.
html, anim = kit.greenscreen("aura_farming_boat_kid", 12, x=104, w=520, crop=(.36, .12, 1, .98))   # crop = zoom into the clip's subject
html, _    = kit.sound("vine-boom", start=8)
face       = kit.face_entry("pikachu", start=5, dur=3, anchor="driver", size=1.5)  # for Three.js scenes (memekit3d.js)
```
Put every `html` inside the root composition; set `window.MEMEKIT = [all anim dicts]`; load
`assets/memekit/hyperframes/memekit.css` and `memekit.js`; call `MemeKit.animate(tl)` on your paused GSAP root timeline before
registering it. See `example/build_demo.py` for the complete minimal file. For 3D: `import { memeClips3D } from
"./assets/memekit/hyperframes/memekit3d.js"`, create it with your scene/camera/anchors, call `.update(t)` in the `hf-seek` render.

Rules baked in (HyperFrames): every element is timed with `data-start`/`data-duration`; green-screen video is `muted` and its sound is a
separate `<audio>`; GIFs are sprite sheets because GIFs can't be seeked; clips start at their **start point** (`start` in the catalog —
e.g. `to_be_continued` content begins at 9.75 s, `giga_chad` at 8.75 s; sounds can begin later too, e.g. The Rock's boom is ~3 s in).

## Using it outside HyperFrames

- **CapCut / Premiere / DaVinci / After Effects:** use `greenscreen/original/*.mp4` with the editor's chroma key, or the
  transparent `.webm` directly; `gifs/*.mp4`; `photos/*`; `sounds/**/*.mp3`.
- **ffmpeg overlay** of a transparent clip with its sound at 12 s:
  `ffmpeg -i base.mp4 -c:v libvpx-vp9 -i greenscreen/side_eye.webm -i greenscreen/side_eye.mp3 -filter_complex "[1:v]setpts=PTS+12/TB[g];[0:v][g]overlay=x=60:y=H-h:eof_action=pass[v];[2:a]adelay=12000|12000[s];[0:a][s]amix=inputs=2:normalize=0[a]" -map "[v]" -map "[a]" out.mp4`
  (`-c:v libvpx-vp9` before the webm input is required to keep the alpha).
- **Remotion / web:** `<OffthreadVideo transparent src=".../x.webm">` + `<Audio>`; sprite sheets work as CSS backgrounds.

## Growing the kit

```bash
python3 tools/grow.py sound "emotional damage" "oh hell nah"          # MyInstants
python3 tools/grow.py greenscreen "skibidi" "goofy ahh"               # YouTube green-screen memes (needs yt-dlp)
python3 tools/grow.py gif "confused nick young" --face 0.5,0.4,0.8   # Giphy; --face cx,cy,size (fractions) adds a round face crop
python3 tools/grow.py drop greenscreen some_bad_id
```
`grow.py` re-levels the audio for you (`tools/level_audio.py`). Then **add a meaning** for each new id in `meta/meanings.json` (`"id": ["mood", "what it shows / when to use it"]`) and run
`python3 tools/rebuild_catalog.py`. Always look at new green-screen clips over a coloured background first — some searches return
the wrong video or key badly (drop those). Requirements: ffmpeg/ffprobe, curl, Python with pillow + numpy, yt-dlp.
Paid bundles exist for a much bigger library (e.g. Notelu's 1300+ meme pack on itch.io, 5,750-clip packs on Gumroad); drop their
files in `_downloads/` and key them with the same `greenscreen` logic.

## Files a session should not need to open

`meta/*.json` (raw metadata that `rebuild_catalog.py` merges), `_downloads/` (untrusted raw downloads — never run anything from there).
