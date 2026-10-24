// MemeKit for Three.js scenes inside HyperFrames: meme faces that follow a character's head (face-swap) and billboard screens.
// entries = kit.face_entry(...) dicts from memekit.py. anchors = { name: [x,y,z] | (t) => [x,y,z] }.
//   import { memeClips3D } from "./assets/memekit/hyperframes/memekit3d.js";
//   const memes = memeClips3D(THREE, scene, camera, window.MEMEKIT_3D, anchors);
//   in your hf-seek render(t): ...update scene...; memes.update(t); renderer.render(scene, camera);
export function memeClips3D(THREE, scene, camera, entries = [], anchors = {}) {
  const loader = new THREE.TextureLoader();
  const list = entries.map((f) => {
    const tex = loader.load(f.src); tex.colorSpace = THREE.SRGBColorSpace; tex.repeat.set(1 / f.cols, 1 / f.rows);
    const w = f.size, h = f.kind === "face" ? f.size : f.size * f.ar;
    const g = new THREE.Group();
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: f.kind !== "face", toneMapped: false }));
    m.renderOrder = 10; g.add(m);
    if (f.kind === "tv") { const fr = new THREE.Mesh(new THREE.PlaneGeometry(w * 1.08, h * 1.1), new THREE.MeshBasicMaterial({ color: 0x1d2030 })); fr.position.z = -0.02; g.add(fr); }
    g.visible = false; scene.add(g); return { f, g, tex };
  });
  const backOut = (x) => 1 + 2.70158 * Math.pow(x - 1, 3) + 1.70158 * Math.pow(x - 1, 2);
  return {
    update(t) {
      camera.updateMatrixWorld();
      for (const { f, g, tex } of list) {
        const u = t - f.t; g.visible = u >= 0 && u < f.d; if (!g.visible) continue;
        const a = anchors[f.anchor]; const p = typeof a === "function" ? a(t) : a; if (!p) { g.visible = false; continue; }
        g.position.set(p[0], p[1] + f.dy, p[2]); g.quaternion.copy(camera.quaternion);
        g.scale.setScalar(Math.max(0.001, backOut(Math.min(1, u / 0.3)) * Math.min(1, (f.d - u) / 0.2)));
        const k = Math.floor(u * f.fps) % f.n; tex.offset.set((k % f.cols) / f.cols, 1 - (Math.floor(k / f.cols) + 1) / f.rows);
      }
    },
  };
}
