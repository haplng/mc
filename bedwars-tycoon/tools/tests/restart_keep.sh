#!/bin/bash
# stop the server and start it again on the same world (as when a single-player world is closed and opened again)
cd /home/claude/mcsrv/run && python3 -c "
import sys; sys.path.insert(0, '/home/claude/mc/tools'); import rcon
try: r = rcon.Rcon(); r.cmd('stop')
except Exception as e: pass"
for i in $(seq 1 30); do pgrep -f "net.minecraft.server.Main" >/dev/null || break; sleep 1; done
rm -f world/session.lock logs/latest.log
(nohup /usr/lib/jvm/java-25-openjdk-amd64/bin/java -Xms1G -Xmx4G -cp "../game.jar:../lib/*" net.minecraft.server.Main --nogui > server.out 2>&1 &)
for i in $(seq 1 180); do grep -q "RCON running" logs/latest.log 2>/dev/null && break; sleep 0.5; done
sleep 2
grep -iE "error|exception|Failed to load|Unknown function|Incorrect argument|Couldn't parse|Couldn't load|Parsing error|Failed to parse|Errors in" logs/latest.log server.out | grep -v "minecraftservices\|Services are\|MinecraftClientException\|UnknownHost" | cut -c1-400 | head -12
echo "server up: $(grep -c 'Done (' logs/latest.log)"
