#!/bin/bash
set -e

# Set multiproc dir and create it
mkdir -p $PROMETHEUS_MULTIPROC_DIR

# Start the metrics server in the background
python /scripts/prometheusServer.py &

# Start the Java service
cd /scripts
exec java -Dfile.encoding=UTF-8 -Xms512m -Xmx1024m -cp /libs/x3ml-engine-exejar.jar:/java/bin X3MLEngineService