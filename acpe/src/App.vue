<template>
  <div class="app">
    <h1>ACPE — Adaptive Color Palette Engine</h1>

    <input type="file" accept="image/*" @change="onImageUpload" />

    <div v-if="imageLoaded" class="row">
      <!-- Image + actions -->
      <div class="panel">
        <div class="label">Downscaled image (for analysis)</div>
        <canvas ref="canvas"></canvas>

        <div class="btnRow">
          <button class="btn" @click="analyzeCanvas">Analyze</button>

          <button class="btn" :disabled="!analyzed" @click="generatePalette">
            Generate palette
          </button>

          <button class="btn" :disabled="!analyzed" @click="toggleBox">
            Toggle selection
          </button>
        </div>

        <div class="small" v-if="lastError">⚠️ {{ lastError }}</div>

        <div class="small" v-if="analyzed">
          Overlay uses <b>{{ overlayColorName }}</b> (fill + stroke)
        </div>
      </div>

      <!-- Controls -->
      <div class="panel" v-if="analyzed">
        <div class="label">Controls</div>

        <div class="control">
          <div class="controlTitle">Chroma</div>
          <div class="seg">
            <button class="segBtn" :class="{ on: chroma==='low' }" @click="setChroma('low')">Low</button>
            <button class="segBtn" :class="{ on: chroma==='medium' }" @click="setChroma('medium')">Medium</button>
            <button class="segBtn" :class="{ on: chroma==='high' }" @click="setChroma('high')">High</button>
          </div>
        </div>

        <div class="control">
          <div class="controlTitle">Temperature</div>
          <div class="seg">
            <button class="segBtn" :class="{ on: temp==='cool' }" @click="setTemp('cool')">Cool</button>
            <button class="segBtn" :class="{ on: temp==='neutral' }" @click="setTemp('neutral')">Neutral</button>
            <button class="segBtn" :class="{ on: temp==='warm' }" @click="setTemp('warm')">Warm</button>
          </div>
        </div>

        <div class="label" style="margin-top:12px;">Scene stats (debug)</div>
        <div class="stat"><b>Mean brightness:</b> {{ stats.meanLuma.toFixed(3) }}</div>
        <div class="stat"><b>Mean saturation-ish:</b> {{ stats.meanSat.toFixed(3) }}</div>
        <div class="stat"><b>Warmth-ish:</b> {{ stats.warmth.toFixed(3) }}</div>

        <div class="label" style="margin-top:12px;">Generation (debug)</div>
        <div class="stat"><b>baseS (HSL saturation):</b> {{ gen.baseS.toFixed(3) }}</div>
        <div class="stat"><b>baseL (HSL lightness):</b> {{ gen.baseL.toFixed(3) }}</div>
        <div class="stat"><b>hueShift:</b> {{ gen.hueShift.toFixed(1) }}°</div>

        <div class="hint">
          High теперь гарантированно меняет базовую насыщенность, поэтому HEX будет меняться.
        </div>

        <div class="btnRow" style="margin-top:12px;">
          <button class="btn" :disabled="!roles.ready" @click="downloadTokens">
            Export tokens.json
          </button>
          <button class="btn" :disabled="!roles.ready" @click="copyCssVars">
            Copy CSS variables
          </button>
        </div>

        <div class="small" v-if="exportMsg">{{ exportMsg }}</div>
      </div>

      <!-- Palette -->
      <div class="panel wide" v-if="palette.length">
        <div class="label">Rainbow + Pink (adaptive) — click to set overlay color</div>

        <div class="swatches">
          <div
            v-for="c in palette"
            :key="c.name"
            class="swatch"
            :style="{ background: c.hex, color: pickTextColor(c.hex) }"
            @click="setOverlayColor(c.name)"
          >
            <div class="swName">{{ c.name }}</div>
            <div class="swHex">{{ c.hex }}</div>
          </div>
        </div>
      </div>

      <!-- UI Preview -->
      <div class="panel wide" v-if="roles.ready">
        <div class="label">UI Preview (roles)</div>

        <div class="previewGrid" :style="previewStyle">
          <div class="card">
            <div class="cardTitle">Project Card</div>
            <div class="cardText">
              background / surface / text / primary / accent
            </div>
            <div class="cardRow">
              <button class="primaryBtn">Primary</button>
              <button class="ghostBtn">Secondary</button>
              <span class="pill">Accent</span>
            </div>
          </div>

          <div class="card">
            <div class="cardTitle">Table</div>
            <div class="table">
              <div class="tr th">
                <div>ID</div><div>Name</div><div>Status</div>
              </div>
              <div class="tr">
                <div>#102</div><div>Labeling</div><div><span class="pill">Active</span></div>
              </div>
              <div class="tr">
                <div>#103</div><div>Review</div><div><span class="pill">Pending</span></div>
              </div>
              <div class="tr">
                <div>#104</div><div>Export</div><div><span class="pill">Done</span></div>
              </div>
            </div>
          </div>
        </div>

        <div class="small">
          Если preview комфортный и читаемый — это уже “продуктовый” результат.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick } from 'vue'

