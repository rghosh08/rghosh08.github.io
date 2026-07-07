#!/usr/bin/env bash
# Replace the served resume PDF with a freshly exported one and stage it.
# Usage: scripts/update-resume.sh [path-to-new-pdf]   (default: ~/Downloads/resume.pdf)
set -euo pipefail

src="${1:-$HOME/Downloads/resume.pdf}"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$repo_root/public/resume_rajat-ghosh.pdf"

if [ ! -f "$src" ]; then
  echo "error: $src not found" >&2
  exit 1
fi
if [ "$(head -c 4 "$src")" != "%PDF" ]; then
  echo "error: $src is not a PDF" >&2
  exit 1
fi

cp "$src" "$dest"
git -C "$repo_root" add "$dest"

echo "Staged public/resume_rajat-ghosh.pdf (from $src)."
echo "Commit with a descriptive message so git history reads as a changelog:"
echo '  git commit -m "Resume: <what changed>, <Month Year>"'
