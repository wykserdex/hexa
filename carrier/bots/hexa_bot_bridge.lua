-- HEXA · бот-мост для бот-матчей (песочница без живых людей).
--
-- Как работает: человек пишет в чат команду вида `!hexa combo` — бот исполняет
-- последовательность официальным Bot API. Никаких внешних процессов и инъекций:
-- это скрипт бота внутри игры, ровно как OpenHyperAI или Ranked Matchmaking AI.
--
-- Куда положить: <Steam>/steamapps/common/dota 2 beta/game/dota/scripts/vscripts/bots/
-- Проверить в игре: доступность ListenToGameEvent и GetBot() в контексте вашей
-- версии бот-скриптов (список функций — официальная документация Valve Bot Scripting).

local HEXA_BOT = {}

local SEQUENCES = {
    combo = {
        { delay = 0.0, ability = "invoker_tornado" },
        { delay = 0.9, ability = "invoker_emp" },
        { delay = 1.1, ability = "invoker_chaos_meteor" },
        { delay = 2.6, ability = "invoker_deafening_blast" },
    },
}

local function bot_has_ability(bot, name)
    for i = 0, 23 do
        local ability = bot:GetAbilityInSlot(i)
        if ability and ability:GetName() == name then return ability end
    end
    return nil
end

function HEXA_BOT.run_sequence(ability_names)
    local bot = GetBot()
    if not bot then return end
    for _, entry in ipairs(ability_names) do
        local ability = bot_has_ability(bot, entry.ability)
        if ability and ability:IsFullyCastable() then
            bot:Action_UseAbility(ability)
        end
    end
end

-- Простой подход: без таймеров внутри бота — окна держит HEXA (модуль sandbox_combo),
-- а бот получает уже готовую последовательность командой из чата.
function HEXA_BOT.on_chat(event)
    local text = string.lower(event.text or "")
    local command = string.match(text, "^!hexa%s+(%S+)")
    if not command then return end

    local bot = GetBot()
    if not bot then return end

    if command == "combo" then
        local sequence = SEQUENCES.combo
        bot:ActionImmediate_Chat("HEXA: выполняю комбо", false)
        HEXA_BOT.run_sequence(sequence)
    elseif command == "timer" then
        local seconds = tonumber(string.match(text, "^!hexa%s+timer%s+(%d+)")) or 180
        bot:ActionImmediate_Chat("HEXA: отметка " .. seconds .. " с", false)
    else
        bot:ActionImmediate_Chat("HEXA: неизвестная команда — combo, timer", false)
    end
end

function HEXA_BOT.Init()
    ListenToGameEvent("player_chat", HEXA_BOT.on_chat, nil)
end

return HEXA_BOT
