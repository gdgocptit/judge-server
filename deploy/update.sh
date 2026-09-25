#!/bin/bash
# Run as root on the existing VPS, with no active submissions.
set -euo pipefail
cd /srv/dmoj/judge-server
if [[ -n $(git status --porcelain) ]]; then
    echo 'Working tree has local changes; commit or save them before deploying.' >&2
    exit 1
fi
bash /srv/dmoj/backup.sh
git pull --ff-only origin master
git submodule update --init --recursive
revision=$(git rev-parse HEAD)
image="gdgocptit/judge-server:$revision"
docker build -f deploy/Dockerfile.vps --label "org.opencontainers.image.revision=$revision" -t "$image" .
docker run --rm --user judge --cap-add SYS_PTRACE --security-opt no-new-privileges:true \
    --memory 1200m --pids-limit 256 -v /etc/dmoj/judge1.yml:/judge.yml:ro \
    --entrypoint /env/bin/python "$image" /judge/deploy/check_beam.py
docker tag gdgocptit/judge-server:production gdgocptit/judge-server:previous
docker tag "$image" gdgocptit/judge-server:production
docker compose -f /srv/dmoj/compose.yml up -d --force-recreate
/srv/dmoj/venv/bin/python /srv/dmoj/smoke.py
echo "Judges deployed: $revision"
