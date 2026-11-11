---
name: telegram-html-widgets
description: >
  Complete specification, architectural rules, linter, and code patterns for Telegram HTML Widgets
  (Bot API 10.4: sendWidget, sendSharedWidget, answerWidgetQuery, editMessageWidgetData,
  editSharedWidgetData, and the client-side QuickJS TelegramWidget API). Use this skill whenever
  creating, editing, debugging, compressing, or integrating interactive HTML widgets rendered inside
  Telegram chat message bubbles, or building Telegram Bot backends for Bot API 10.4 widgets.
version: 1.0.0
license: MIT
---

# Telegram HTML Widgets (Bot API 10.4) — Agent Skill

You build **Telegram HTML Widgets** introduced in **Telegram Bot API 10.4 (November 9, 2026)** (official docs: `https://core.telegram.org/bots/widgets` and `https://core.telegram.org/bots/api`).

A Telegram widget is a self-contained HTML document (or bare HTML fragment) with inline `<style>` and `<script>`, sent by a bot in a message (`sendWidget` / `sendSharedWidget`) and rendered natively inside the chat message bubble across iOS, Android, macOS, Windows, and Web clients.

> **CRITICAL RULE FOR AI AGENTS:**
> Telegram widgets DO NOT run in a browser WebView. Their JavaScript runs inside a **QuickJS sandbox** with **zero network access**, and the Telegram app filters the DOM and CSS against **Widget Profile 1**. Any HTML element, CSS property, or JS API outside Profile 1 is **silently stripped** (or stops the widget with `"Widget stopped"`). Never guess standard web features—follow the exact rules below and run `python scripts/check_widget.py <file.html>` before finishing.

---

## 1. Hard Size & Runtime Quotas

| Resource / Parameter | Exact Limit | What Happens If Exceeded |
| :--- | :--- | :--- |
| **Uncompressed HTML** | `1 .. 32,768` bytes of UTF-8 (no `U+0000` NUL) | Server rejects `sendWidget` with `INPUT_MEDIA_WIDGET_TOO_LARGE` / `HTML_INVALID` |
| **Compressed HTML** | **`<= 4,096` bytes** via `zlib.compress(html, 9)` | Server rejects `sendWidget` with `INPUT_MEDIA_WIDGET_TOO_LARGE` |
| **`chat_data` / `public_data`** | `0 .. 1,024` bytes of UTF-8 each | `INPUT_MEDIA_WIDGET_DATA_TOO_LARGE` (Note: 512 Cyrillic chars = 1024 bytes) |
| **`TelegramWidget.request(data)`** | `1 .. 64` bytes of UTF-8 | Throws `TypeError` in widget before sending |
| **`answerWidgetQuery` `data`** | `0 .. 1,024` bytes of UTF-8 | Server rejects with `WIDGET_RESULT_TOO_LARGE` |
| **Time to answer query** | `15` seconds | Rejects in widget with `TIMEOUT`; late bot answer fails with `query is too old` |
| **Request rate limit** | `5` requests per `5` seconds per user & bot | Rejects in widget with `RATE_LIMITED` (`1` request in flight per widget, else `BUSY`) |
| **Shared widget edits** | `1` edit per second (`editSharedWidgetData`) | Fails with `Too Many Requests: retry after ...` (flood wait) |
| **Bubble Dimensions** | Width: `200px`..bubble max (~`320-430px` on phone). Height: `50..600px` | Content taller than `600px` is **clipped** (nothing scrolls inside a widget) |
| **Web Storage (`localStorage`)** | `4,096` bytes per message on device (UTF-8 keys+values) | Throws `QuotaExceededError` (always wrap `setItem` in `try/catch`) |
| **Sandbox Memory & CPU** | `8 MB` RAM, `300 ms/s` JS CPU (`500 ms` max in 1 task) | Widget is killed and displays `"Widget stopped"` |
| **DOM & CSS Limits** | Max `2,000` DOM nodes, `400` CSS rules, `32` `@keyframes` | Widget is killed and displays `"Widget stopped"` |
| **Heavy Paint Elements** | **Max `16` elements at once** with `opacity < 1`, blurred `box-shadow`, `filter`, or `backdrop-filter` (`max 2` with `backdrop-filter`) | **Widget stops immediately!** Never use `opacity` to dim text or slots—use `var(--tg-theme-hint-color)`, `rgba()`, or `fill-opacity` instead! |

