#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

command=${1:-dev}

if [ ! -d node_modules ]; then
  npm install --include=optional
fi

case "$command" in
  dev)
    npm run dev
    ;;
  build)
    npm run build
    ;;
  preview)
    npm run preview
    ;;
  *)
    echo "Usage: ./run.sh [dev|build|preview]" >&2
    exit 1
    ;;
esac
