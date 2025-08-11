#!/bin/bash
mkdir -p /data/db
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
sleep 3
python scripts/seed_data.py
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
