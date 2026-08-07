
---

## 1. Project Summary

A single-page, immersive 3D portfolio website built with React + Three.js (WebGPU renderer).  
The user **scrolls infinitely** to fly a camera around a circular diorama divided into **four seasonal scenes** (Winter → Spring → Summer → Fall → loops back).  
Small chibi-style papercraft characters walk, ride bikes, wave, and react to scroll activity along a separate circular path.  
An **Info/Credits panel** can be opened at any time, which shrinks and blurs the 3D view.

---

## 2. Tech Stack

| Library | Version | Role |
|---|---|---|
| React | ^19.2.0 | UI framework |
| React DOM | ^19.2.0 | DOM renderer |
| Three.js | ^0.182.0 | 3D engine (WebGPU renderer via `three/webgpu`) |
| @react-three/fiber | ^9.5.0 | React ↔ Three.js bridge (R3F) |
| @react-three/drei | ^10.7.7 | R3F helpers (PerspectiveCamera, useGLTF, useProgress…) |
| GSAP | ^3.14.2 | Animations (timelines, scroll triggers, mesh tweens) |
| @gsap/react | ^2.1.2 | `useGSAP` hook |
| Lenis | ^1.3.17 | Smooth infinite scroll (synced to GSAP ticker) |
| Zustand | ^5.0.11 | Global state management (4 stores) |
| Vite | ^7.3.1 | Build tool / dev server |

**Renderer note:** The Canvas uses `THREE.WebGPURenderer` (not the default WebGL renderer).  
`extend(THREE)` is called so all Three.js classes are available as JSX elements.

---

## 3. Directory Structure

```
amit/
├── public/
│   ├── basis/                  # KTX2 Basis transcoder (WASM + JS)
│   ├── fonts/                  # SlimeBox.woff / .woff2 (custom font)
│   ├── images/                 # Papercraft color swatches + character head PNGs (webp)
│   │   ├── red/green/blue/orange/white.webp  — loading screen quadrant textures
│   │   ├── head.webp           — loading bar character indicator (neutral)
│   │   └── head_smile.webp     — loading bar character indicator (hover smile)
│   ├── media/                  # Favicon set + OG image + webmanifest
│   ├── models/                 # Compressed .glb scene models (gltfjsx + draco)
│   │   ├── Scene_1_Winter-transformed.glb
│   │   ├── Scene_2_Spring-transformed.glb
│   │   ├── Scene_3_Summer-transformed.glb
│   │   ├── Scene_4_Fall-transformed.glb
│   │   ├── Moving_Characters-transformed.glb
│   │   └── moveee-transformed.glb   (unused/prototype)
│   └── textures/               # Baked scene textures as .webp
│       ├── Scene_1_Winter_1-4.webp
│       ├── Scene_2_Spring_1-4.webp
│       ├── Scene_3_Summer_1-4.webp
│       ├── Scene_4_Fall_1-3.webp
│       └── Moving_Characters_1.webp
├── src/
│   ├── main.jsx                # React entry point
│   ├── index.css               # Global styles + SlimeBox @font-face
│   ├── App.jsx                 # Root component — layout + info panel GSAP animation
│   ├── App.css                 # canvas { height/width: 100%; touch-action: none }
│   ├── store/                  # Zustand global stores (see §6)
│   ├── components/             # UI overlay components (see §7)
│   └── Experience/             # All 3D / Three.js code (see §8)
├── scripts/
│   └── process_models.js       # Node script — batch-processes raw GLBs
├── raw_assets/
│   └── moveee.glb              # Raw (unoptimised) GLB
├── Blender Files and Addon/    # Source .blend files + curve_to_points.py Blender addon
├── vite.config.js              # Vite config — only @vitejs/plugin-react
├── package-lock.json
└── README.md
```

---

## 4. Entry & Boot Sequence

```
index.html → src/main.jsx
  → <App />
      → <LoadingScreen />       renders instantly (z-index: huge), blocks interaction
      → <Experience />          mounts Canvas + ReactLenis + Scene (lazy via Suspense)
      → <InfoPanel />           hidden until Info button clicked
      → <InfoButton />          top-right fixed button
      → <ZoomSlider />          bottom-center fixed slider
      → <Border />              decorative dashed border overlay
```