### How to Measure Size Exactly Like Telegram's Server
Telegram's server uses `zlib` at level 9 (not `gzip`, which is ~12 bytes larger):
```bash
python -c "import sys,zlib; d=open(sys.argv[1],'rb').read(); print(f'Raw: {len(d)}/32768 B | Zlib9: {len(zlib.compress(d,9))}/4096 B')" widget.html
```
Always keep `zlib` size under **`3,850` bytes** to leave a safety margin.

---

## 2. Widget Profile 1: What Works vs What Is Silently Stripped

Every Telegram client enforces **Profile 1**. Anything in the **FORBIDDEN (OUT)** column is silently deleted from the DOM/CSS or throws an error.

| Category | ALLOWED (IN PROFILE 1) | FORBIDDEN / STRIPPED (OUT OF PROFILE 1) |
| :--- | :--- | :--- |
| **Form Controls & Interactive** | **`<button>` is the ONLY form control!** Custom pills/tabs/sliders built with `<div>`/`<span>` + click/pointer events. `<details>`/`<summary>`. | **`<input>` (all types), `<select>`, `<option>`, `<textarea>`, `<form>`, `<label>`, `<fieldset>`, `<progress>`, `<meter>`, `<dialog>`** — ALL ARE COMPLETELY REMOVED! |
| **Scrolling & Overflow** | Fit content inside `<= 560px` height using tabs, pagination, or steps. `overflow: hidden` or `clip`. | **`overflow: auto`, `overflow: scroll`, `overflow-x: auto`, `overflow-y: auto`** — converted to `overflow: hidden`! Nothing scrolls inside a widget! `position: sticky` becomes `relative`. |
| **Units & Layout** | `px`, `em`, `rem`, `%`, `vw`, `vmin`, `vmax` (relative to bubble width), `flex`, `grid`, `calc()`, `min()`, `max()`, `clamp()`. | **`vh`, `dvh`, `svh`, `vb`** (height-relative units are stripped). `margin-inline`, `padding-block` (logical properties stripped). CSS nesting (`&`) and `@container` stripped. |
| **Colors & Effects** | `var(--tg-theme-*)`, hex, `rgb()`, `rgba()`, `hsl()`, `light-dark()`, `linear-gradient`, `radial-gradient`, `conic-gradient`, `2D transform`. | `oklch()`, `lab()`, `lch()`, `color-mix()`, `text-shadow`, `-webkit-line-clamp`, `background-clip: text`, `3D transforms` (`translateZ`, `rotateX/Y`), `clip-path`, `mask`. |
| **Fonts** | Generic families ONLY: `system-ui`, `sans-serif`, `serif`, `monospace`, `ui-sans-serif`, `ui-monospace`, `ui-rounded`. | Named fonts (`'Roboto'`, `'Inter'`, `'Helvetica'`) and `@font-face` are stripped. |
| **Images & SVG** | Inline `<svg>` (`path`, `rect`, `circle`, `line`, `polyline`, `polygon`, `text`, `linearGradient`, `radialGradient`). `<img src="data:image/png;base64,...">` (PNG/JPEG/GIF/WebP `<=1024x1024`). | External image URLs (`https://...`), `<img src="data:image/svg+xml...">`, SVG `<clipPath>`, `<mask>`, `<pattern>`, `<fe*>` filters, `<foreignObject>`, SMIL `<animate>`. |
| **Network & Browser APIs** | `window.TelegramWidget`, `localStorage`, `sessionStorage`, `Promise`, `setTimeout`, `requestAnimationFrame`, `Canvas 2D`, `Intl`, `TextEncoder`. | `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `Worker` (throw `NetworkDisabledError`). `navigator.clipboard` (use `TelegramWidget.copyText`), `alert`/`confirm`/`prompt`, ` focus()`. |
| **Input & Gestures** | `click`, `dblclick`, `pointerdown`, `pointermove`, `pointerup`, `pointercancel`. Horizontal drag requires `touch-action: pan-y` or `none` on the element. | `touchstart`, `touchmove`, `touchend` (removed on touch devices — use Pointer Events!). `keydown`/`keyup`/`input` (no keyboard exists). Vertical drag always scrolls the chat. |

### The Bottom Timestamp Corner Rule (`safe-area-inset-bottom`)
When a widget message has **no caption below it**, Telegram draws the message timestamp (`14:32 ✓✓`) over the bottom-right corner of the widget.
* **Best Practice:** Either always send a `caption` below the widget in `sendWidget`, OR pad the bottom container using:
  ```css
  body { margin: 0; padding: 12px 12px max(12px, env(safe-area-inset-bottom)); }
  ```

---

## 3. Client-Side JavaScript API (`window.TelegramWidget`)

Inside Telegram, `window.TelegramWidget` exists synchronously before the first `<script>` line runs. Outside Telegram (in a regular browser), it is `undefined`—always include a compact fallback mock for local testing.

### 3.1 Properties
* `TelegramWidget.chatData` (`string | null`): Message-specific state (up to 1024 UTF-8 bytes), or `null`. Shared by members in a group, always `null` in a forward. Parse with `JSON.parse()` inside `try/catch`.
* `TelegramWidget.publicData` (`string | null`): Shared state (up to 1024 UTF-8 bytes), or `null`. Synchronized across all instances of a shared widget (`is_shared: true`).
* `TelegramWidget.colorScheme`: `'light'` or `'dark'`.
* `TelegramWidget.themeParams`: Frozen object with `#rrggbb` colors (`bg_color`, `text_color`, `hint_color`, `link_color`, `button_color`, `button_text_color`, `secondary_bg_color`, `accent_text_color`, `subtitle_text_color`, `destructive_text_color`, `section_separator_color`). Also injected on `:root` as `--tg-theme-<key-with-dashes>`.
* `TelegramWidget.viewer`: `{ id, first_name, last_name?, username?, is_premium? }` of the user viewing the widget (or `null` in previews/forwards where queries are disallowed).
* `TelegramWidget.chatType`: `'private' | 'group' | 'supergroup' | 'channel' | null`.
* `TelegramWidget.isForward` (`boolean`), `TelegramWidget.isPreview` (`boolean`), `TelegramWidget.isActive` (`boolean`).
* `TelegramWidget.wallet`: `WidgetWallet | null` (for TON transactions/signing).

