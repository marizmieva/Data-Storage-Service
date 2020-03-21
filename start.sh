#!/bin/bash

python3 A/server.py 5001 &
python3 AB/server.py 5002 &
python3 B/server.py 5003 &
python3 BA/server.py 5004 &
python3 middleware.py 5000 &

python3 client_dir/client.py 5005

wait