#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
plugin_dir="${MUSESCORE_PLUGIN_DIR:-$HOME/Documents/MuseScore4/Plugins}"
mkdir -p "$plugin_dir"
cp "$repo_dir/plugins/musescore-mcp-websocket.qml" "$plugin_dir/musescore-mcp-websocket.qml"
printf 'Installed MuseScore plugin to %s\n' "$plugin_dir/musescore-mcp-websocket.qml"
printf 'Open MuseScore, open a score, then choose Plugins > musescore-mcp-websocket.\n'
