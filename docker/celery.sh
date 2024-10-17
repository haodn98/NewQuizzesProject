#!/bin/bash

cd src

celery --app=core.celery:celery worker -B -l INFO