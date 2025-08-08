#!/bin/bash
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
