# Telegram HTML Widgets (Bot API 10.4) — AI Agent Skill & Profile 1 Linter

[![Bot API](https://img.shields.io/badge/Telegram_Bot_API-10.4-2481cc?style=flat-square&logo=telegram)](https://core.telegram.org/bots/api-changelog#november-9-2026)
[![Widget Profile](https://img.shields.io/badge/Widget_Profile-1_(QuickJS)-34c759?style=flat-square)](https://core.telegram.org/bots/widgets)
[![Size Limit](https://img.shields.io/badge/Zlib_Level_9-%E2%89%A4_4096_Bytes-orange?style=flat-square)](#3-profile-1-linter--size-validator)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

Готовый **Agent Skill (`SKILL.md`)**, справочник спецификаций и автоматический линтер для создания нативных **HTML-виджетов Telegram (`sendWidget` / `sendSharedWidget`)**, вышедших в **Bot API 10.4 (9 ноября 2026)**.

Подходит для **Antigravity, Claude Code, Cursor, Windsurf, Codex / OpenClaw** и любых других AI-агентов.

---

## Зачем нужен этот скилл? (Почему обычные LLM ломают виджеты)

В Bot API 10.4 появились интерактивные HTML-виджеты, которые рендерятся **прямо внутри пузыря сообщения за 0 мс** без открытия браузера/WebView. Но ни одна базовая LLM не знает жёстких правил песочницы **Telegram Widget Profile 1 (QuickJS)** и при просьбе «напиши виджет для Telegram» генерирует нерабочий код:

1. **Все стандартные теги форм вырезаются:** `<input>`, `<select>`, `<textarea>`, `<form>`, `<label>` бесследно удаляются клиентом Telegram. Единственный разрешённый контрол — `<button>`.
2. **Внутри виджета нет скролла:** `overflow: auto` и `overflow: scroll` принудительно превращаются в `overflow: hidden`, а единицы `vh` / `dvh` удаляются.
3. **Аварийная остановка (`"Widget stopped"`) при >16 элементах с `opacity < 1`:** если нейросеть приглушит неактивные слоты или подписи через `opacity: 0.5`, на 17-м элементе виджет упадёт.
4. **Жёсткий лимит сжатия `zlib(level=9) <= 4096 байт` (и `<= 32 КБ` raw UTF-8):** ни один фронтенд-фреймворк (React/Vue) туда не помещается, а каждый запрос `TelegramWidget.request(data)` ограничен **64 байтами**.
5. **Нулевой доступ к сети (`Zero-Network`):** `fetch`, `XMLHttpRequest` и `WebSocket` выбрасывают `NetworkDisabledError`.

Подключив эту папку как **Skill**, ваш ИИ-агент с первой попытки пишет валидные, адаптивные под тёмную/светлую тему Telegram виджеты до 3.5 КБ и сразу проверяет их встроенным линтером.

---

## 1. Структура пакета

```text
tg-widget_skill/
├── SKILL.md                                 # Главный системный манифест и правила для ИИ-агента
├── README.md                                # Документация и инструкция по установке
├── references/
│   ├── bot-api-10-4-reference.md            # Полная спецификация sendWidget, sendSharedWidget,
│   │                                        # answerWidgetQuery, editMessageWidgetData и TON Wallet
│   └── widget-profile-1-whitelist.md        # Полный список разрешённых/вырезаемых HTML, CSS, SVG,
│                                            # JS API и матрица жестов touch-action
├── scripts/
│   └── check_widget.py                      # Линтер Profile 1 и точный счётчик zlib(9) <= 4096 B
└── examples/
    └── boilerplate.html                     # Эталонный стартер (2.2 КБ в zlib-9, 0 ошибок)
```

---

## 2. Быстрая установка в AI-агенты

### Antigravity / Gemini CLI
Скопируйте папку `tg-widget_skill` в директорию глобальных скиллов:
```bash
# Windows (PowerShell)
Copy-Item -Recurse .\tg-widget_skill "$HOME\.gemini\config\skills\telegram-html-widgets"

# macOS / Linux
cp -r ./tg-widget_skill ~/.gemini/config/skills/telegram-html-widgets
```

### Claude Code
Положите папку в `.claude/skills/` вашего проекта или в глобальный каталог `~/.claude/skills/`:
```bash
mkdir -p .claude/skills
cp -r ./tg-widget_skill .claude/skills/telegram-html-widgets
```

### Cursor / Windsurf
Добавьте содержимое `SKILL.md` в `.cursor/rules/telegram-widgets.mdc` (или укажите `@tg-widget_skill/SKILL.md` в промпте перед генерацией виджета).

---

## 3. Linter & Валидатор размера (`check_widget.py`)

Сервер Telegram проверяет размер виджета через **`zlib.compress(html, 9) <= 4096`** (а не через обычный `gzip`, который отличается на 12 байт). Скрипт `scripts/check_widget.py` считает точный серверный размер и сканирует код на запрещённые теги, CSS-свойства и сетевые вызовы:

```bash
python tg-widget_skill/scripts/check_widget.py tg-widget_skill/examples/boilerplate.html
```

Пример вывода:
```text
[PASS] boilerplate.html           | Raw:  6002/32768 B | Zlib9: 2246/4096 B (Gzip9: 2258 B)
```

Что отлавливает линтер:
* Превышение `32 768 B` raw UTF-8 или `4 096 B` `zlib(9)` и наличие `NUL`-байтов (`U+0000`).
* Запрещённые теги: `<input>`, `<select>`, `<textarea>`, `<form>`, `<iframe>`, `<audio>`, `<video>`, SVG `<clipPath>`, `<mask>`, `<foreignObject>`, `<animate>`.
* Вырезаемые CSS-правила: `overflow: auto/scroll`, `position: sticky`, единицы `vh/dvh/svh`, `@font-face`, `@import`, `@container`, `:has()`, `clip-path`, `text-shadow`, `oklch()`.
* Опасное использование `opacity < 1` (предупреждение о лимите в 16 «тяжёлых» элементов на экране).
* Запрещённые вызовы в песочнице QuickJS: `fetch()`, `XMLHttpRequest`, `WebSocket`, `navigator.clipboard`, `alert/confirm/prompt`, `touchstart/touchmove/touchend` и внешние картинки `<img src="https://...">`.

---

## 4. Как протестировать готовые коммерческие виджеты вживую

Хотите посмотреть, как нативные HTML-виджеты Bot API 10.4 работают прямо внутри ленты чата Telegram без единого экрана загрузки?

👉 **Откройте нашего демо-бота в Telegram: [@ttttesttsttabot](https://t.me/ttttesttsttabot)** и отправьте команду `/all`:
1. **Онлайн-запись (`/booking`, 3.68 КБ zlib):** интерактивный календарь дней недели и сетка слотов времени (под интеграцию с YClients / Altegio / Dikidi).
2. **D2C Экспресс-корзина (`/shop`, 3.74 КБ zlib):** карточка товара с выбором модификаций, шагомером количества `+/-` и заказом в 1 клик.
3. **EdTech Лид-Квиз (`/quiz`, 3.77 КБ zlib):** мульти-шаговый опросник с прогресс-баром и мгновенным расчётом результата внутри одного сообщения.
4. **Crypto / Трейдинг карточка (`/trading`, 3.27 КБ zlib):** живой SVG-график, расчёт PnL, выбор плеча/маржи и исполнение ордера.

---

## 5. Примеры промптов для вашего ИИ-агента (после установки скилла)

* *"Используя скилл `telegram-html-widgets`, сверстай нативный HTML-виджет калькулятора ипотеки с двумя горизонтальными ползунками (`touch-action: pan-y`), пересчётом ежемесячного платежа и отправкой заявки через `TelegramWidget.request`. Проверь результат через `check_widget.py`."*
* *"Напиши бэкенд на Python (`aiogram 3` / raw HTTP) для отправки `sendWidget` с `allow_queries: true` и обработки `widget_query` через `answerWidgetQuery` и `editMessageWidgetData`."*

---

## Лицензия
MIT License. Свободно используйте в личных и коммерческих проектах.
