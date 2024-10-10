#!/bin/bash

alembic upgrade head

cd src

gunicorn -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:8000