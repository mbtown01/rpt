#!/bin/bash -x

if [[ $(uname -a) =~ "^Darwin" ]]; then 
    alias realpath=grealpath 
fi
RPT_HOME="$(realpath $(dirname $0)/../)"
source ${RPT_HOME}/scripts/setenv.sh

RPT_RUN_USER=pi
RPT_RUN_HOSTNAME=pi-dev
RPT_RUN_IPADDR=192.168.8.187
RPT_RUN_PORT=3000
RPT_RUN_ENTRYPOINT=src/web.py

# Shutdown any previously running interpreters
ssh ${RPT_RUN_USER}@${RPT_RUN_HOSTNAME} killall python3

# Sync the project and execute
rsync -avz "${RPT_HOME}/src" "${RPT_RUN_USER}@${RPT_RUN_HOSTNAME}:rpt"
ssh ${RPT_RUN_USER}@${RPT_RUN_HOSTNAME} python3 -m ptvsd \
    --host ${RPT_RUN_IPADDR} --port ${RPT_RUN_PORT} --wait \
    "rpt/${RPT_RUN_ENTRYPOINT}"