### 3.2 Methods
* **`TelegramWidget.request(data[, options]) -> Promise<{ result: string | null }>`**
  * Sends `data` (`1..64` UTF-8 bytes string) to the bot.
  * **MUST be called synchronously inside a user tap handler (`click` or `pointerup`)** (or in the background in a `private` chat with the bot: once when the widget appears on screen, then at most once every 5s).
  * Only **one request in flight** at a time (a second call rejects with `err.code === 'BUSY'`).
  * Resolves with `{ result: string | null }` (the `data` string passed by the bot to `answerWidgetQuery`, up to 1024 bytes).
  * Rejects with `WidgetRequestError` where `err.code` is `'NOT_ALLOWED' | 'BUSY' | 'RATE_LIMITED' | 'TIMEOUT' | 'FAILED' | 'INVALID_ANSWER'`.
  * **CRITICAL:** `answerWidgetQuery` only returns `{ result }` to the caller—it does **not** persist state! To persist state changes, the bot must also call `editMessageWidgetData` or `editSharedWidgetData`.
* **`TelegramWidget.watchPublicData()` / `unwatchPublicData()`**
  * Call `watchPublicData()` on init if the widget displays live `publicData` from a shared widget (`is_shared: true`). While on screen, the client polls at the shared widget's `cache_time` (default 30s, configurable `5..3600s` via `editSharedWidgetData`) and fires `publicDataChanged`.
  * Keep a revision counter (`"r": 12`) in your state so an older poll never overwrites a newer `request` answer.
