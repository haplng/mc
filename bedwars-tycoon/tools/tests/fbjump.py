import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
b = join()
if sc('#state') != 3: print('start', start('tea', b)); time.sleep(1)
c('effect give tester minecraft:resistance infinite 4 true')
c('fill 596 90 -4 640 90 4 minecraft:stone'); c('fill 596 91 -4 640 99 4 minecraft:air'); c('tp tester 603.5 91 0.5 -90 0'); time.sleep(0.5)
print(c('give tester minecraft:carrot_on_a_stick[!minecraft:max_damage,!minecraft:damage,item_model="minecraft:fire_charge",max_stack_size=64,custom_data={bw:"fireball"}] 3')[:80])
def jump(dy, back, kb, label):
    c('kill @e[tag=lj]'); c('summon minecraft:mannequin 600.5 91 0.5 {Tags:["lj"],Rotation:[-90f,0f]}'); time.sleep(0.4)
    c(f'execute as @e[tag=lj] at @s rotated ~ 0 positioned ^ ^{dy} ^-{back} run summon minecraft:armor_stand ~ ~ ~ {{Marker:1b,Invisible:1b,NoGravity:1b,Tags:["lj2"],equipment:{{head:{{id:"minecraft:leather_helmet",count:1,components:{{"minecraft:enchantments":{{"bw:{kb}":1}}}}}}}}}}')
    time.sleep(0.07); c('kill @e[tag=lj2]'); time.sleep(0.05); m = c('data get entity @e[tag=lj,limit=1] Motion'); mm = re.findall(r'(-?[\d.]+(?:E-?\d+)?)d', m); ymax = 91
    for _ in range(14):
        time.sleep(0.25); p = pos('@e[tag=lj,limit=1]'); ymax = max(ymax, p[1]) if p else ymax
    print(f'{label}: motion ({float(mm[0]):.2f}, {float(mm[1]):.2f}) landed x {p[0] - 600.5:.1f} peak +{ymax - 91:.1f} hp', c('data get entity @e[tag=lj,limit=1] Health')[-6:])
jump(1.05, 1.2, 'push', 'dy1.05 back1.2'); jump(0.7, 1.3, 'push', 'dy0.7 back1.3'); jump(0.4, 1.4, 'push', 'dy0.4 back1.4'); jump(1.3, 1.0, 'push', 'dy1.3 back1.0')
# a normal fireball at the feet (fireball jump): blast_fb at the feet, slightly behind
jump(0.1, 0.8, 'blast_fb', 'blast_fb at feet back0.8'); jump(0.1, 0.3, 'blast_fb', 'blast_fb at feet back0.3')
b.close()
