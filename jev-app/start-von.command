#!/bin/zsh
# Double-click this file in Finder to run the Von Semantic Router for a session.
# It starts the Von decision model (von serve) and the local app server
# (router.py), then opens the page. Closing the Terminal window stops both.
#
# Von is looked for at VON_BIN, then ~/.venvs/von/bin/von, then on PATH.
# Install it once with:
#   uv venv --python 3.12 ~/.venvs/von
#   uv pip install --python ~/.venvs/von/bin/python "von-sdk>=1.3.7"
set -u
cd "$(dirname "$0")" || exit 1
VON_URL=${VON_BASE_URL:-http://127.0.0.1:8000}
ROUTER_PORT=${ROUTER_PORT:-8766}
VON=${VON_BIN:-$HOME/.venvs/von/bin/von}
[ -x "$VON" ] || VON=$(command -v von || true)
up() { curl -s -m 2 -o /dev/null "$1/health"; }
export VON_BASE_URL=$VON_URL

pids=()
cleanup() { [ ${#pids[@]} -gt 0 ] && kill "${pids[@]}" 2>/dev/null; }
trap cleanup EXIT INT TERM HUP

if up "$VON_URL"; then
  echo "Von is already running at $VON_URL"
elif [ -z "$VON" ]; then
  echo "Von is not installed. See the comment at the top of this file."; read -r "?Press Enter to close"; exit 1
else
  host=${${VON_URL#*://}%%:*}; port=${${VON_URL##*:}%%/*}
  echo "Starting Von at $VON_URL (the first start downloads about 3 GB of weights)…"
  "$VON" serve --host "$host" --port "$port" & pids+=($!)
fi

if curl -s -m 2 -o /dev/null "http://127.0.0.1:$ROUTER_PORT/api/config"; then
  echo "The router is already running at http://127.0.0.1:$ROUTER_PORT"
else
  python3 router.py --port "$ROUTER_PORT" & pids+=($!)
fi

for _ in {1..300}; do up "$VON_URL" && break; sleep 1; done
up "$VON_URL" && echo "Von is up." || echo "Von is still starting; the page's status line will update when it is ready."
open "http://127.0.0.1:$ROUTER_PORT/"
echo "Close this window to stop the session."
wait
