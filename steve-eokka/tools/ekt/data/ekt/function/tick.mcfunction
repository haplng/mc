scoreboard players add #now ekt 1
execute if score #arm ekt matches 1 if score #state ek matches 1 if score #intr ek matches 0 if score #steve ek matches 1 if score #beat ek = #beat ekt if score #phase ek = #phase ekt if score #idle ek matches 0 run function ekt:fire
execute if score #arm ekt matches 2 if score #cap ekt matches 0 unless score #drop ek matches 1 run function ekt:capture
execute if score #arm ekt matches 2 if score #cap ekt matches 1 if score #intr ek matches 0 unless score #drop ek matches 1 run function ekt:ended
