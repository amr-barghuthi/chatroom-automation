#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_ROOT"

docker compose run --rm \
  --entrypoint python \
  -v "$BACKEND_ROOT:/app" \
  app \
  manage.py test be_automation.backend_tests "$@"