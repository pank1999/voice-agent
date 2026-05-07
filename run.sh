#!/bin/bash

set -a
source .env 2>/dev/null || true
set +a

source venv/bin/activate
uvicorn app.main:app --reload