/** --- state --- **/
const canvas = ref(null)
const imageLoaded = ref(false)
const analyzed = ref(false)
const lastError = ref('')
const palette = ref([])

const stats = reactive({ meanLuma: 0, meanSat: 0, warmth: 0 })

const boxSelected = ref(false)
const overlayColorName = ref('Cyan')
const lastImageData = ref(null)

/** Day-2 controls **/
const chroma = ref('medium') // low | medium | high
const temp = ref('neutral')  // cool | neutral | warm

/** debug for generation **/
const gen = reactive({ baseS: 0, baseL: 0, hueShift: 0 })

/** Roles for UI preview **/
const roles = reactive({
  ready: false,
  background: '#ffffff',
  surface: '#f5f5f5',
  text: '#111111',
  primary: '#3b82f6',
  accent: '#ec4899'
})

const exportMsg = ref('')

/** --- utils --- **/
function clamp01(x) { return Math.max(0, Math.min(1, x)) }
function luma01(r, g, b) { return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 }
function saturation01(r, g, b) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b)
  if (mx === 0) return 0
  return (mx - mn) / mx
}
function warmth01(r, g, b) {
  const denom = Math.max(30, r + g + b)
  return (r - b) / denom
}
function rgbToHex(r, g, b) {
  const toHex = (v) => v.toString(16).padStart(2, '0')
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}
function pickTextColor(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return luma01(r, g, b) > 0.55 ? '#111' : '#fff'
}
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

/** --- upload --- **/
async function onImageUpload(event) {
  analyzed.value = false
  palette.value = []
  roles.ready = false
  lastError.value = ''
  exportMsg.value = ''
  boxSelected.value = false
  overlayColorName.value = 'Cyan'

  const file = event.target.files?.[0]
  if (!file) return

  const img = new Image()
  img.onload = async () => {
    imageLoaded.value = true
    await nextTick()

    const c = canvas.value
    const ctx = c?.getContext('2d')
    if (!c || !ctx) {
      lastError.value = 'Canvas not available'
      return
    }

    const size = 260
    c.width = size
    c.height = size
    ctx.clearRect(0, 0, size, size)
    ctx.drawImage(img, 0, 0, size, size)

    lastImageData.value = ctx.getImageData(0, 0, c.width, c.height)
  }
  img.onerror = () => (lastError.value = 'Failed to load image')
  img.src = URL.createObjectURL(file)
}

/** --- analysis --- **/
function analyzeCanvas() {
  lastError.value = ''
  exportMsg.value = ''

  const c = canvas.value
  const ctx = c?.getContext('2d', { willReadFrequently: true })
  if (!c || !ctx) {
    lastError.value = 'Canvas not ready'
    return
  }

  const data = ctx.getImageData(0, 0, c.width, c.height).data

  let sumL = 0, sumS = 0, sumW = 0, n = 0
  const step = 4 * 2
  for (let i = 0; i < data.length; i += step) {
    const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3]
    if (a < 10) continue
    sumL += luma01(r, g, b)
    sumS += saturation01(r, g, b)
    sumW += warmth01(r, g, b)
    n++
  }

  if (!n) { lastError.value = 'No pixels sampled'; return }

  stats.meanLuma = clamp01(sumL / n)
  stats.meanSat = clamp01(sumS / n)
  stats.warmth = Math.max(-1, Math.min(1, sumW / n))

  analyzed.value = true
}

/** --- controls --- **/
function setChroma(v) {
  chroma.value = v
  // regenerate if analysis exists (not only when palette exists)
  if (analyzed.value) generatePalette()
}
function setTemp(v) {
  temp.value = v
  if (analyzed.value) generatePalette()
}

