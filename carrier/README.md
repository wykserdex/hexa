# Носитель песочницы — внутренняя часть

Здесь лежит то, что даёт обвязке руки **внутри игры**: серверный Lua кастомки, разметка HUD
и бот-мост. Вместе с `python -m hexa serve` это замыкает цикл: HEXA считает — игра исполняет.

## Канал

```
HEXA (Python)  ──GET /state──▶  Panorama HUD  ──CustomGameEvent──▶  серверный Lua  ──▶  игра
       ▲                             │
       └──────POST /event────────────┘   (хоткеи, игровое время)
```

Никакой инъекции, чтения памяти и эмуляции ввода. Всё внутри твоей кастомки/бот-матча,
через официальные интерфейсы: CustomGameEventManager, Panorama, Bot API.

## Состав

| Файл | Куда | Что делает |
|---|---|---|
| `addon/scripts/vscripts/hexa/hexa_server.lua` | кастомка: `vscripts/` | исполняет действия из очереди, слушает `!hexa ...` в чате, отдаёт игровое время |
| `addon/scripts/vscripts/addon_init.lua` | в конец твоего `addon_init.lua` | поднимает мост при старте |
| `addon/panorama/layout/custom_game/hexa_hud.xml` | кастомка: `panorama/layout/` | разметка панели таймеров |
| `bots/hexa_bot_bridge.lua` | `game/dota/scripts/vscripts/bots/` | бот-матч: `!hexa combo` и `!hexa timer 180` |
| `hexa_hud.js` | генерируется: `python -m hexa build-panorama --out build/panorama` | опрос моста, отрисовка таймеров, отправка хоткеев |

## Установка: кастомка

1. Скопируй `hexa_server.lua` в `scripts/vscripts/hexa/` своего аддона, а блок из
   `addon_init.lua` — в конец своего `addon_init.lua`.
2. Собери клиентскую часть и положи её в аддон:
   ```bash
   python -m hexa build-panorama --out build/panorama
   cp build/panorama/hexa_hud.js <аддон>/panorama/scripts/custom_game/
   cp build/panorama/styling.css <аддон>/panorama/styles/custom_game/hexa_hud.css
   ```
   XML-разметку бери из `addon/panorama/layout/custom_game/hexa_hud.xml`.
3. Запусти обвязку в режиме песочницы:
   ```bash
   python -m hexa --sandbox serve
   ```
4. Запусти свою кастомку локально. Панель таймеров появится в углу, действия из модулей
   уйдут на сервер игры и исполнятся официальным API.

## Установка: бот-матч

1. Скопируй `bots/hexa_bot_bridge.lua` в
   `<Steam>/steamapps/common/dota 2 beta/game/dota/scripts/vscripts/bots/`.
2. Создай лобби с локальным хостом, боты — с включёнными скриптами.
3. В чате: `!hexa combo` — бот выполняет последовательность, `!hexa timer 180` — отметка.
4. `hexa serve --sandbox` при этом считает тайминги и слушает ту же игру через GSI.

## Что проверено, а что нужно проверить в игре

**Проверено на этой машине (Python-сторона, реальные HTTP-запросы):**
- `GET /state` отдаёт таймеры, уведомления, активные отметки, очередь действий и героя;
- `POST /event` с типом `tick` двигает игровые часы и запускает модули;
- `POST /event` с типом `hotkey` запускает комбо и ручные отметки;
- действия попадают в очередь (`seq1..seq4` с кастами) и отдаются клиенту через `?since=`;
- GSI-пейлоад от Доты принимается на `:3000` и порождает те же уведомления, что в демо;
- предохранитель: вне песочницы `GuardedSink` **не кладёт действия в очередь** (проверено отдельно).

**Нужно проверить в игре (честно, здесь не запускалось):**
- имена событий и методов в вашей версии: `CustomGameEventManager`, `Send_ServerToPlayer`,
  `ExecuteOrderFromTable`, `ListenToGameEvent` в бот-скриптах, `GetBot()`;
- доступен ли `$.AsyncWebRequest` из Panorama кастомки к `127.0.0.1` в вашей сборке;
- привязка клавиши: событие `hexa_press` должен кто-то отправлять (в кастомке — свой биндинг,
  вне кастомки работает резервный чат-канал `!hexa ...`).

## Границы

- Действия исполняются **только в твоей игре**: кастомка на своём сервере, локальное лобби, бот-матч.
  Живых людей в этих матчах нет или они согласились играть по твоим правилам.
- Часовые пояса событий (`CustomGameEventManager`) и API движка — официальные; внешних процессов
  внутри игры нет, инъекции нет.
- За пределами песочницы мост не используется: `GuardedSink` не отдаёт действия в очередь,
  пока `general.sandbox = false`.
