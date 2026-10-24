// CamFX — meme camera moves and edit effects (zoom punch, Rock zoom, earthquake, deep fry, whip pan, VHS, …)
// for HyperFrames or any GSAP timeline. Seek-safe: every effect is a pure function of time.
//
//   CamFX.add(tl, { fx: "zoom_punch", t: 3.2, d: 0.9, target: "#stage", x: 50, y: 40, k: 1, cap: "WHAT?!" })
//
// target = the element that holds your footage/scene (a dedicated wrapper — CamFX owns its transform and filter).
// x, y   = focus point in % of the target (the face), k = intensity (1 = normal), cap = caption text (some effects have one).
// Overlays (flash, vignette, speed lines, captions…) go in a layer CamFX places over the target.
// Effects mix by channel: zooms multiply, shakes and rotations add, colour filters stack.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const io = (x) => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const eo = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const ei = (x) => Math.pow(clamp(x), 3);
  const back = (x) => { x = clamp(x); const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const elastic = (x) => { x = clamp(x); return x === 0 || x === 1 ? x : Math.pow(2, -10 * x) * Math.sin((x * 10 - .75) * 2 * Math.PI / 3) + 1; };
  const env = (p, a = .1, r = .15) => Math.min(a ? clamp(p / a) : 1, r ? clamp((1 - p) / r) : 1); // attack / hold / release
  const hash = (n) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const jit = (t, rate, seed = 0) => hash(Math.floor(t * rate) + seed * 1013) * 2 - 1; // stepped random −1…1
  const wave = (t, seed = 0) => Math.sin(t * 1.3 + seed) * .5 + Math.sin(t * 2.7 + seed * 2.1) * .3 + Math.sin(t * 5.1 + seed * 3.3) * .2;
  const pulseAt = (lt, at, rate) => Math.exp(-Math.max(0, lt - at) * rate) * (lt >= at ? 1 : 0); // decaying hit

  // zoom toward the focus point and pull it toward the centre by m (never exposing an edge)
  function zoomTo(c, s, m = .5) {
    const fx = (50 - c.x) * m * (s - 1), fy = (50 - c.y) * m * (s - 1);
    return { s, ox: c.x, oy: c.y, px: clamp(fx, (100 - c.x) * (1 - s), c.x * (s - 1)), py: clamp(fy, (100 - c.y) * (1 - s), c.y * (s - 1)) };
  }
  const shake = (lt, amp, rate = 26, rot = 0) => ({ px: jit(lt, rate, 1) * amp, py: jit(lt, rate, 2) * amp, r: jit(lt, rate, 3) * rot, s: 1 + Math.abs(amp) * .028 });
  const mix = (...o) => { const r = {}; for (const x of o) for (const k in x) r[k] = k in r && MUL.has(k) ? r[k] * x[k] : k in r && ADD.has(k) ? r[k] + x[k] : x[k]; return r; };

  // ---------- the effects: f(p 0→1, c) → channels; c = { lt (s since start), d, k, x, y, cap }, return { …, o: overlays } ----------
  const FX = {
    // ZOOM
    zoom_punch: (p, c) => { const a = eo(p / .05) * (1 - io((p - .8) / .2)); const h = pulseAt(c.lt, 0, 12);
      return mix(zoomTo(c, 1 + .38 * c.k * a, .55), { px: jit(c.lt, 30, 1) * .7 * h * c.k, py: jit(c.lt, 30, 2) * .7 * h * c.k }); },
    crash_zoom: (p, c) => { const a = io(p / .28) * (1 - eo((p - .86) / .14)); const mv = Math.sin(Math.PI * clamp(p / .28)) + Math.sin(Math.PI * clamp((p - .86) / .14));
      return mix(zoomTo(c, 1 + 1.05 * c.k * a, .7), { blur: 9 * mv * c.k, rgb: 7 * mv * c.k }); },
    dramatic_zoom: (p, c) => { const m = io(p / .85) * (1 - eo((p - .93) / .07));
      return mix(zoomTo(c, 1 + .55 * c.k * m, .6), { sat: 1 - .25 * m, con: 1 + .15 * m, o: { vig: [.7 * m] } }); },
    triple_zoom: (p, c) => { const step = p < 1 / 3 ? 0 : p < 2 / 3 ? 1 : 2, t0 = step * c.d / 3, lv = [1.2, 1.48, 1.9][step];
      const a = eo((c.lt - t0) / .06) * (1 - io((p - .92) / .08)), prev = step ? [1, 1.2, 1.48][step] : 1, h = pulseAt(c.lt, t0, 14);
      return mix(zoomTo(c, 1 + (lerp(prev, lv, a) - 1) * c.k * (1 - io((p - .92) / .08)), .7), { px: jit(c.lt, 30, 1) * h, py: jit(c.lt, 30, 2) * h,
        o: { cap: c.cap ? [step === 2 ? env(p, 0, .08) : 0, back((c.lt - 2 * c.d / 3) / .25)] : null } }); },
    rock_eyebrow: (p, c) => { const m = io(p / .9) * (1 - eo((p - .95) / .05));
      return mix(zoomTo(c, 1 + .5 * c.k * m, .6), { gray: .85 * m, con: 1 + .1 * m, o: { vig: [.55 * m] } }); },
    dark_zoom: (p, c) => { const m = io(p / .92) * (1 - eo((p - .95) / .05));
      return mix(zoomTo(c, 1 + .28 * c.k * m, .5), { bri: 1 - .55 * m, con: 1 + .35 * m, sat: 1 - .3 * m, o: { vig: [.9 * m] } }); },
    zoom_out_reveal: (p, c) => { const m = 1 - eo(p / .7); return mix(zoomTo(c, 1 + 1.3 * c.k * m, .8), { blur: 3 * m * m }); },
    ken_burns: (p, c) => mix(zoomTo(c, 1 + .16 * c.k * io(p), .3), { px: (io(p) - .5) * 2.4 * c.k }),
    mind_blown: (p, c) => { const b = .35, pre = ei(p / b), h = pulseAt(c.lt, b * c.d, 5), out = 1 - io((p - .85) / .15);
      const s = p < b ? 1 + .6 * pre * c.k : 1 + (.25 + .35 * h) * c.k * out;
      return mix(zoomTo(c, s, .6), shake(c.lt, 2.4 * h * c.k, 30, 2 * h), { blur: p < b ? 4 * pre : 6 * h, bri: 1 + 1.4 * h, o: { flash: [p < b ? 0 : h], lines: [p < b ? 0 : .95 * Math.min(1, h * 2) * out, 1 + .4 * (1 - h)] } }); },

    // SHAKE
    shake: (p, c) => { const e = env(p, .08, .2); return shake(c.lt, 1.2 * c.k * e, 24, .8 * c.k * e); },
    earthquake: (p, c) => { const e = env(p, .05, .2);
      return mix(shake(c.lt, 3.4 * c.k * e, 30, 2.6 * c.k * e), { s: 1 + .1 * e, blur: 1.6 * e, rgb: 6 * e * Math.abs(jit(c.lt, 30, 4)) }); },
    impact_hit: (p, c) => { const h = pulseAt(c.lt, 0, 9);
      return { px: Math.sin(c.lt * 55) * 2.4 * c.k * h, py: Math.cos(c.lt * 47) * 1.7 * c.k * h, s: 1 + .1 * c.k * h, o: { flash: [.55 * pulseAt(c.lt, 0, 14)] } }; },
    rage_vibrate: (p, c) => { const e = env(p, .1, .15);
      return mix(zoomTo(c, 1 + .12 * e * c.k, .4), shake(c.lt, .8 * c.k * e, 40, .6 * e), { sat: 1 + .7 * e, con: 1 + .15 * e, o: { tint: [.5 * e, "#ff4545", "multiply"] } }); },
    bass_boosted: (p, c) => { const e = env(p, .04, .12), beat = Math.pow(Math.abs(Math.sin(Math.PI * c.lt * 4)), 6);
      return mix(zoomTo(c, 1 + (.15 + .14 * beat) * e * c.k, .4), shake(c.lt, 3 * e * c.k, 30, 2 * e),
        { sat: 1 + 3 * e, con: 1 + 1.1 * e, bri: 1 + .1 * e, hue: -10 * e, rgb: 5 * e, blur: .6 * e, o: { grain: [.5 * e] } }); },
    handheld: (p, c) => { const e = env(p, .15, .15);
      return { px: wave(c.lt * .9, 1) * .7 * c.k * e, py: wave(c.lt * .8, 2) * .6 * c.k * e, r: wave(c.lt * .7, 3) * .5 * c.k * e, s: 1 + .045 * e }; },
    heartbeat: (p, c) => { const ph = (c.lt % .833) / .833, beat = Math.exp(-((ph - .05) ** 2) / .0015) + .7 * Math.exp(-((ph - .22) ** 2) / .0015), e = env(p, .1, .1);
      return mix(zoomTo(c, 1 + (.03 + .07 * beat * c.k) * e, .3), { sat: 1 - .2 * e, o: { vig: [(.35 + .35 * beat) * e, "#5a0000"] } }); },

    // MOVE / TRANSITION
    whip_pan_left: (p, c) => whip(p, c, -1),
    whip_pan_right: (p, c) => whip(p, c, 1),
    spin_360: (p, c) => { const m = io(p); return { r: 360 * m * Math.sign(c.k || 1), s: 1 - .35 * Math.sin(Math.PI * m) + .25 * Math.sin(Math.PI * m) ** 4, blur: 6 * Math.sin(Math.PI * m), ox: c.x, oy: c.y }; },
    dutch_tilt: (p, c) => { const m = eo(p / .15) * (1 - io((p - .85) / .15));
      return mix(zoomTo(c, 1 + .34 * m, .3), { r: -11 * c.k * m, con: 1 + .1 * m }); },
    drunk_wobble: (p, c) => { const e = env(p, .15, .15);
      return { r: Math.sin(c.lt * 2.2) * 4 * c.k * e, skew: Math.sin(c.lt * 1.6 + 1) * 6 * c.k * e, s: 1 + .14 * e, px: Math.sin(c.lt * 1.4) * 1.5 * e,
        blur: 1.2 * e, warp: 14 * e, wf: [.006, .012], wseed: 3, hue: Math.sin(c.lt * 1.1) * 15 * e }; },
    upside_down: (p, c) => { const m = back(p / .3) * (1 - io((p - .75) / .25)); return { r: 180 * m, s: 1 + .08 * Math.sin(Math.PI * clamp(m)), ox: 50, oy: 50 }; },
    bounce_boing: (p, c) => { const h = pulseAt(c.lt, 0, 4.5), w = Math.sin(c.lt * 26) * h * .2 * c.k;
      return { sqx: 1 + w, sqy: 1 - w, s: 1 + .2 * h, ox: c.x, oy: 92 }; },
    bonk_drop: (p, c) => { const hit = .22, fall = 1 - ei(p / hit), h = p < hit ? 0 : pulseAt(c.lt, hit * c.d, 7);
      return { py: -105 * fall * (p < hit ? 1 : 0), sqy: 1 - .2 * h * Math.cos(c.lt * 30), sqx: 1 + .12 * h * Math.cos(c.lt * 30), oy: 100, ox: 50, s: 1 + .2 * h,
        px: jit(c.lt, 30, 1) * 1.2 * h }; },

    // COLOUR / FILTER
    deep_fry: (p, c) => { const e = env(p, .03, .1);
      return mix(zoomTo(c, 1 + .09 * e * c.k, .3), shake(c.lt, .45 * e, 24), { sat: 1 + 2.8 * e * c.k, con: 1 + 1.1 * e * c.k, bri: 1 + .12 * e, hue: -12 * e, rgb: 3 * e,
        o: { grain: [.45 * e], emoji: [e], tint: [.28 * e, "#ff7a00", "overlay"] } }); },
    freeze_gray: (p, c) => { const e = env(p, .01, .04), h = pulseAt(c.lt, 0, 10);
      return mix(zoomTo(c, 1 + .07 * e * c.k, .3), { gray: e, sep: .3 * e, con: 1 + .15 * e, o: { flash: [.6 * h], cap: [e, back(c.lt / .3)] } }); },
    sad_mode: (p, c) => { const e = env(p, .25, .15);
      return mix(zoomTo(c, 1 + .08 * io(p) * e, .3), { gray: .75 * e, bri: 1 - .12 * e, o: { tint: [.5 * e, "#2a5cff", "soft-light"], vig: [.55 * e] } }); },
    rainbow_party: (p, c) => { const e = env(p, .05, .1);
      return mix(zoomTo(c, 1 + (.03 + .07 * Math.pow(Math.abs(Math.sin(Math.PI * c.lt * 2.2)), 4)) * e * c.k, .2), { hue: (c.lt * 400) % 360 * e, sat: 1 + .9 * e }); },
    flashbang: (p, c) => { const f = p < .06 ? eo(p / .06) : 1 - eo((p - .06) / .8);
      return { bri: 1 + 2 * f * c.k, blur: 8 * f, o: { flash: [f] } }; },
    horror_flicker: (p, c) => { const e = env(p, .1, .1), fl = hash(Math.floor(c.lt * 14) + 7) < .25 ? .25 : 1;
      return mix(zoomTo(c, 1 + .1 * io(p) * e, .3), { bri: lerp(1, .6 * fl, e), gray: .6 * e, con: 1 + .3 * e, o: { vig: [.8 * e], grain: [.35 * e] } }); },
    camera_flash: (p, c) => { const h = pulseAt(c.lt, 0, 6); return mix(zoomTo(c, 1 + .06 * h, .2), { gray: .4 * pulseAt(c.lt, 0, 3), o: { flash: [h] } }); },

    // GLITCH / RETRO
    vhs: (p, c) => { const e = env(p, .05, .05), band = hash(Math.floor(c.lt * 6) + 5) > .72 ? 12 : 2.5;
      return { sat: 1 + .25 * e, con: 1 - .05 * e, bri: 1 + .05 * e, rgb: (2.5 + 2 * Math.abs(jit(c.lt, 12, 2))) * e, warp: band * e, wf: [0, .06], wseed: Math.floor(c.lt * 12),
        s: 1 + .02 * e, o: { scan: [.4 * e, c.lt], grain: [.3 * e], osd: [e, "PLAY ▶"] } }; },
    glitch_hit: (p, c) => { const e = env(p, .02, .1), on = hash(Math.floor(c.lt * 16) + 9) > .3 ? 1 : .2;
      return { warp: 42 * on * e * c.k, wf: [0, .09], wseed: Math.floor(c.lt * 20), rgb: 14 * Math.abs(jit(c.lt, 16, 5)) * e * c.k,
        inv: hash(Math.floor(c.lt * 16) + 4) > .86 ? e : 0, hue: jit(c.lt, 16, 6) * 40 * e, px: jit(c.lt, 16, 7) * 1.5 * e, s: 1 + .04 * e }; },
    rgb_split_hit: (p, c) => { const h = pulseAt(c.lt, 0, 6) * (1 - eo((p - .9) / .1)); return mix(zoomTo(c, 1 + .06 * h, .2), { rgb: 18 * c.k * h }); },
    tv_off: (p, c) => { const a = eo(p / .4), b = eo((p - .4) / .3), g = p < .4 ? a : 1 - eo((p - .7) / .25);
      return { sqy: 1 - .9 * a, bri: 1 + 2 * a, o: { crt: [1 - a * .995, 1 - b * .995, g] } }; },

    // OVERLAY STYLE
    anime_speedlines: (p, c) => { const e = env(p, .04, .15);
      return mix(zoomTo(c, 1 + .25 * c.k * eo(p / .08) * e, .5), { sat: 1 + .3 * e, con: 1 + .1 * e, o: { lines: [.85 * e, 1] } }); },
    sus_red: (p, c) => { const e = env(p, .15, .12), pu = .5 + .5 * Math.sin(c.lt * 6);
      return mix(zoomTo(c, 1 + .18 * c.k * io(p / .9) * e, .5), { sat: 1 - .2 * e, o: { vig: [(.5 + .3 * pu) * e, "#c00000"], cap: [e, back(c.lt / .3)] } }); },
    red_alert: (p, c) => { const e = env(p, .03, .08), pu = Math.pow(.5 + .5 * Math.sin(c.lt * 2 * Math.PI * 2.5), 2);
      return mix(shake(c.lt, .5 * e, 20), { o: { flash: [.42 * pu * e, "#ff1010"] } }); },
    cinematic_bars: (p, c) => { const m = eo(p / .15) * (1 - io((p - .85) / .15));
      return mix(zoomTo(c, 1 + .08 * m, .3), { con: 1 + .12 * m, sat: 1 - .15 * m, o: { bars: [.12 * m], tint: [.25 * m, "#008c99", "soft-light"] } }); },
    spotlight: (p, c) => { const e = env(p, .12, .12); return mix(zoomTo(c, 1 + .08 * e, .2), { o: { spot: [.9 * e, 20] } }); },
    emotional_damage: (p, c) => { const e = env(p, .02, .1), h = pulseAt(c.lt, 0, 5);
      return mix(zoomTo(c, 1 + (.22 + .1 * h) * e * c.k, .6), shake(c.lt, 1.8 * h * c.k, 28, 1.5 * h), { sat: 1 + .4 * e, o: { tint: [(.25 + .35 * h) * e, "#ff2a2a", "multiply"], cap: [e, back(c.lt / .25)] } }); },
    thug_life: (p, c) => { const m = eo(p / .12) * (1 - io((p - .9) / .1));
      return mix(zoomTo(c, 1 + .3 * m * c.k, .6), { gray: m, con: 1 + .4 * m, o: { cap: [m, back((c.lt - .15) / .3)], vig: [.4 * m] } }); },
    dream_wavy: (p, c) => { const e = env(p, .2, .2);
      return { warp: 22 * e * (.6 + .4 * Math.sin(c.lt * 3)), wf: [.004, .01 + .002 * Math.sin(c.lt * 2)], wseed: 2, blur: 1.2 * e, bri: 1 + .12 * e, sat: 1 + .15 * e, s: 1 + .05 * e,
        o: { vig: [.55 * e, "#ffffff"] } }; },
  };
  function whip(p, c, dir) { const a = ei(p / .5), b = 1 - eo((p - .5) / .5), m = p < .5 ? a : b;
    return { px: (p < .5 ? dir : -dir) * 85 * m, blur: 26 * m, s: 1 + .05 * m }; }

  const DEFAULT_CAP = { freeze_gray: "Yup. That's me.", sus_red: "SUS", emotional_damage: "EMOTIONAL DAMAGE!", thug_life: "THUG LIFE" };
  const MUL = new Set(["s", "sqx", "sqy", "sat", "con", "bri"]);
  const ADD = new Set(["px", "py", "r", "skew", "blur", "hue", "gray", "sep", "inv", "rgb", "warp"]);
  const NEUTRAL = { s: 1, sqx: 1, sqy: 1, sat: 1, con: 1, bri: 1, px: 0, py: 0, r: 0, skew: 0, blur: 0, hue: 0, gray: 0, sep: 0, inv: 0, rgb: 0, warp: 0 };

  // ---------- per-target state: overlay layer + one SVG filter (displacement → RGB split) ----------
  let N = 0;
  const STYLE = `.cfx-layer{position:absolute;pointer-events:none;overflow:hidden;container-type:size}
.cfx-layer>*{position:absolute;inset:0;opacity:0}
.cfx-cap{inset:auto 0 9% 0!important;text-align:center;font:400 8.5cqw/1 "MK Archivo Black",Impact,"Arial Black",sans-serif;color:#fff;-webkit-text-stroke:.55cqw #000;paint-order:stroke fill;text-transform:uppercase;letter-spacing:.01em}
.cfx-osd{inset:6% auto auto 5%!important;font:700 4.6cqw/1 "Courier New",monospace;color:#fff;text-shadow:.3cqw .3cqw 0 #000a}
.cfx-emoji span{position:absolute;font-size:9cqw;line-height:1}
.cfx-bars i,.cfx-crt i{position:absolute;left:0;right:0;background:#000}
.cfx-crt b{position:absolute;left:0;right:0;top:50%;height:.6cqh;background:#fff;box-shadow:0 0 3cqw 1cqw #fff;transform:translateY(-50%)}`;
  function state(el) {
    if (el._cfx) return el._cfx;
    if (!document.getElementById("cfx-style")) { const s = document.createElement("style"); s.id = "cfx-style"; s.textContent = STYLE; document.head.appendChild(s); }
    const par = el.parentElement; if (getComputedStyle(par).position === "static") par.style.position = "relative";
    const layer = document.createElement("div"); layer.className = "cfx-layer";
    Object.assign(layer.style, el.offsetWidth ? { left: el.offsetLeft + "px", top: el.offsetTop + "px", width: el.offsetWidth + "px", height: el.offsetHeight + "px" } : { inset: 0 });
    layer.style.zIndex = el._cfxZ || 60;
    el.insertAdjacentElement("afterend", layer);
    const id = "cfx-f" + (++N), ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg"); svg.setAttribute("width", 0); svg.setAttribute("height", 0); svg.style.position = "absolute";
    svg.innerHTML = `<filter id="${id}" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
      <feTurbulence type="fractalNoise" baseFrequency="0 0.06" numOctaves="1" seed="1" result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="0" xChannelSelector="R" yChannelSelector="G" result="w"/>
      <feColorMatrix in="w" type="matrix" values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" result="r"/><feOffset in="r" dx="0" result="ro"/>
      <feColorMatrix in="w" type="matrix" values="0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0" result="g"/>
      <feColorMatrix in="w" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0" result="b"/><feOffset in="b" dx="0" result="bo"/>
      <feBlend in="ro" in2="g" mode="screen" result="rg"/><feBlend in="rg" in2="bo" mode="screen"/></filter>`;
    document.body.appendChild(svg);
    const f = svg.querySelector("filter");
    el._cfx = { el, layer, id, turb: f.querySelector("feTurbulence"), disp: f.querySelector("feDisplacementMap"), offs: f.querySelectorAll("feOffset"), svg };
    return el._cfx;
  }

  // ---------- overlays ----------
  const SPEED = (() => { let g = ""; for (let k = 0; k < 2; k++) { g += `<g class="g${k}">`; for (let i = 0; i < 70; i++) {
    const a = (i / 70) * Math.PI * 2 + hash(i + k * 99) * .08, w = .006 + hash(i * 3 + k) * .014, r0 = 7 + hash(i * 7 + k) * 9;
    const p = (ang, r) => `${50 + Math.cos(ang) * r},${50 + Math.sin(ang) * r}`;
    g += `<polygon points="${p(a - w, 75)} ${p(a + w, 75)} ${p(a, r0)}" fill="#fff"/>`; } g += "</g>"; } return g; })();
  const GRAIN = `url("data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5 0 0 0 0 .5 0 0 0 0 .5 0 0 0 1.4 -.2"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>')}")`;
  const EMOJI = ["😂", "💯", "👌", "🔥", "😳", "😂", "💯"];
  function ov(inst, name) {
    if (inst.ov[name]) return inst.ov[name];
    const e = document.createElement("div"); e.className = "cfx-" + name;
    if (name === "lines") { e.innerHTML = `<svg viewBox="0 0 100 100" preserveAspectRatio="none" style="width:100%;height:100%">${SPEED}</svg>`;
      Object.assign(e.style, { inset: "auto", width: "300%", height: "300%" }); }
    if (name === "scan") { e.style.background = "repeating-linear-gradient(0deg, rgba(0,0,0,.45) 0 2px, transparent 2px 4px)";
      e.innerHTML = `<i style="position:absolute;left:0;right:0;height:9%;background:linear-gradient(transparent,rgba(255,255,255,.18),transparent)"></i>`; }
    if (name === "grain") { e.style.backgroundImage = GRAIN; e.style.mixBlendMode = "overlay"; }
    if (name === "bars" || name === "crt") e.innerHTML = name === "bars" ? `<i style="top:0"></i><i style="bottom:0"></i>` : `<i style="top:0"></i><i style="bottom:0"></i><i style="left:0;right:auto;top:0;bottom:0"></i><i style="right:0;left:auto;top:0;bottom:0"></i><b></b>`;
    if (name === "emoji") e.innerHTML = EMOJI.map((m, i) => `<span style="left:${8 + hash(i * 5 + 1) * 78}%;top:${6 + hash(i * 11 + 2) * 72}%;transform:rotate(${(hash(i) - .5) * 50}deg)">${m}</span>`).join("");
    inst.st.layer.appendChild(e); inst.ov[name] = e; return e;
  }
  function overlay(inst, name, v, c) {
    const e = ov(inst, name), a = Array.isArray(v) ? v : [v], op = clamp(a[0]);
    e.style.opacity = op; if (op <= 0) return;
    if (name === "flash") e.style.background = a[1] || "#fff";
    else if (name === "vig") e.style.background = `radial-gradient(ellipse at ${c.x}% ${c.y}%, transparent ${a[2] ?? 32}%, ${a[1] || "#000"} 100%)`;
    else if (name === "spot") e.style.background = `radial-gradient(circle at ${c.x}% ${c.y}%, transparent ${a[1]}%, #000 ${a[1] + 14}%)`;
    else if (name === "tint") { e.style.background = a[1]; e.style.mixBlendMode = a[2] || "multiply"; }
    else if (name === "lines") { const k = Math.floor(c.lt * 14) % 2;
      e.style.left = `${c.x - 150}%`; e.style.top = `${c.y - 150}%`; e.style.transform = `rotate(${jit(c.lt, 14, 8) * 4}deg) scale(${a[1] || 1})`;
      e.querySelector(".g0").style.display = k ? "none" : ""; e.querySelector(".g1").style.display = k ? "" : "none"; }
    else if (name === "scan") e.firstChild.style.top = `${((a[1] || 0) * 35 % 120) - 10}%`;
    else if (name === "grain") e.style.backgroundPosition = `${Math.floor(hash(Math.floor(c.lt * 24)) * 220)}px ${Math.floor(hash(Math.floor(c.lt * 24) + 3) * 220)}px`;
    else if (name === "bars") e.querySelectorAll("i").forEach((b) => (b.style.height = a[0] * 100 + "%")), (e.style.opacity = 1);
    else if (name === "crt") { const [t, b, l, r] = e.querySelectorAll("i"), sy = a[0], sx = a[1];
      t.style.height = b.style.height = (1 - sy) * 50 + "%"; l.style.width = r.style.width = (1 - sx) * 50 + "%";
      e.querySelector("b").style.opacity = a[2]; e.querySelector("b").style.transform = `translateY(-50%) scaleX(${sx})`; e.style.opacity = 1; }
    else if (name === "cap") { e.textContent = c.cap; e.style.transform = `scale(${.4 + .6 * (a[1] ?? 1)})`; if (!c.cap) e.style.opacity = 0; }
    else if (name === "osd") e.textContent = Math.floor(c.lt * 2) % 2 ? a[1] : a[1].replace("▶", " ");
    else if (name === "emoji") e.querySelectorAll("span").forEach((s, i) => { s.style.scale = 1 + .15 * Math.sin(c.lt * 9 + i); });
  }

  // ---------- combine every active effect on a target and write transform + filter ----------
  function apply(st, list, t) {
    const acc = { ...NEUTRAL }; let ox = 50, oy = 50, zbest = 0, wf = [0, .06], wseed = 1, wbest = 0;
    for (const inst of list) {
      for (const k in inst.ov) inst.ov[k].style.opacity = 0;
      let p = (t - inst.t) / inst.d; if (p < 0 || (p > 1 && !inst.hold)) continue; p = clamp(p);
      const c = { lt: p * inst.d, d: inst.d, k: inst.k, x: inst.x, y: inst.y, cap: inst.cap };
      const r = FX[inst.fx](p, c) || {};
      for (const k in r) if (MUL.has(k)) acc[k] *= r[k]; else if (ADD.has(k)) acc[k] += r[k];
      if (r.s !== undefined && Math.abs(r.s - 1) >= zbest && r.ox !== undefined) { zbest = Math.abs(r.s - 1); ox = r.ox; oy = r.oy; }
      if (r.ox !== undefined && zbest === 0) { ox = r.ox; oy = r.oy; }
      if (r.warp && r.warp > wbest) { wbest = r.warp; wf = r.wf || wf; wseed = r.wseed ?? wseed; }
      if (r.o) for (const k in r.o) if (r.o[k]) overlay(inst, k, r.o[k], c);
    }
    const el = st.el, u = (el.offsetWidth || 1920) / 1920, A = acc;
    const moved = A.s !== 1 || A.sqx !== 1 || A.sqy !== 1 || A.px || A.py || A.r || A.skew;
    el.style.transformOrigin = `${ox}% ${oy}%`;
    el.style.transform = moved ? `translate(${A.px}%, ${A.py}%) rotate(${A.r}deg) skewX(${A.skew}deg) scale(${A.s * A.sqx}, ${A.s * A.sqy})` : "";
    const f = [];
    if (A.warp > .05 || A.rgb > .05) {
      st.turb.setAttribute("baseFrequency", `${wf[0]} ${wf[1]}`); st.turb.setAttribute("seed", wseed);
      st.disp.setAttribute("scale", A.warp * u); st.offs[0].setAttribute("dx", A.rgb * u); st.offs[1].setAttribute("dx", -A.rgb * u);
      f.push(`url(#${st.id})`);
    }
    if (A.blur > .02) f.push(`blur(${(A.blur * u).toFixed(2)}px)`);
    if (A.sat !== 1) f.push(`saturate(${A.sat.toFixed(3)})`);
    if (A.con !== 1) f.push(`contrast(${A.con.toFixed(3)})`);
    if (A.bri !== 1) f.push(`brightness(${A.bri.toFixed(3)})`);
    if (A.hue) f.push(`hue-rotate(${A.hue.toFixed(1)}deg)`);
    if (A.gray > .005) f.push(`grayscale(${clamp(A.gray)})`);
    if (A.sep > .005) f.push(`sepia(${clamp(A.sep)})`);
    if (A.inv > .005) f.push(`invert(${clamp(A.inv)})`);
    el.style.filter = f.join(" ");
  }

  function render(tl, t) {
    const by = new Map();
    for (const inst of tl._cfx.list) { if (!by.has(inst.st)) by.set(inst.st, []); by.get(inst.st).push(inst); }
    by.forEach((list, st) => apply(st, list, t));
  }

  window.CamFX = {
    FX, DEFAULT_CAP,
    // add one effect to a (paused) GSAP timeline; works with HyperFrames seeking
    add(tl, o) {
      const el = typeof o.target === "string" ? document.querySelector(o.target) : o.target;
      if (!el) { console.warn("CamFX: target not found", o.target); return tl; }
      if (!FX[o.fx]) { console.warn("CamFX: unknown effect", o.fx); return tl; }
      if (o.z) el._cfxZ = o.z;
      const st = state(el);
      const inst = { fx: o.fx, t: +o.t || 0, d: +o.d || 1.5, k: o.k ?? 1, x: o.x ?? 50, y: o.y ?? 45, hold: !!o.hold, st, ov: {},
        cap: o.cap ?? DEFAULT_CAP[o.fx] ?? "" };
      tl._cfx = tl._cfx || { list: [], driver: null, proxy: { v: 0 } };
      tl._cfx.list.push(inst);
      const end = Math.max(...tl._cfx.list.map((i) => i.t + i.d)) + .05;
      if (tl._cfx.driver) tl.remove(tl._cfx.driver);
      tl._cfx.driver = gsap.to(tl._cfx.proxy, { v: 1, duration: end, ease: "none", paused: true, onUpdate() { render(tl, this.time()); } });
      tl.add(tl._cfx.driver.paused(false), 0);
      return tl;
    },
    renderAt(tl, t) { if (tl._cfx) render(tl, t); },
    // remove all effects and overlays from a target (dashboard previews)
    clear(target) {
      const el = typeof target === "string" ? document.querySelector(target) : target; if (!el || !el._cfx) return;
      el._cfx.layer.remove(); el._cfx.svg.remove(); el.style.transform = el.style.filter = ""; delete el._cfx;
    },
  };
})();
