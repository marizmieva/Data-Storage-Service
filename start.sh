#!/bin/bash

python3 server.py A 5005 &
python3 server.py B 5006 &
python3 server.py C 5007 &
python3 server.py D 5008 &
python3 middleware.py 5005 5006 5007 5008 1000 &

python3 client.py 1000

wait