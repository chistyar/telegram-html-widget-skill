# Telegram Widget Profile 1 — Complete Whitelist, Blacklist & Gesture Rules

> Extracted from `https://core.telegram.org/bots/widgets#what-widgets-support` (Profile 1).
> Every Telegram client (iOS, Android, macOS, Desktop, Web) parses widget HTML/CSS/JS inside a QuickJS sandbox and strips anything outside Profile 1 before drawing.

---

## 1. HTML Elements & Attributes

### Allowed (IN Profile 1)
* **Structure & Text:** `div`, `span`, `p`, `br`, `hr`, `h1`, `h2`, `h3`, `h4`, `h5`, `h6`, `header`, `footer`, `main`, `nav`, `section`, `article`, `aside`, `pre`, `blockquote`, `figure`, `figcaption`.
* **Inline Text:** `b`, `i`, `u`, `s`, `em`, `strong`, `small`, `mark`, `code`, `kbd`, `sub`, `sup`, `abbr`, `cite`, `q`, `del`, `ins`, `time`.
* **Lists & Tables:** `ul`, `ol`, `li`, `dl`, `dt`, `dd`, `menu`, `table`, `thead`, `tbody`, `tfoot`, `tr`, `th`, `td` (with `colspan` and `rowspan`), `details`, `summary` (supports `toggle` event).
* **Media & Controls:** `<button>` (**the ONLY allowed form control**), `<canvas>`, `<img>` (**ONLY** with `src="data:image/png;..."`, `jpeg`, `gif`, or `webp` up to `1024x1024` px).
* **Links:** `<a href="#id">` (no navigation) and `<a href="https://...">` (opens via `TelegramWidget.openLink` or `openTelegramLink` on a tap).
* **Attributes:** `class`, `id`, `style`, `title`, `hidden`, `lang`, `dir`, `data-*`, `aria-*`, `disabled` (on `<button>`), and inline `on*` handlers (`onclick`, `onpointerdown`, etc.).

### Stripped / Removed (OUT of Profile 1)
* **ALL Form Inputs:** `form`, `input` (all types: text, checkbox, radio, range, number, hidden), `select`, `option`, `optgroup`, `textarea`, `label`, `fieldset`, `legend`, `datalist`, `output`, `progress`, `meter` — **removed together with their content!**
  * *Replacement:* Build checkboxes, radios, range sliders, and steppers using `<button>` or `<div class="pill">` + JS state!
* **Overlays & Media:** `dialog`, `popover`, `audio`, `video`, `source`, `track`, `iframe`, `frame`, `object`, `embed`, `portal`, `template`, `slot`, `math`, `ruby`.
* **External & Unsupported Images:** `<img src="https://...">` (never requested, shows placeholder), `<img src="data:image/svg+xml...">` (**use inline `<svg>` instead!**), `data:` AVIF, BMP, or ICO.
* **Keyboard & Editing Attributes:** `contenteditable`, `spellcheck`, `inputmode`, `draggable`, `tabindex`, `autofocus`, `accesskey`.

---

## 2. Inline SVG

### Allowed (IN Profile 1)
* `svg`, `g`, `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `text`, `tspan`, `defs`, `symbol`, `use` (fragment `#id` links only), `linearGradient`, `radialGradient`, `stop`, `viewBox`, `transform`, CSS fills/strokes and CSS animations on SVG properties.

### Stripped / Removed (OUT of Profile 1)
* `clipPath`, `mask`, `pattern`, `marker`, SVG filter primitives (`feGaussianBlur`, `feDropShadow`, etc.), SMIL animations (`<animate>`, `<animateTransform>`, `<animateMotion>`), `foreignObject`, `<image>`.

---

## 3. CSS Properties, Selectors & At-Rules

