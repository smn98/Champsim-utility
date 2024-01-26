#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "Illegal number of parameters"
    echo "Usage: ./copy_to_server.sh [SERVER IP] [USER]"
    exit 1
fi

SERVER_IP=$1
USER=$2

echo "-----------------------------------------------------------" >> ~/backup.log 
echo `date` >> ~/backup.log 
rsync -av --del ~/secure_berti/Berti_Baseline/* ${USER}@${SERVER_IP}:~/secure_berti/Berti_Baseline >> ~/backup.log 
rsync -av --del ~/secure_berti/GhostMinion/* ${USER}@${SERVER_IP}:~/secure_berti/GhostMinion >> ~/backup.log 
rsync -av ~/secure_berti/results-${HOSTNAME}/* ${USER}@${SERVER_IP}:~/secure_berti/results-${HOSTNAME} >> ~/backup.log 
rsync -av ~/secure_berti/plots/* ${USER}@${SERVER_IP}:~/secure_berti/plots >> ~/backup.log 