/** --- palette --- **/
function hslToRgb(h, s, l) {
  const C = (1 - Math.abs(2 * l - 1)) * s
  const Hp = (h % 360) / 60
  const X = C * (1 - Math.abs((Hp % 2) - 1))
  let r1 = 0, g1 = 0, b1 = 0
  if (0 <= Hp && Hp < 1) [r1, g1, b1] = [C, X, 0]
  else if (1 <= Hp && Hp < 2) [r1, g1, b1] = [X, C, 0]
  else if (2 <= Hp && Hp < 3) [r1, g1, b1] = [0, C, X]
  else if (3 <= Hp && Hp < 4) [r1, g1, b1] = [0, X, C]
  else if (4 <= Hp && Hp < 5) [r1, g1, b1] = [X, 0, C]
  else if (5 <= Hp && Hp < 6) [r1, g1, b1] = [C, 0, X]
  const m = l - C / 2
  return { r: Math.round((r1 + m) * 255), g: Math.round((g1 + m) * 255), b: Math.round((b1 + m) * 255) }
}

function generatePalette() {
  if (!analyzed.value) return

  const anchors = [
    { name: 'Red', hue: 10 },
    { name: 'Orange', hue: 28 },
    { name: 'Yellow', hue: 50 },
    { name: 'Green', hue: 120 },
    { name: 'Cyan', hue: 190 },
    { name: 'Blue', hue: 220 },
    { name: 'Violet', hue: 275 },
    { name: 'Pink', hue: 325 }
  ]

  // Lightness: follow scene but keep usable range
  const baseL = clamp01(Math.max(0.35, Math.min(0.78, stats.meanLuma)))

  // Saturation: make Low/Medium/High VISIBLY different
  let satBase = stats.meanSat * 3.0

  if (chroma.value === 'low') {
    satBase *= 0.70
  } else if (chroma.value === 'high') {
    // guarantee visible change in HEX even if meanSat is small
    satBase = Math.max(satBase * 1.75, 0.28)
  } // medium = as-is

  const baseS = clamp01(Math.min(0.70, Math.max(0.10, satBase)))

  // Temperature: add fixed shift + scene warmth
  const tempShift = temp.value === 'warm' ? 8 : temp.value === 'cool' ? -8 : 0
  const hueShift = Math.max(-12, Math.min(12, stats.warmth * 40)) + tempShift

  // save debug
  gen.baseS = baseS
  gen.baseL = baseL
  gen.hueShift = hueShift

  palette.value = anchors.map((a) => {
    const h = (a.hue + hueShift + 360) % 360
    const { r, g, b } = hslToRgb(h, baseS, baseL)
    return { name: a.name, hex: rgbToHex(r, g, b) }
  })

  computeRoles()
  drawOverlayBox()
}

/** --- roles --- **/
function computeRoles() {
  const bg = '#ffffff'
  const surface = stats.meanLuma > 0.55 ? '#f6f6f6' : '#1b1b1b'
  const text = stats.meanLuma > 0.55 ? '#111111' : '#f5f5f5'

  const cyan = palette.value.find(p => p.name === 'Cyan')?.hex || '#b8cfd5'
  const pink = palette.value.find(p => p.name === 'Pink')?.hex || '#d5b8c8'

  roles.background = bg
  roles.surface = surface
  roles.text = text
  roles.primary = cyan
  roles.accent = pink
  roles.ready = true
}

const previewStyle = computed(() => ({
  '--bg': roles.background,
  '--surface': roles.surface,
  '--text': roles.text,
  '--primary': roles.primary,
  '--accent': roles.accent
}))

/** --- overlay box --- **/
function restoreBaseImage(ctx) {
  if (lastImageData.value) ctx.putImageData(lastImageData.value, 0, 0)
}
function getOverlayHex() {
  return palette.value.find((p) => p.name === overlayColorName.value)?.hex || '#b8cfd5'
}
function setOverlayColor(name) {
  overlayColorName.value = name
  drawOverlayBox()
}
function toggleBox() {
  boxSelected.value = !boxSelected.value
  drawOverlayBox()
}
function drawOverlayBox() {
  const c = canvas.value
  const ctx = c?.getContext('2d')
  if (!c || !ctx) return

  restoreBaseImage(ctx)

  const hex = getOverlayHex()
  const fillAlpha = boxSelected.value
    ? (stats.meanLuma < 0.2 ? 0.28 : 0.22)
    : (stats.meanLuma < 0.2 ? 0.22 : 0.12)

  const strokeAlpha = 0.95
  const lineW = boxSelected.value ? 2 : 1

  const x = Math.round(c.width * 0.18)
  const y = Math.round(c.height * 0.18)
  const w = Math.round(c.width * 0.64)
  const h = Math.round(c.height * 0.64)

  ctx.fillStyle = hexToRgba(hex, fillAlpha)
  ctx.fillRect(x, y, w, h)

  ctx.strokeStyle = hexToRgba(hex, strokeAlpha)
  ctx.lineWidth = lineW
  ctx.strokeRect(x, y, w, h)
}

