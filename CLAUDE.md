# MemeKit

A universal meme library (green-screen clips with sound, reaction GIFs with face crops, meme sounds, photo memes) for making
fun educational videos on any subject. **Read `README.md` first**, then `CATALOG.md` to pick memes by mood and meaning.
Use `hyperframes/memekit.py` to place them in HyperFrames videos (working example in `example/`).
Add memes with `tools/grow.py`, then add a meaning in `meta/meanings.json` and run `tools/rebuild_catalog.py`.
Respect the user's ratings from the review dashboard (`tools/dashboard.py`): prefer ❤️ favourites, never use 🚫 items.
Personal / educational use only.
Camera effects (zoom punch, Rock zoom, earthquake, deep fry, VHS, …): `hyperframes/camfx.js` + `kit.camfx(...)`, any video via `tools/camfx_render.py`,
rated in the Camera FX dashboard (`tools/dashboard.py --camfx`). Ratings live in `meta/ratings.json` as `camfx:<id>`; effect metadata in `meta/camfx.json`.

**User rules (Oct 2026):** memes at a NATURAL comedy pace — only on real punchlines (~1 per 15–30 s), never random gap fillers; variety, no repeats. Memes end on a HARD CUT (no exit animation). Meme audio = one stable level
~3 dB under the narration: always `mk.Kit(..., voice="audio/voiceover.wav")`, never hand-set `vol=`. Skill: `meme-edit`.
