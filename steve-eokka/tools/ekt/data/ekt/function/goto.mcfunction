function ek:lobby/enter
function ek:game/start_n
$scoreboard players set #stage ek $(prev)
execute if score #stage ek matches 1.. run function ek:game/stage_clear
execute if score #stage ek matches 0 run scoreboard players set #stage ek 1
