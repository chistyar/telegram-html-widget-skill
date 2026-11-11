# Telegram Bot API 10.4 — Complete Widgets Reference

> Canonical specification extracted from `https://core.telegram.org/bots/api` and `https://core.telegram.org/bots/widgets` (Bot API 10.4, November 9, 2026).

---

## 1. Bot API Methods

### 1.1 `sendWidget`
Use this method to send a message with an HTML widget.
* **Production availability:** Currently, in the production environment, widgets can be sent only to **private chats**, and sent widgets automatically have `protect_content` enabled and therefore cannot be forwarded. (Groups, inline mode, and forwards work on the Telegram test server).
* **Returns:** On success, the sent `Message` is returned (with `message.widget` populated, including `message.widget.id` if `is_shared: true`).

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `chat_id` | Integer or String | **Yes** | Unique identifier for the target chat or username of the target supergroup (`@username`). |
| `message_thread_id` | Integer | Optional | Unique identifier for the target message thread (topic) of a forum; for forum supergroups and private chats of bots with forum topic mode enabled only. |
| `html` | String | **Yes** | HTML code of the widget, `1..32768` bytes of UTF-8 (no `U+0000` NUL character). Must not exceed **`4096` bytes** when compressed by `zlib` at level 9 (`INPUT_MEDIA_WIDGET_TOO_LARGE` / `INPUT_MEDIA_WIDGET_HTML_INVALID`). |
| `width` | Integer | Optional | Width of the widget in logical pixels; omit (or `0`) if the widget must occupy the whole width of the message bubble. Clamped by the app to `200..max_bubble_width`. |
| `height` | Integer | Optional | Height of the widget in logical pixels; omit (or `0`) if the height is automatic based on content (`50..600` px). |
| `public_data` | String | Optional | Public (shared) state of the widget, `0..1024` UTF-8 bytes, available wherever the widget is shown. If `is_shared: true`, all messages with it share this state. |
| `chat_data` | String | Optional | Chat-specific state of the widget, `0..1024` UTF-8 bytes, tied to this specific message (never carried by forwards). |
| `caption` | String | Optional | Widget caption, `0..1024` characters after entities parsing. Shown in chat list, notifications, search, and on clients that do not yet support widgets. |
| `parse_mode` | String | Optional | Mode for parsing entities in the caption (`"HTML"`, `"MarkdownV2"`). |
| `caption_entities` | Array of `MessageEntity` | Optional | List of special entities in the caption. |
| `show_caption_above_media` | Boolean | Optional | Pass `True` if the caption must be shown above the widget (leaves message timestamp overlaid on the widget's bottom corner). |
| `allow_queries` | Boolean | Optional | **Pass `True` to allow the widget to send queries (`TelegramWidget.request`) to the bot.** Without this, all requests reject with `NOT_ALLOWED` and `TelegramWidget.viewer` is `null`. |
| `is_shared` | Boolean | Optional | Pass `True` to create a shared widget on the server, which can be re-sent via `sendSharedWidget` and updated globally via `editSharedWidgetData`. |
| `disable_notification` | Boolean | Optional | Sends the message silently. |
| `protect_content` | Boolean | Optional | Protects the contents of the sent message from forwarding and saving. |
| `allow_paid_broadcast` | Boolean | Optional | Pass `True` to allow up to 1000 messages/sec for 0.1 Telegram Stars per message. |
| `message_effect_id` | String | Optional | Unique identifier of the message effect to be added (private chats only). |
| `reply_parameters` | `ReplyParameters` | Optional | Description of the message to reply to. |
| `reply_markup` | `InlineKeyboardMarkup` / `ReplyKeyboardMarkup` | Optional | Additional interface options (e.g., inline buttons rendered underneath the widget bubble). |

---

### 1.2 `sendSharedWidget`
Use this method to send again a shared widget previously created by the bot (via `sendWidget` with `is_shared: true`).

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `chat_id` | Integer or String | **Yes** | Unique identifier for the target chat or `@username`. |
| `message_thread_id` | Integer | Optional | Forum topic thread identifier. |
| `widget_id` | String | **Yes** | Unique identifier of the shared widget (obtained from `message.widget.id` when first sent with `is_shared: true`). |
| `chat_data` | String | Optional | Chat-specific data for this new message instance, `0..1024` UTF-8 bytes. (The `public_data`, `html`, `width`, `height`, and `allow_queries` are inherited from the shared widget). |
| `caption` | String | Optional | Widget caption, `0..1024` characters. |
| `parse_mode` | String | Optional | Mode for parsing entities in the caption. |
| `show_caption_above_media` | Boolean | Optional | Pass `True` if caption must be shown above the widget. |
| `reply_markup` | `InlineKeyboardMarkup` | Optional | Inline keyboard or reply markup. |

---

### 1.3 `answerWidgetQuery`
Use this method to send an answer to a query (`widget_query` or `shared_widget_query`) from a widget.
* **Timeout:** Must be answered within **15 seconds**, otherwise the widget's Promise rejects with `TIMEOUT`.
* **Behavior:** The answer is received **only** by the widget instance that sent the query (as `{ result: data }`) and **does not** mutate `chat_data` or `public_data`. Returns `True` on success.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `widget_query_id` | String | **Yes** | Unique identifier for the query to be answered (`update.widget_query.id` or `update.shared_widget_query.id`). |
| `data` | String | Optional | Data to be returned to the widget as `answer.result`, `0..1024` UTF-8 bytes (`WIDGET_RESULT_TOO_LARGE` if exceeded). |

---

### 1.4 `editMessageWidgetData`
Use this method to edit `chat_data` and/or `public_data` of a widget in a message sent by the bot or via the bot (inline).
* **Rate limit:** Counts as one sent message against the bot's message sending limits. If `public_data` of a shared widget is changed, it can be changed at most **once per second**.
* **Empty string:** Passing `""` clears that state (the widget sees `null`). Omitting a parameter leaves that state unchanged.
* **Unchanged state:** If the new state is identical to the current state, returns `400 Bad Request: message is not modified`.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `chat_id` | Integer or String | Optional | Required if `inline_message_id` is not specified. |
| `message_id` | Integer | Optional | Required if `inline_message_id` is not specified. |
| `inline_message_id` | String | Optional | Required if `chat_id` and `message_id` are not specified. |
| `public_data` | String | Optional | New public data of the widget, `0..1024` UTF-8 bytes; pass `""` to clear. |
| `chat_data` | String | Optional | New chat-specific data of the widget, `0..1024` UTF-8 bytes; pass `""` to clear. |

---

### 1.5 `editSharedWidgetData`
Use this method to edit `public_data` of a shared widget globally across all messages and forwards displaying it.
* **Rate limit:** At most **1 edit per second** per `widget_id`. Coalesce rapid updates on your backend!

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `widget_id` | String | **Yes** | Unique identifier of the shared widget. |
| `public_data` | String | **Yes** | New public data of the widget, `0..1024` UTF-8 bytes; pass `""` to remove public data. |
| `cache_time` | Integer | Optional | Client polling interval in seconds (`5..3600`, default `30`) while a widget that called `TelegramWidget.watchPublicData()` is on screen. |

---

## 2. Bot API Types & Classes

### 2.1 `Widget` (in `Message.widget` and `ExternalReplyInfo.widget`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String | *Optional*. Unique identifier of the shared widget (present only if sent with `is_shared: true`). |
| `width` | Integer | *Optional*. Fixed logical width (`200..max`), omitted if automatic. |
| `height` | Integer | *Optional*. Fixed logical height (`50..600`), omitted if automatic. |
| `html` | String | HTML source code of the widget. |
| `public_data` | String | *Optional*. Public state of the widget (`0..1024` bytes). |
| `chat_data` | String | *Optional*. Message-specific chat state (`0..1024` bytes). |

### 2.2 `WidgetQuery` (in `Update.widget_query`)
Represents an incoming query from a widget in an original message sent by the bot or via inline mode.
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique query identifier. |
| `from` | `User` | Authenticated Telegram user who tapped the widget (or whose client sent a background request in a private chat). |
| `chat` | `Chat` | *Optional*. Chat containing the widget message (omitted for inline messages). |
| `message_id` | Integer | *Optional*. Message identifier (omitted for inline messages). |
| `inline_message_id` | String | *Optional*. Inline message identifier. |
| `chat_instance` | String | Global identifier uniquely corresponding to the chat. |
| `chat_type` | String | *Optional*. For inline messages: `"sender"`, `"private"`, `"group"`, `"supergroup"`, or `"channel"`. |
| `type` | `WidgetQueryType` | *Optional*. Describes TON wallet payload if the query was initiated via `{ wallet: true }`, `wallet.sendTransaction`, or `wallet.signData`. |
| `data` | String | Query payload sent by `TelegramWidget.request(data)`, `1..64` UTF-8 bytes. |
| `widget_id` | String | *Optional*. Identifier of the shared widget if `is_shared: true`. |

### 2.3 `SharedWidgetQuery` (in `Update.shared_widget_query`)
Represents an incoming query from a **forwarded** message containing a shared widget (`is_shared: true` + `allow_queries: true`).
* Contains **only**: `id`, `from`, `type` (optional), `data` (`1..64` bytes), and `widget_id`. (No `chat`, `message_id`, or `chat_instance` is exposed for privacy).

### 2.4 `WidgetQueryType` & `WidgetQueryWallet` (TON Wallet Integration)
When a widget interacts with `TelegramWidget.wallet`, `widget_query.type` contains one of:
1. **`WidgetQueryTypeData`** (`type: "data"`):
   * Triggered by `TelegramWidget.request(data, { wallet: true })` on a tap.
   * Contains `wallet_card` (`TonWalletCard`: user's profile TON wallet address and balance).
2. **`WidgetQueryTypeSentTransaction`** (`type: "sent_transaction"`):
   * Triggered after user confirms `TelegramWidget.wallet.sendTransaction(tx, data)`.
   * Contains `wallet` (`WidgetQueryWallet`: `address`, `amount` in nanotons, `public_key`, `state_init`) and `msg_hash` (String).
   * **Security Note:** Always verify the transaction on the TON blockchain (sender, recipient, amount, outcome), never rely on `msg_hash` alone!
3. **`WidgetQueryTypeSignData`** (`type: "sign_data"`):
   * Triggered after user confirms `TelegramWidget.wallet.signData(payload, data)`.
   * Contains `wallet` (`WidgetQueryWallet`) and `sign_data` (TON Connect signature JSON signed for domain `bot<bot_id>`).

### 2.5 Inline Mode Classes (Currently Test Server Only)
* **`InputWidgetMessageContent`**: Used in `InlineQueryResultArticle.input_message_content` to send a new widget (`html`, `width`, `height`, `public_data`, `chat_data`, `caption`, `parse_mode`, `show_caption_above_media`, `allow_queries`, `is_shared`).
* **`InputSharedWidgetMessageContent`**: Used in `InlineQueryResultArticle.input_message_content` to send an existing shared widget (`widget_id`, `chat_data`, `caption`, `parse_mode`, `show_caption_above_media`).
