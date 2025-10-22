#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://192.168.0.6:8001}"
TOK="${TOK:-dev-admin-token}"
curl -s "$BASE/healthz" | jq .