### Allowed (IN Profile 1)
* **Layout:** `display` (`block`, `inline`, `inline-block`, `flex`, `inline-flex`, `grid`, `inline-grid`, `table*`, `none`), `flex-*`, `grid-*`, `gap`, `position` (`static`, `relative`, `absolute`, `fixed` — relative to the bubble), `top`, `right`, `bottom`, `left`, `z-index`, `float`, `aspect-ratio`, `box-sizing`, `object-fit`, `overflow: hidden`, `overflow: clip`.
* **Box & Paint:** `margin*`, `padding*`, `width`, `height`, `min-*`, `max-*`, `border*`, `border-radius`, `outline*`, `box-shadow`, `opacity` (**WARNING: max 16 elements with `opacity < 1` or blurred shadow at once!**), `visibility`, `background*` (with `data:` images, `linear-gradient`, `radial-gradient`, `conic-gradient`, `repeating-*`), 2D `transform` (`translate`, `rotate`, `scale`).
* **Filters:** `filter` with `blur()`, `brightness()`, `drop-shadow()` ONLY; `backdrop-filter` with `blur()`, `brightness()` ONLY (max 2 elements with `backdrop-filter`).
* **Typography:** `font-size`, `font-weight`, `font-style`, `line-height`, generic `font-family` (`system-ui`, `sans-serif`, `serif`, `monospace`, `ui-sans-serif`, `ui-serif`, `ui-monospace`, `ui-rounded`), `font-variant-numeric: tabular-nums`, `text-align`, `text-decoration`, `text-transform`, `letter-spacing`, `white-space`, `overflow-wrap`, `word-break`, single-line `text-overflow: ellipsis`, `vertical-align`, `user-select` (`none`, `text`, `auto`).
* **Colors:** Hex, `rgb()`, `rgba()`, `hsl()`, `hsla()`, `transparent`, `currentColor`, `light-dark()`, `color-scheme`.
* **Units & Functions:** `px`, `em`, `rem`, `%`, `ch`, `ex`, `vw`, `vmin`, `vmax` (relative to bubble width), `calc()`, `min()`, `max()`, `clamp()`, `var()`, `env(safe-area-inset-*)`, `attr(data-*)`.
* **Selectors:** Type, `.class`, `#id`, `[attr]`, combinators, `:first-child`, `:last-child`, `:nth-child()`, `:not()`, `:is()`, `:where()`, `:root`, `::before`, `::after`, `:active`, `:hover` (mouse only), `:disabled` / `:enabled` (on `<button>` only).
* **At-Rules:** `@keyframes` (max 32), `@supports`, `@media` on `min-width`, `max-width`, `orientation`, `prefers-color-scheme`, `prefers-reduced-motion`.

### Stripped / Removed (OUT of Profile 1)
* **Scrolling & Sticky:** `overflow: auto`, `overflow: scroll`, `overflow-x: auto`, `overflow-y: auto` (**all become `overflow: hidden`!**), `position: sticky` (becomes `relative`).
* **Height Units:** `vh`, `dvh`, `svh`, `lvh`, `vb`.
* **Logical Properties:** `margin-inline`, `margin-block`, `padding-inline`, `padding-block`, `inset-inline`, `inline-size`, `block-size`.
* **Effects & 3D:** 3D transforms (`translateZ`, `translate3d`, `rotateX`, `rotateY`, `perspective`), `clip-path`, `mask`, `-webkit-mask`, `mix-blend-mode`, `background-blend-mode`, `filter: grayscale() / saturate() / contrast() / invert() / sepia() / hue-rotate()`, `text-shadow`, `-webkit-line-clamp`, `background-clip: text`.
* **Modern Color Spaces:** `oklch()`, `oklab()`, `lch()`, `lab()`, `hwb()`, `color-mix()`.
* **Selectors & At-Rules:** `:has()`, `:focus`, `:focus-visible`, `:focus-within`, `:checked`, `::placeholder`, `@font-face`, `@import`, `@container`, `@layer`, `@property`, CSS nesting (`&`), `@media (hover: hover)`, `@media (pointer: coarse)`.

---

## 4. Gestures & Touch-Action Matrix

A widget shares its message bubble with Telegram's native chat gestures (vertical chat scrolling, horizontal swipe-to-reply, and 500ms hold for message context menu).

| Element CSS `touch-action` | 500ms Hold | Horizontal Drag | Vertical Drag | When to Use |
| :--- | :--- | :--- | :--- | :--- |
| `touch-action: auto` *(default)* | Telegram opens message menu | Telegram triggers swipe-to-reply | Telegram scrolls chat | Default for cards, text, and regular tap buttons |
| `touch-action: pan-y` | Telegram opens message menu | **Widget receives drag (`pointermove`)** | Telegram scrolls chat | Custom horizontal range sliders, carousels, swipeable cards |
| `touch-action: none` | **Widget receives `contextmenu`** | **Widget receives drag (`pointermove`)** | Telegram scrolls chat | Game pads, hold-to-confirm buttons, interactive `<canvas>` |

* **Important Gesture Rules:**
  1. **Keep interactive controls `>= 20px` away from the leading edge** (left edge in LTR) — the outer 20px always belongs to the OS back gesture.
  2. **Never trigger requests on `pointerdown`** — a touch may turn into a vertical chat scroll, firing `pointercancel` with no `click`. Always trigger `TelegramWidget.request()` inside `click` (or `pointerup`).
  3. **One privileged action per tap:** One tap unlocks **one** call among `TelegramWidget.request()`, `openLink()`, `openTelegramLink()`, or `copyText()`, and it must be invoked **synchronously** inside the event handler (never inside `setTimeout` or after an `await`).