**Loading flow:**
1. `@react-three/drei`'s `useProgress` tracks asset loading progress.
2. `LoadingScreen` shows a progress bar with a character indicator head.
3. When `progress === 100`, an **"Enter!"** button appears.
4. Clicking "Enter!" triggers a GSAP animation that flies all four quadrants off-screen.
5. `setIsExperienceReady(true)` is called → Lenis scroll is enabled.
6. Inside the `<Scene>`, a `<SceneReadySentinel>` component calls `setIsSceneReady(true)` once mounted.

---

## 5. Scroll System

- **Lenis** (`lenis/react`) provides smooth infinite scroll (`infinite: true`).
- Lenis is **manually ticked** by GSAP's ticker (`gsap.ticker.add(update)`) to keep them in sync.
- On each Lenis scroll event, `e.progress` (0–1, loops infinitely) is written to `useCurveProgressStore.scrollProgress`.
- `ScrollTrigger.update()` is also called on each scroll event.
- Lenis is **stopped** while `isInfoPanelOpen === true` or while `isExperienceReady === false`.

---

## 6. State Stores (Zustand)

### `useExperienceStore` — `src/store/useExperienceStore.js`
| State | Type | Purpose |
|---|---|---|
| `isExperienceReady` | boolean | True after user clicks "Enter!" |
| `isSceneReady` | boolean | True after Scene's Suspense resolves |
| `isInfoPanelOpen` | boolean | Toggles Info/Credits panel |
| `setIsExperienceReady(bool)` | fn | Called by LoadingScreen |
| `setIsSceneReady(bool)` | fn | Called by SceneReadySentinel |
| `setIsInfoPanelOpen(bool)` | fn | Called by InfoButton |

### `useCurveProgressStore` — `src/store/useCurveProgressStore.js`
| State | Type | Purpose |
|---|---|---|
| `curves` | object | Pre-built CatmullRom curves (created once at module load) |
| `scrollProgress` | number 0–1 | Current scroll position on curves |
| `setScrollProgress(value)` | fn | Called every scroll frame by Lenis |

The `curves` object keys:
- `cameraPathCurve` — desktop camera position path
- `cameraLookAtCurve` — desktop camera look-at path
- `mobileCameraPathCurve` — mobile camera position path
- `mobileCameraLookAtCurve` — mobile camera look-at path
- `movingCharactersCurve` — path characters walk along (desktop)
- `mobileMovingCharactersCurve` — same for mobile

### `useCameraStore` — `src/store/useCameraStore.js`
| State | Type | Purpose |
|---|---|---|
| `zoom` | number (1–3) | Camera orthographic zoom controlled by ZoomSlider |
| `setZoom(zoom)` | fn | Called by ZoomSlider on change |

### `useResponsiveStore` — `src/store/useResponsiveStore.js`
| State | Type | Purpose |
|---|---|---|
| `isMobile` | boolean | `window.innerWidth < 764` |

Updated via a `window.resize` event listener attached at module load time. Breakpoint: **764px**.

---

## 7. UI Components

