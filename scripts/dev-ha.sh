#!/bin/sh
# Local dev Home Assistant (Docker/Colima, port 8124) with the integration copied in and a mock switch on port 80.
#   scripts/dev-ha.sh start   start mock switch + HA container (creates it on first use)
#   scripts/dev-ha.sh sync    copy the integration into the dev config (restart HA after changes to manifest.json)
#   scripts/dev-ha.sh stop    stop both
# Mock switch password: devtest-pw-1, host to enter in HA: host.docker.internal
cd "$(dirname "$0")/.." || exit 1
ROOT="$(pwd -P)"   # real path: Docker bind mounts must not go through a symlink
sync_files() {
  mkdir -p dev-ha/config/custom_components
  rsync -a --delete --exclude __pycache__ custom_components/goalake_poe_switch dev-ha/config/custom_components/
}
case "$1" in
  start)
    sync_files
    [ -f dev-ha/config/configuration.yaml ] || printf 'default_config:\n\nlogger:\n  default: warning\n  logs:\n    custom_components.goalake_poe_switch: debug\n' > dev-ha/config/configuration.yaml
    (nohup python3 -I dev-sim/mock_switch.py --host 0.0.0.0 --port 80 --password devtest-pw-1 > dev-ha/mock.log 2>&1 &)
    docker start ha-goalake-dev 2>/dev/null || docker run -d --name ha-goalake-dev -p 127.0.0.1:8124:8123 \
      -v "$ROOT/dev-ha/config:/config" ghcr.io/home-assistant/home-assistant:2026.11.1
    echo "HA on http://127.0.0.1:8124" ;;
  sync) sync_files ;;
  stop)
    docker stop ha-goalake-dev
    pkill -f "dev-sim/mock_switch.py" ;;
  *) echo "usage: $0 start|sync|stop"; exit 2 ;;
esac