* **`TelegramWidget.copyText(text)`**: Copies `1..256` UTF-16 chars to clipboard on a tap and shows a native toast.
* **`TelegramWidget.openLink(url)`**: Opens external `https://` URL (`<=256` chars) with user confirmation on a tap.
* **`TelegramWidget.openTelegramLink(url)`**: Opens `https://t.me/...` link (`<=256` chars) inside Telegram without confirmation on a tap.
* **`TelegramWidget.setResizeAnchor('top' | 'bottom')`**: Controls which edge stays fixed when height changes. Guard with `TelegramWidget.setResizeAnchor?.('bottom')`.
* **`TelegramWidget.HapticFeedback`**: `.impactOccurred('light'|'medium'|'heavy'|'rigid'|'soft')`, `.notificationOccurred('error'|'success'|'warning')`, `.selectionChanged()`.
* **`TelegramWidget.ready()`**: Optional signal that initial render is complete.

### 3.3 Events (`TelegramWidget.onEvent(type, handler)`)
* `'chatDataChanged'`: Bot updated `chat_data` via `editMessageWidgetData`. `TelegramWidget.chatData` is already updated when this fires.
* `'publicDataChanged'`: Bot updated `public_data` via `editMessageWidgetData` or `editSharedWidgetData`.
* `'themeChanged'`: User switched light/dark theme or palette.
* `'activated'` / `'deactivated'`: Widget entered or left the visible viewport.
* `'contentSafeAreaChanged'`: Timestamp corner inset changed.

### 3.4 TON Wallet Payments (`TelegramWidget.wallet`)
1. Check `if (TelegramWidget.wallet)` before rendering a TON pay button.
2. On a button tap, call `TelegramWidget.request('pay:item_1', { wallet: true })`.
3. The bot receives `widget_query` with `type: { type: "data", wallet_card: ... }` containing the user's TON wallet address & balance, and replies via `answerWidgetQuery` with a JSON-serialized TON Connect transaction: `{"valid_until": 1794350000, "messages": [{"address": "UQ...", "amount": "1000000000"}]}`.
4. In the `.then(ans => ...)` handler (within 10 seconds, no second tap needed!), the widget calls:
   ```javascript
   TelegramWidget.wallet.sendTransaction(JSON.parse(ans.result), 'paid:item_1')
     .then(finalAns => renderPaid(finalAns.result))
     .catch(err => renderError(err.code)); // 'REJECTED' | 'BAD_REQUEST' | 'TIMEOUT'
   ```

---

## 4. Bot API 10.4 Backend Contract

For full parameter tables, read `references/bot-api-10-4-reference.md`. Below are the 5 core HTTP methods:

1. **`sendWidget`**:
   ```json
   POST https://api.telegram.org/bot<TOKEN>/sendWidget
   {
     "chat_id": 123456789,
     "html": "<style>...</style><div>...</div><script>...</script>",
     "chat_data": "{\"step\":1}",
     "public_data": "{\"r\":1,\"price\":92450}",
     "allow_queries": true,
     "is_shared": false,
     "caption": "Optional fallback & notification text"
   }
   ```
   *(Note: Pass `"allow_queries": true` whenever the widget calls `TelegramWidget.request()`, otherwise every request fails with `NOT_ALLOWED`! Currently in production, `sendWidget` works in `private` chats with the bot; groups/inline/forwards work on the Telegram test server).*

2. **`sendSharedWidget`**: Re-sends a previously created shared widget (`is_shared: true`) by its `widget_id` (`result.widget.id` from the first `sendWidget`).
3. **`answerWidgetQuery`**: Must be called within **15 seconds** for every incoming `widget_query` or `shared_widget_query` in `Update`:
   ```json
   POST https://api.telegram.org/bot<TOKEN>/answerWidgetQuery
   {
     "widget_query_id": "8123456789012345678",
     "data": "{\"ok\":true,\"id\":\"BK-104\"}"
   }
   ```
4. **`editMessageWidgetData`**: Silently updates `chat_data` and/or `public_data` of a specific message (`chat_id` + `message_id` or `inline_message_id`). Pass `""` (empty string) to clear a state back to `null`.
5. **`editSharedWidgetData`**: Silently updates `public_data` (and optional `cache_time` `5..3600` seconds) for **all** messages displaying `widget_id` (max 1 edit/sec).