### `src/components/LoadingScreen/`
- **File:** `LoadingScreen.jsx` + `LoadingScreen.css`
- Full-screen overlay, `z-index: 99999999999999`.
- Four `.quadrant` divs (TL, TR, BL, BR) each with a papercraft paper texture background and an SVG `filter id="torn"` (fractal noise displacement) for a torn-paper edge.
- Loading bar: `.loading-bar-fill` width = `maxProgress%` with a `.loading-bar-indicator` character head at the tip.
- Images are preloaded via hidden 0×0 divs (the author's own words: "Lol don't do this this is cringe").
- A credits GitHub link and "Swipe/Scroll to navigate" hint are shown during loading.
- On "Enter!" click: four quadrants fly to their respective corners via GSAP, `setIsExperienceReady(true)` fires.

### `src/components/Border/`
- **File:** `Border.jsx` + `Border.css`
- Single `<div class="full-page-border">` — `position: fixed; inset: 0`.
- `border: 4px dashed #e5e5e5` with a radial gradient vignette.
- `pointer-events: none`, `z-index: 9999`.
- Scaled/rounded by App.jsx GSAP animation when InfoPanel opens.

### `src/components/ZoomSlider/`
- **File:** `ZoomSlider.jsx` + `ZoomSlider.css`
- Fixed bottom-center, `z-index: 9999999`.
- `<input type="range" min=1 max=3 step=0.01>` → calls `useCameraStore.setZoom`.
- Flanked by minus/plus SVG icons.
- Fades out (`opacity: 0`, `pointerEvents: none`) when InfoPanel opens.

### `src/components/Buttons/InfoButton/`
- **File:** `InfoButton.jsx` + `InfoButton.css`
- Fixed top-right (`right: 60px; top: 60px`), `z-index: 3`.
- Toggles `isInfoPanelOpen`. Label: **"Info"** / **"Close"**.
- Hover: dashed white border.
- Mobile: shifts to `right: 20px; top: 28px`.

### `src/components/InfoPanel/`
- **File:** `InfoPanel.jsx` + `InfoPanel.css`
- Full-screen `position: fixed` div.
- Background image swaps based on current season (detected from `scrollProgress`):
  - Winter (0–0.235): `/images/blue.webp`
  - Spring (0.235–0.49): `/images/green.webp`
  - Summer (0.49–0.74): `/images/orange.webp`
  - Fall (0.74–1): `/images/red.webp`
- `.info-box` positioned `right: 5%; top: 35%` (desktop) — white text with credits, Codrops link, YouTube link, GitHub link.
- Responsive breakpoints: 1300px, 1250px, 764px (mobile: centered at bottom).

---

## 8. Experience (3D Scene)

### `src/Experience/Experience.jsx`
The 3D root. Wraps everything in `<ReactLenis root>` + `<Canvas>`.

**Canvas setup:**
- `id="canvas-container"`, `position: fixed; top: 0; left: 0`.
- `flat` prop (no tone mapping).
- Custom `gl` factory uses `THREE.WebGPURenderer` with `logarithmicDepthBuffer: true`.
- Background color: `#111111` (very dark grey).
- A `<div id="dummy-scroll-div" style="height: 1000vh">` provides the scrollable height for Lenis.

---

### `src/Experience/Scene.jsx`
Renders all 3D objects inside the Canvas:
```
<Scene>
  <CustomCamera />
  <Suspense fallback={null}>
    <MovingCharacters />
    <Winter />
    <Spring />
    <Summer />
    <Fall />
    <SceneReadySentinel />   ← fires setIsSceneReady(true) on mount
  </Suspense>
</Scene>
```

---

### `src/Experience/components/CustomCamera.jsx`
Manages a `<PerspectiveCamera makeDefault fov={50}>` nested inside a `<group ref={cameraGroupRef}>`.

**Per-frame logic (`useFrame`):**
1. Reads `scrollProgress` directly from the store (not via subscription, to avoid re-renders).
2. Samples `cameraPathCurve.getPointAt(scrollProgress)` → `targetPosition`.
3. Samples `cameraLookAtCurve.getPointAt(scrollProgress)` → `targetLookAt`.
4. On first frame: hard-copies position (no lerp). Every subsequent frame: `position.lerp(target, 0.1)`, `lookAt.lerp(target, 0.1)`.
5. **Mouse parallax (desktop only):** `cameraRef.current.position` and `rotation` are offset by `pointer * 0.1` (lerped at 0.1). On mobile: fixed offset `x=0.3, y=0`.
6. **Zoom:** reads `useCameraStore.zoom` and applies it to `cameraRef.current.zoom`, calling `updateProjectionMatrix()`.
7. Pauses all camera movement while `isInfoPanelOpen === true`.

---

### `src/Experience/components/Curves.js`
Defines all CatmullRom splines as raw `THREE.Vector3` point arrays.

**`exportedCurves` array** — each entry has:
- `name` — key used in the curves object
- `closed: true` — all curves loop
- `startIndex` — rotates the point array so the start of the curve aligns with the desired scene start
- `points` — `THREE.Vector3[]`

**`createCurves()`** — iterates `exportedCurves`, applies `startIndex` rotation, constructs `THREE.CatmullRomCurve3` for each, and returns a named object. Called once at store init.

---

### `src/Experience/components/AnimateMesh.jsx`
A reusable wrapper component that sine-animates any mesh property per frame.

**Props:**
| Prop | Default | Description |
|---|---|---|
| `children` | — | Mesh(es) to animate |
| `animations` | — | Array of animation descriptors (overrides single-prop mode) |
| `property` | `"rotation"` | Object3D property to animate |
| `axis` | `"y"` | Axis on that property |
| `speed` | `1` | Sine frequency multiplier |
| `amplitude` | `0.3` | Sine amplitude |
| `offset` | `0` | Sine phase offset |
| `base` | `0` | Resting value added to sine output |
| `position` | — | Position of the wrapper group |

Formula: `ref.current[property][axis] = base + amplitude * Math.sin(clock.elapsedTime * speed + offset)`

---

### `src/Experience/utils/ktxLoader.jsx`
Custom hook `useKTX2Texture(url, options)` that:
- Detects `.ktx2` extension to choose between `KTX2Loader` and `THREE.TextureLoader`.
- Sets transcoder path to `/basis/` for KTX2.
- Returns a `THREE.MeshBasicMaterial` with `colorSpace: SRGBColorSpace`, `flipY: false`, configurable `transparent`, `alphaTest`, and `side`.
- Also exposes `useKTX2Texture.preload(url)` for preloading.

---

## 9. Scene Models

All models are auto-generated by **gltfjsx** and use baked textures (no realtime lighting). Materials are all `MeshBasicMaterial` via `useKTX2Texture`.

### Scene_1_Winter (`Scene_1_Winter.jsx`)
- **GLB:** `/models/Scene_1_Winter-transformed.glb`
- **Textures:** `Scene_1_Winter_1-4.webp`
- **Animated parts (AnimateMesh):**
  - Deer head — z-axis tilt, amplitude 0.2, speed 1.5
  - Notes 1, 2, 3 — gentle z-axis wobble (slightly different speeds/offsets)
  - Snowman arms (left and right) — x-axis swing, amplitude 0.5, speed 2
- **Animated parts (useFrame):**
  - Fire (Inner, Center, Outer) — random snap rotation (not smooth), frequency ~2.2 Hz using hash-based random angle

### Scene_2_Spring (`Scene_2_Spring.jsx`)
- **GLB:** `/models/Scene_2_Spring-transformed.glb`
- **Textures:** `Scene_2_Spring_1-4.webp`
- Uses `side: "double"` on all textures (paper seen from both sides).
- Has animated **gate** meshes that respond to scroll direction (open/close via `useFrame` + GSAP).

### Scene_3_Summer (`Scene_3_Summer.jsx`)
- **GLB:** `/models/Scene_3_Summer-transformed.glb`
- **Textures:** `Scene_3_Summer_1-4.webp`
- Contains **interactive signs** (Starbucks, Blender, Figma, Psychiatrist):
  - `onPointerEnter` → sign floats up `+FLOAT_AMOUNT` via GSAP
  - `onPointerLeave` → sign returns to base Y
  - Changes `document.body.style.cursor` to `"pointer"` on hover

### Scene_4_Fall (`Scene_4_Fall.jsx`)
- **GLB:** `/models/Scene_4_Fall-transformed.glb`
- **Textures:** `Scene_4_Fall_1-3.webp`
- Has animated arms/limbs via `AnimateMesh`.

---

## 10. Moving Characters (`Moving_Characters.jsx`)

The most complex file (~700 lines). All season characters share one GLB.

- **GLB:** `/models/Moving_Characters-transformed.glb`
- **Texture:** `/textures/Moving_Characters_1.webp` (`side: "double"`)

### Characters & visibility ranges (scroll 0–1)
| Character ref | Season | Visible range |
|---|---|---|
| `winterFrontCharacterRef` | Winter | 0.02 – 0.235 |
| `winterSideCharacterRef` | Winter | 0.02 – 0.235 |
| `springFrontCharacterRef` | Spring | 0.235 – 0.49 |
| `springSideCharacterRef` | Spring | 0.235 – 0.49 |
| `summerFrontCharacterRef` | Summer | 0.49 – 0.74 |
| `summerWaveRef` | Summer | 0.49 – 0.74 |
| `fallFrontCharacterRef` | Fall | 0.74 – 0.99 |

### Per-frame logic (`moveObjectOrCharacter`)
1. Checks if `scrollProgress` is inside the character's range.
2. If visibility changed: GSAP tweens `innerWrapper.position.y` to `0.23` (appear) or `-5` (hide below ground).
3. Samples `movingCharactersCurve.getPointAt(curveValue)` for position.
4. Uses curve tangent + up vector cross product for facing direction.
5. Lerps position at `0.1` per frame (hard-copies on loop-wrap detected by `abs(diff) > 0.5`).

### Character swap animations
- **Winter & Spring** have **front-facing** (idle) and **side-facing** (walking) versions.
- When scrolling starts → side character drops in, front character drops out (GSAP `back.in/out`).
- After 3 seconds of no scrolling → front character returns.
- `winterSideFaceRef` / `springSideFaceRef` visibility toggles so face changes to smile while scrolling.

### Limb animations
- **Winter walking:** arms and feet swing via `Math.sin(scrollProgress * 100) * 0.7` applied to `rotation.z`.
- **Spring bike wheels:** `rotation.z = baseRotation - scrollProgress * 205`.

---

## 11. App-level GSAP Animation (App.jsx)

When `isInfoPanelOpen` changes, a GSAP timeline shrinks the 3D scene to make room for the info panel:

**Desktop:**
- `#canvas-container` → `scale: 0.6`, `borderRadius: 32px`, `transformOrigin: "20px center"` (slides left)
- `.full-page-border` → same transform
- `.zoom-slider-wrapper` → `scale: 0.6`, `opacity: 0`, `pointerEvents: none`

**Mobile:**
- `#canvas-container` → `scale: 0.4`, `transformOrigin: "center 160px"` (slides up)
- `.zoom-slider-wrapper` → `opacity: 0` only

Timeline is rebuilt when `isMobile` changes (responsive). `tlRef.current.play()` / `.reverse()` on panel open/close.

---

## 12. Public Assets Reference

### Fonts
| File | Usage |
|---|---|
| `/fonts/SlimeBox.woff2` | Primary site font (all text) |
| `/fonts/SlimeBox.woff` | Fallback |

### Images (`/images/`)
| File | Usage |
|---|---|
| `red.webp` | Loading screen BL quadrant; Info panel Fall BG |
| `green.webp` | Loading screen TR quadrant; Info panel Spring BG |
| `blue.webp` | Loading screen TL quadrant; Info panel Winter BG |
| `orange.webp` | Loading screen BR quadrant; Info panel Summer BG |
| `white.webp` | Loading bar fill texture |
| `head.webp` | Loading bar character indicator (neutral) |
| `head_smile.webp` | Loading bar character indicator (hover) |
| `Scene_1-4_*.ktx2` | KTX2 compressed scene textures (GPU-native) |
| `Moving_Characters_1.ktx2` | KTX2 compressed character texture |

### Models (`/models/`)
All GLBs are Draco-compressed via `gltfjsx`:
- `Scene_1_Winter-transformed.glb` (225KB, originally 2.79MB)
- `Scene_2_Spring-transformed.glb` (392KB, originally 1.47MB)
- `Scene_3_Summer-transformed.glb` (417KB, originally 4.09MB)
- `Scene_4_Fall-transformed.glb` (133KB, originally 2.05MB)
- `Moving_Characters-transformed.glb` (121KB, originally 1.03MB)
- `moveee-transformed.glb` (132KB) — unused prototype, not rendered in Scene.jsx

---

## 13. Known Issues / TODOs (from README)

- Loading screen is buggy (vibe coded).
- Major responsive issues on mobile.
- No hover interactions yet (mentioned as future).
- Paper shape-key animations not implemented.
- TSL (Three.js Shading Language) shaders considered for paper color change.
- Butterfly on string has no physics.
- `Moving_Characters.jsx` is bloated (~700 lines, self-described).

---

## 14. Development Commands

```bash
# Install dependencies
npm install

# Start dev server (Vite, default http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

---

## 15. Key Patterns & Conventions

- **No route system** — single page only.
- **Zustand stores** use direct `getState()` reads inside `useFrame` loops to avoid React re-render overhead.
- All **textures are baked** (Blender → KTX2/webp). No realtime lighting in Three.js.
- **KTX2 format** with Basis transcoder for GPU-native compressed textures (best performance).
- `AnimateMesh` is the reusable animation primitive — use it instead of inline `useFrame` for simple sinusoidal motion.
- `isMobile` breakpoint is **764px** (not the common 768px).
- The `movingCharactersCurve` and `cameraPathCurve` are separate closed loops — characters travel a wider circle, camera travels a tighter path closer to the scenes.
- Curve `startIndex` in `Curves.js` is the main knob to shift where "scroll 0%" points in the world.
- **GSAP `overwrite: "auto"`** is used on character visibility tweens to prevent animation stacking on rapid scroll.
