#!/bin/sh
# Pull the latest OpenPushups and restart the container if anything changed.
# Workout data lives in ./data (gitignored) and is never touched by updates.
set -e
cd "$(dirname "$0")"
old=$(git rev-parse HEAD)
git pull --ff-only --quiet
[ "$old" = "$(git rev-parse HEAD)" ] && exit 0
docker compose up -d --force-recreate
