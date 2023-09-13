#! /bin/bash

cd /home/example/icad_tr_uploader
python3 tr_uploader.py ${1} ${2}
status=$?

# Exit with 0 status, even if there is an error.
if [ $status -ne 0 ]; then
    echo "Error with python script, exit status: $status"
    exit 0
else
    exit 0
fi