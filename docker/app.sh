#!/bin/bash

alembic upgrade head

cd src

gunicorn main:app --bind=0.0.0.0:8000