// MemeKit animator: snappy pop-in (or a straight cut, enter:"cut"), a HARD CUT out (meme-edit style, no fade/slide exit)
// and sprite-sheet stepping for every entry in window.MEMEKIT (the `anims` dicts returned by memekit.py).
// Call MemeKit.animate(tl) on your paused root timeline, then register it.
window.MemeKit = {
  animate(tl, items = window.MEMEKIT || []) {
    let seed = 11; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const run = (list) => { for (const c of list) {
      if (!c) continue;
      if (Array.isArray(c)) { run(c); continue; }
      if (c.kind === "card") {
        const rot = (rnd() - 0.5) * 7, sel = `#${c.id} .mk-in`;
        if (c.enter === "cut") tl.fromTo(sel, { opacity: 0, rotation: rot }, { opacity: 1, duration: 0.01 }, c.t);
        else tl.fromTo(sel, { scale: 0.55, opacity: 0, rotation: rot - 6 }, { scale: 1, opacity: 1, rotation: rot, duration: 0.16, ease: "back.out(2.6)" }, c.t);
        if (c.sheet) { const S = c.sheet; const n = Math.ceil(c.d * S.fps);
          for (let k = 0; k < n; k++) { const f = k % S.n, col = f % S.cols, row = Math.floor(f / S.cols);
            tl.set(`#${c.id} .mk-sheet`, { backgroundPosition: `${S.cols > 1 ? (col / (S.cols - 1)) * 100 : 0}% ${S.rows > 1 ? (row / (S.rows - 1)) * 100 : 0}%` }, c.t + k / S.fps); } }
        (c.labs || []).forEach((lt, i) => tl.fromTo(`#${c.id}-l${i}`, { scale: 1.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.14, ease: "power4.out" }, lt));
        tl.set(sel, { opacity: 0 }, c.t + c.d);  // hard cut
      } else if (c.kind === "camfx") {
        if (window.CamFX) window.CamFX.add(tl, c); else console.warn("MemeKit: load hyperframes/camfx.js for camera effects");
      } else if (c.kind === "gs") {
        const sel = `#${c.id}`;
        if (!c.pop) tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.01 }, c.t);
        else tl.fromTo(sel, { scale: 0.6, y: 90, opacity: 0 }, { scale: 1, y: 0, opacity: 1, duration: 0.16, ease: "back.out(2.4)" }, c.t);
        tl.set(sel, { opacity: 0 }, c.t + c.d);  // hard cut
      }
    } };
    run(items);
    return tl;
  },
};
