#!/bin/sh
# Create (or update) the public Hugging Face Space that runs Von for the
# Semantic Router page, then wait until it is running. Needs a Hugging Face
# login (hf auth login) and the huggingface_hub package; the Von venv has it.
#
#   sh jev-app/von-space/deploy.sh             # Space rghosh8/von -> https://rghosh8-von.hf.space
#   SPACE=you/von sh jev-app/von-space/deploy.sh
set -eu
cd "$(dirname "$0")"
SPACE=${SPACE:-rghosh8/von}
PY=${PY:-$HOME/.venvs/von/bin/python}
[ -x "$PY" ] || PY=python3
"$PY" - "$SPACE" <<'PYEOF'
import sys, time
from huggingface_hub import HfApi
repo = sys.argv[1]
api = HfApi()
print("space:", api.create_repo(repo, repo_type="space", space_sdk="docker", private=False, exist_ok=True))
api.upload_folder(folder_path=".", repo_id=repo, repo_type="space", allow_patterns=["Dockerfile", "README.md"],
                  commit_message="Run von serve from the upstream CPU image")
host = "https://" + repo.replace("/", "-").replace("_", "-").lower() + ".hf.space"
for _ in range(120):
    stage = api.get_space_runtime(repo).stage
    print("stage:", stage)
    if stage == "RUNNING":
        break
    if stage in ("BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"):
        sys.exit(f"Space failed: {stage}; see https://huggingface.co/spaces/{repo}")
    time.sleep(10)
print("Von server:", host)
print("Health:", host + "/health")
PYEOF
