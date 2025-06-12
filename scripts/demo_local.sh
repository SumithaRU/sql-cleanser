#!/usr/bin/env bash
# Dev-only demo: runs on local sample data
set -e

python src/backend/compare_utils.py \
  --base sample-input-scripts/base \
  --oracle sample-input-scripts/oracle \
  --out results/demo 