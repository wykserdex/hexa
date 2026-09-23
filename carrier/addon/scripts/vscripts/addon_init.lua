-- HEXA · точка входа аддона кастомки.
-- Скопируй этот блок в конец своего addon_init.lua (или подключи файл через require).

require("hexa/hexa_server")

function Activate()
    GameRules.GameMode = GameRules.GameMode or {}
    GameRules.GameMode.Hexa = HEXA
    HEXA.Init()
    print("[HEXA] мост поднят: hexa_action / hexa_tick / !hexa ...")

    -- Необязательно: отдать клиенту игровое время сразу после старта,
    -- чтобы HUD начал рисовать таймеры до первого тика.
    CustomGameEventManager:RegisterListener("hexa_ready", function(event)
        local player = PlayerResource:GetPlayer(event.PlayerID)
        if player then
            CustomGameEventManager:Send_ServerToPlayer(player, "hexa_state", {
                game_time = GameRules:GetGameTime(),
            })
        end
    end)
end
