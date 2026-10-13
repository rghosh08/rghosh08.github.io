# Von decision server (https://huggingface.co/wfzyx/von) for the Semantic Router
# page at https://rajatghosh.me/jev-router.html. The upstream CPU image runs
# `von serve` with OpenVINO; Spaces route traffic to app_port from README.md.
FROM ghcr.io/wfzyx/von:cpu
CMD ["--host", "0.0.0.0", "--port", "7860"]
