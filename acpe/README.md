# ACPE — Adaptive Color Palette Engine

ACPE is an experimental web tool that generates adaptive UI color palettes
based on image scene analysis.

The main idea is to reduce eye strain and improve long-session UX
by keeping color harmony consistent with scene brightness,
saturation, and temperature.

This project was built as a focused MVP to explore how color intelligence
can be integrated into real-world tools such as annotation platforms,
AI dashboards, and enterprise software.

---

## Features

- Image-based scene analysis (brightness, saturation, warmth)
- Adaptive “Rainbow + Pink” palette generation
- Chroma control: Low / Medium / High
- Temperature control: Cool / Neutral / Warm
- Bounding box overlay with perceptual transparency
- UI preview with design roles (background, surface, text, primary, accent)
- Export to `tokens.json`
- Export CSS variables for easy integration

---

## Tech Stack

- Vue 3 (Composition API)
- Vite
- HTML Canvas
- Pure JavaScript color math (no heavy libraries)

---

## How it works

1. Upload an image
2. ACPE analyzes global scene properties
3. Fixed hue anchors are adapted to the scene context
4. The resulting palette remains visually balanced and UI-friendly

The generated colors are designed to be usable in professional software
without overwhelming the user or causing visual fatigue.

---

## Run locally

```bash
npm install
npm run dev

