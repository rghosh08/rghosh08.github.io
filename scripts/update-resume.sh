#!/usr/bin/env bash
# Compile resume/resume.tex and stage the served PDF (public/resume_rajat-ghosh.pdf).
# Usage: scripts/update-resume.sh            — compile from source (requires tectonic)
#        scripts/update-resume.sh <pdf>      — skip compilation, use a pre-built PDF
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$repo_root/public/resume_rajat-ghosh.pdf"

if [ $# -ge 1 ]; then
  src="$1"
else
  command -v tectonic >/dev/null || {
    echo "error: tectonic not found (brew install tectonic), or pass a pre-built PDF" >&2
    exit 1
  }
  tectonic "$repo_root/resume/resume.tex"
  src="$repo_root/resume/resume.pdf"
fi

if [ ! -f "$src" ]; then
  echo "error: $src not found" >&2
  exit 1
fi
if [ "$(head -c 4 "$src")" != "%PDF" ]; then
  echo "error: $src is not a PDF" >&2
  exit 1
fi

cp "$src" "$dest"
git -C "$repo_root" add "$dest" resume/resume.tex
echo "Staged public/resume_rajat-ghosh.pdf and resume/resume.tex."
echo "Commit with a descriptive message so git history reads as a changelog:"
echo '  git commit -m "Resume: <what changed>, <Month Year>"'
