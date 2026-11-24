#!/bin/bash
# The test server. 26.3 ships no obfuscation and its CLIENT jar holds the dedicated server too, so the launcher's files are enough:
#   /home/claude/mcsrv/game.jar   = .minecraft/versions/26.3/26.3.jar
#   /home/claude/mcsrv/lib/*.jar  = the jars named in versions/26.3/26.3.json from .minecraft/libraries (no lwjgl, no natives needed)
#   java 25 (apt: openjdk-25-jdk-headless)
# server.sh setup                 writes run/eula.txt and run/server.properties and makes the reports the fake player reads
# server.sh start <world> [zip]   fresh copy of a world folder, the pack zip put into it, server left running (rcon 25575, game 25565)
# server.sh again                 stop and start on the same world: what closing a single-player world and opening it again does
# server.sh stop
# Things that cost time: white-list is ON by default in 26.3; the bot needs offline mode and no compression; pause-when-empty must be off
# or nothing ticks while no fake player is connected.
export JAVA_TOOL_OPTIONS=
J=/usr/lib/jvm/java-25-openjdk-amd64/bin/java; S=/home/claude/mcsrv
mkdir -p $S/run; cd $S/run
stop() {
  python3 -c "
import sys; sys.path.insert(0, '/home/claude/mc/tools'); import rcon
try: rcon.Rcon().cmd('stop')
except Exception: pass" 2>/dev/null
  for i in $(seq 1 40); do pgrep -f "net.minecraft.server.Main" >/dev/null || break; sleep 1; done
  pkill -9 -f "net.minecraft.server.Main" 2>/dev/null; true
}
up() {
  rm -f world/session.lock logs/latest.log
  (nohup $J -Xms1G -Xmx4G -cp "../game.jar:../lib/*" net.minecraft.server.Main --nogui > server.out 2>&1 &)
  for i in $(seq 1 240); do grep -q "RCON running" logs/latest.log 2>/dev/null && break; sleep 0.5; done
  sleep 2
  grep -iE "error|exception|Failed to load|Unknown function|Incorrect argument|Couldn't parse|Couldn't load|Parsing error|Failed to parse|Errors in" logs/latest.log server.out | grep -v "minecraftservices\|Services are\|MinecraftClientException\|UnknownHost\|authserver\|sessionserver" | cut -c1-400 | head -12
  echo "server up: $(grep -c 'Done (' logs/latest.log)"
}
case "$1" in
  setup)
    echo "eula=true" > eula.txt
    printf '%s\n' online-mode=false white-list=false network-compression-threshold=-1 enable-rcon=true rcon.password=ekqatest rcon.port=25575 broadcast-rcon-to-ops=false \
      level-name=world server-port=25565 spawn-protection=0 allow-flight=true max-tick-time=-1 pause-when-empty-seconds=-1 view-distance=8 simulation-distance=11 \
      enforce-secure-profile=false sync-chunk-writes=false function-permission-level=2 difficulty=normal gamemode=creative > server.properties
    (cd $S && $J -Xmx2G -cp "game.jar:lib/*" net.minecraft.data.Main --reports --output reports/out > reports.log 2>&1; ls reports/out/reports | tr '\n' ' ')
    ln -sfn . $S/server; echo; echo "the fake player finds the packet ids with EK_ROOT=$S" ;;
  start) stop; rm -rf world; cp -r "$2" world; [ -n "$3" ] && cp "$3" world/datapacks/bedwars_maps.zip; up ;;
  again) stop; up ;;
  stop) stop; echo stopped ;;
  *) sed -n '2,12p' "$0" ;;
esac
