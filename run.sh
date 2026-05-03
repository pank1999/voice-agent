#!/bin/bash

export $(grep -v '^#' .env | xargs)

uvicorn app.main:app --reload