/** --- export tokens --- **/
function buildTokens() {
  return {
    name: 'ACPE tokens',
    version: '0.1.0',
    scene: {
      meanLuma: stats.meanLuma,
      meanSat: stats.meanSat,
      warmth: stats.warmth
    },
    controls: {
      chroma: chroma.value,
      temperature: temp.value,
      baseS: gen.baseS,
      baseL: gen.baseL,
      hueShift: gen.hueShift
    },
    palette: palette.value,
    roles: { ...roles }
  }
}

function downloadTokens() {
  exportMsg.value = ''
  const tokens = buildTokens()
  const json = JSON.stringify(tokens, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = 'acpe.tokens.json'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)

  exportMsg.value = 'Saved: acpe.tokens.json'
}

async function copyCssVars() {
  exportMsg.value = ''
  const css =
`/* ACPE roles */
:root {
  --acpe-bg: ${roles.background};
  --acpe-surface: ${roles.surface};
  --acpe-text: ${roles.text};
  --acpe-primary: ${roles.primary};
  --acpe-accent: ${roles.accent};
}

/* ACPE palette */
:root {
${palette.value.map(p => `  --acpe-${p.name.toLowerCase()}: ${p.hex};`).join('\n')}
}
`
  try {
    await navigator.clipboard.writeText(css)
    exportMsg.value = 'Copied CSS variables to clipboard.'
  } catch {
    exportMsg.value = 'Could not copy (browser blocked clipboard). You can select & copy from DevTools.'
    console.log(css)
  }
}
</script>

<style>
.app { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; }
.row { margin-top: 16px; display: flex; gap: 16px; align-items: flex-start; flex-wrap: wrap; }
.panel { border: 1px solid #ccc; padding: 12px; width: fit-content; }
.panel.wide { min-width: 360px; max-width: 760px; }
.label { font-size: 12px; opacity: 0.7; margin-bottom: 8px; }
.btnRow { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.btn { padding: 6px 10px; font-size: 14px; cursor: pointer; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.small { margin-top: 10px; font-size: 12px; opacity: 0.85; }
.control { margin-top: 10px; }
.controlTitle { font-size: 12px; opacity: 0.8; margin-bottom: 6px; }
.seg { display: flex; gap: 6px; flex-wrap: wrap; }
.segBtn {
  padding: 6px 10px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid #bbb;
  background: #fff;

  color: #111 !important;
}

.segBtn.on {
  border-color: #333;
  font-weight: 600;

  color: #111 !important;
}

.stat { margin-bottom: 6px; }
.hint { margin-top: 10px; font-size: 12px; opacity: 0.8; line-height: 1.4; }

.swatches { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.swatch { border-radius: 10px; padding: 10px; min-height: 64px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer; user-select: none; }
.swName { font-weight: 600; font-size: 14px; }
.swHex { font-size: 12px; opacity: 0.9; }

/** UI preview */
.previewGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  background: var(--bg);
  color: var(--text);
  border: 1px solid #ddd;
}
.card { border-radius: 14px; padding: 14px; background: var(--surface); border: 1px solid rgba(0,0,0,0.08); }
.cardTitle { font-weight: 700; margin-bottom: 8px; }
.cardText { opacity: 0.85; font-size: 13px; line-height: 1.35; }
.cardRow { margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.primaryBtn { background: var(--primary); color: #111; border: none; padding: 8px 12px; border-radius: 12px; cursor: pointer; }
.ghostBtn { background: transparent; color: var(--text); border: 1px solid rgba(0,0,0,0.18); padding: 8px 12px; border-radius: 12px; cursor: pointer; }
.table { margin-top: 10px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(0,0,0,0.10); }
.tr { display: grid; grid-template-columns: 0.6fr 1fr 0.9fr; gap: 8px; padding: 10px 10px; background: rgba(255,255,255,0.4); }
.th { font-weight: 700; background: rgba(0,0,0,0.06); }
.pill { display: inline-block; padding: 4px 8px; border-radius: 999px; background: var(--accent); color: #111; font-size: 12px; }
</style>
