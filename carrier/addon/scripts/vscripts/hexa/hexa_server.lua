-- HEXA · серверная часть аддона кастомки.
--
-- Канал: клиентский HUD (hexa_hud.js) -> CustomGameEventManager -> этот файл -> официальный API игры.
-- Ничего, кроме API самой Dota, здесь нет: аддон исполняет действия в СВОЕЙ игре,
-- где правила задаёт автор кастомки. Это и есть носитель для автоматизации.
--
-- Проверить в игре (не запускалось на этой машине): имена событий и методов API.
-- Список методов — официальная документация Valve по Workshop Tools + moddota.

local HEXA = {}

local ALLOWED = { cast = true, move = true, attack = true, stop = true }

local function split_items(packed)
    local out = {}
    for chunk in string.gmatch(packed or "", "[^|]+") do
        table.insert(out, chunk)
    end
    return out
end

local function hero_of(pid)
    if not PlayerResource then return nil end
    local hero = PlayerResource:GetSelectedHeroEntity(pid)
    if hero and not hero:IsNull() then return hero end
    return nil
end

-- ---------------------------------------------------------------- исполнители

local function do_cast(hero, ability_name)
    local ability = hero:FindAbilityByName(ability_name)
    if not ability then return false, "нет способности " .. tostring(ability_name) end
    if not ability:IsFullyCastable() then return false, "не готова: " .. ability_name end
    hero:CastAbilityNoTarget(ability, hero:GetPlayerOwnerID())
    return true
end

local function do_move(hero, arg)
    local x, y = string.match(arg or "", "(%S+)%s+(%S+)")
    if not x or not y then return false, "нужны координаты x y" end
    ExecuteOrderFromTable({
        UnitIndex = hero:entindex(),
        OrderType = DOTA_UNIT_ORDER_MOVE_TO_POSITION,
        Position = Vector(tonumber(x), tonumber(y), 0),
        Queue = false,
    })
    return true
end

local function do_attack(hero, arg)
    local target = EntIndexToHScript(tonumber(arg) or -1)
    if not target then return false, "цель не найдена" end
    ExecuteOrderFromTable({
        UnitIndex = hero:entindex(),
        OrderType = DOTA_UNIT_ORDER_ATTACK_TARGET,
        TargetIndex = target:entindex(),
        Queue = false,
    })
    return true
end

local function do_stop(hero)
    ExecuteOrderFromTable({
        UnitIndex = hero:entindex(),
        OrderType = DOTA_UNIT_ORDER_STOP,
        Queue = false,
    })
    return true
end

-- ---------------------------------------------------------------- API для HUD и чата

function HEXA.execute(pid, packed)
    local hero = hero_of(pid)
    if not hero then return { "нет героя у игрока " .. tostring(pid) } end

    local results = {}
    for _, line in ipairs(split_items(packed)) do
        local kind, arg = string.match(line, "^(%S+)%s+(.+)$")
        if kind and ALLOWED[kind] then
            local ok, err
            if kind == "cast" then
                ok, err = do_cast(hero, arg)
            elseif kind == "move" then
                ok, err = do_move(hero, arg)
            elseif kind == "attack" then
                ok, err = do_attack(hero, arg)
            elseif kind == "stop" then
                ok, err = do_stop(hero)
            end
            table.insert(results, (ok and "ok " or "fail ") .. line .. (err and (" (" .. err .. ")") or ""))
        else
            table.insert(results, "skip " .. tostring(line) .. " (действие не разрешено)")
        end
    end
    return results
end

function HEXA.on_action(event)
    local pid = event and event.PlayerID
    local results = HEXA.execute(pid, event and event.items)
    if not results then return end

    local msg = "HEXA: " .. table.concat(results, " | ")
    print(msg)

    -- эхо обратно в HUD: видно, что реально исполнилось, а что нет
    if pid and PlayerResource then
        local player = PlayerResource:GetPlayer(pid)
        if player then
            CustomGameEventManager:Send_ServerToPlayer(player, "hexa_echo", { text = msg })
        end
    end
end

-- Резервный канал: !hexa cast invoker_tornado — работает даже без HUD.
function HEXA.on_chat(event)
    local text = string.lower(event.text or "")
    local rest = string.match(text, "^!hexa%s+(.+)$")
    if not rest then return end
    local results = HEXA.execute(event.playerid, rest)
    if results then print("HEXA(chat): " .. table.concat(results, " | ")) end
end

-- Клиент шлёт этот тик, мы отвечаем игровым временем: у Panorama нет своего доступа к часам.
function HEXA.on_tick(event)
    local pid = event and event.PlayerID
    if not pid then return end
    local player = PlayerResource:GetPlayer(pid)
    if not player then return end
    CustomGameEventManager:Send_ServerToPlayer(player, "hexa_state", {
        game_time = GameRules:GetGameTime(),
    })
end

function HEXA.Init()
    CustomGameEventManager:RegisterListener("hexa_action", HEXA.on_action)
    CustomGameEventManager:RegisterListener("hexa_tick", HEXA.on_tick)
    ListenToGameEvent("player_chat", HEXA.on_chat, nil)
end

return HEXA