---

## 5. Canonical Minimal Widget Pattern

Always follow this pattern when authoring a new Telegram HTML Widget:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<style>
:root{
  --bg:var(--tg-theme-bg-color,#fff);
  --txt:var(--tg-theme-text-color,#000);
  --hint:var(--tg-theme-hint-color,#707579);
  --btn:var(--tg-theme-button-color,#3390ec);
  --btn-t:var(--tg-theme-button-text-color,#fff);
  --card:var(--tg-theme-secondary-bg-color,#f4f4f5);
  --err:var(--tg-theme-destructive-text-color,#e53935);
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--txt);padding:12px 12px max(12px,env(safe-area-inset-bottom));font-size:13px;line-height:1.35;user-select:none}
.w-card{background:var(--card);border-radius:12px;padding:12px;margin-bottom:8px}
.w-hint{color:var(--hint);font-size:11px}
.w-btn{background:var(--btn);color:var(--btn-t);border:none;border-radius:10px;padding:11px;font-weight:700;font-size:14px;width:100%;cursor:pointer}
</style>
</head>
<body>
<div class="w-card">
  <div id="title" style="font-weight:700;font-size:15px">Заголовок</div>
  <div class="w-hint" id="status">Готово к отправке</div>
</div>
<button class="w-btn" id="act-btn">Подтвердить</button>
<script>
(function(){
  var TW = window.TelegramWidget || {
    chatData: null, publicData: null,
    onEvent: function(){}, ready: function(){}, watchPublicData: function(){},
    request: function(d){ return Promise.resolve({result: JSON.stringify({ok:1, echo:d})}); }
  };
  var $ = function(id){ return document.getElementById(id); };
  var busy = false;

  function parse(s){ try { return s ? JSON.parse(s) : null; } catch(e){ return null; } }

  function render(){
    var cd = parse(TW.chatData) || {};
    if(cd.confirmed){
      $('status').textContent = 'Подтверждено: #' + cd.confirmed;
      $('act-btn').disabled = true;
      $('act-btn').textContent = 'Выполнено ✓';
    }
  }

  $('act-btn').onclick = function(){
    if(busy) return;
    busy = true;
    $('act-btn').disabled = true;
    $('status').textContent = 'Отправка...';
    TW.request('ACT|1').then(function(ans){
      busy = false;
      var res = parse(ans && ans.result);
      if(res && res.id){
        $('status').textContent = 'Подтверждено: #' + res.id;
        $('act-btn').textContent = 'Выполнено ✓';
      } else {
        $('act-btn').disabled = false;
        render();
      }
    }, function(err){
      busy = false;
      $('act-btn').disabled = false;
      $('status').textContent = 'Ошибка: ' + (err && err.code ? err.code : 'FAILED');
    });
  };

  TW.onEvent('chatDataChanged', render);
  TW.onEvent('publicDataChanged', render);
  render();
  if(TW.ready) TW.ready();
})();
</script>
</body>
</html>
```

---

## 6. Mandatory Pre-Delivery Checklist for AI Agents

Before returning any Telegram HTML Widget to the user, run `python scripts/check_widget.py <path/to/widget.html>` and verify:
1. **`zlib.compress(html, 9)` is `<= 4096` bytes** and raw UTF-8 length is `<= 32768` bytes.
2. **Zero `<input>`, `<select>`, `<textarea>`, or `<form>` elements** (use `<button>` and `<div>` pills instead).
3. **Zero `overflow: auto` or `overflow: scroll`** (nothing scrolls inside a widget; use tabs, pagination, or `flex-wrap`).
4. **Zero `opacity < 1` on repeated elements** (never use `opacity` on slots/pills/labels; use `var(--tg-theme-hint-color)` or `rgba()` so you never hit the 16-element stop limit).
5. **All `TelegramWidget.request(payload)` payloads are `1..64` UTF-8 bytes** and called synchronously inside `onclick` / `onpointerup`.
6. **Backend passes `"allow_queries": True`** in `sendWidget` and answers every `widget_query` within 15 seconds via `answerWidgetQuery`.
