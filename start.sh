#!/bin/bash

python3 server.py A 5001 &
python3 server.py B 5002 &
python3 server.py C 5003 &
python3 server.py D 5004 &
python3 middleware.py 5001 5002 5003 5004 5000 &

python3 client.py 5000

wait