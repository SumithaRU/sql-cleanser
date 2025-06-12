#!/usr/bin/env bash
# Full re-verification & test pass script
set -e

echo "0. Install Python test dependencies"
python -m pip install --upgrade pip
python -m pip install -r src/backend/requirements.txt pytest

echo "1. Build frontend"
cd src/frontend
npm run build

echo "2. Run backend tests"
cd ../..
python -m pytest --maxfail=1 --disable-warnings -q

echo "3. Run demo local"
bash scripts/demo_local.sh

echo "All checks passed." 