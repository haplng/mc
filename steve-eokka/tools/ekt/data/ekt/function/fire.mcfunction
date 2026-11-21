scoreboard players set #arm ekt 2
scoreboard players set #cap ekt 0
scoreboard players set #energy ek 100
scoreboard players set #tier ek -1
execute unless entity @e[tag=ek.cur] run summon minecraft:marker 0.5 60 0.5 {Tags:["ek.cur"]}
function ekt:place with storage ekt:s a
scoreboard players set #cur ek 1
function ekt:try with storage ekt:s a
scoreboard players operation #fired_at ekt = #now ekt
