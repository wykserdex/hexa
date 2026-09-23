// HEXA · hexa_hud.js — клиентская часть кастомки.
// Тянет состояние у HEXA (`python -m hexa serve`, порт 3001) и шлёт туда игровые события.
// Требует серверный Lua (hexa_server.lua), который отвечает с игровым временем.
(function () {
    var BASE = "http://127.0.0.1:3001";
    var POLL = 0.5;
    var lastSeq = 0;
    var gameTime = 0;

    function panel() {
        var p = $("#HexaTimersPanel");
        if (!p) p = $.CreatePanel("Panel", $.GetContextPanel(), "HexaTimersPanel");
        return p;
    }

    function render(state) {
        var p = panel();
        p.RemoveAndDeleteChildren();
        (state.upcoming || []).slice(0, 6).forEach(function (row) {
            var label = $.CreatePanel("Label", p, "");
            label.AddClass("hexa-row");
            label.html = true;
            label.text = '<span class="hexa-time">' + row.at + '</span>' + row.title;
        });
    }

    function sendActions(state) {
        (state.actions || []).forEach(function (action) {
            if (action.seq <= lastSeq) return;
            lastSeq = action.seq;
            // песочница: действия уходят на сервер игры, исполняет hexa_server.lua
            GameEvents.SendCustomGameEventToServer("hexa_action", { items: action.items.join("|") });
        });
    }

    function poll() {
        $.AsyncWebRequest(BASE + "/state?since=" + lastSeq, {
            type: "GET",
            callback: function (data) {
                try {
                    var state = JSON.parse(data);
                    render(state);
                    sendActions(state);
                } catch (e) {}
            }
        });
        // сообщаем HEXA игровое время; его присылает сервер игры в hexa_state
        $.AsyncWebRequest(BASE + "/event", {
            type: "POST",
            data: JSON.stringify({ type: "tick", game_time: gameTime })
        });
        $.Schedule(POLL, poll);
    }

    // хоткей: сервер шлёт это событие, когда игрок нажал привязанную клавишу
    GameEvents.Subscribe("hexa_press", function (event) {
        $.AsyncWebRequest(BASE + "/event", {
            type: "POST",
            data: JSON.stringify({ type: "hotkey", action: event.action })
        });
    });

    // игровое время приходит от серверного Lua
    GameEvents.Subscribe("hexa_state", function (event) { gameTime = event.game_time || 0; });

    poll();
})();
