#!/bin/bash

usage() { echo "Usage: $0 [-i <input folder>] [-o <output folder>] [-m <mapping file>] [-g <generator policy>] [-b <batch size>]" 1>&2; exit 1; }

while getopts ":i:o:m:g:b:" o; do
    case "${o}" in
        i)
            RECORDSINPUTFOLDER=${OPTARG}
            ;;
        o)
            RECORDSOUTPUTFOLDER=${OPTARG}
            ;;
        m)
            RECORDMAPPING=${OPTARG}
            ;;
        g)
            GENERATOR=${OPTARG}
            ;;
        b)
            BATCHSIZE=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

echo "Mapping Records"
numfiles=$(find $RECORDSINPUTFOLDER -type f -name '*.xml' | wc -l)
count=1
echo "Found $numfiles record XML files in $RECORDSINPUTFOLDER"


# Calculate the number of batches
numbatches=$((numfiles / BATCHSIZE))
if ((numfiles % BATCHSIZE != 0)); then
    numbatches=$((numbatches + 1))
fi

# Loop through the files in batches
for ((batch=1; batch<=numbatches; batch++)); do
    echo "Processing batch $batch of $numbatches"
    (
    start=$(( (batch - 1) * BATCHSIZE + 1 ))
    end=$(( batch * BATCHSIZE ))
    if ((end > numfiles)); then
        end=$numfiles
    fi
    for ((i=start; i<=end; i++)); do
        f=$(find $RECORDSINPUTFOLDER -type f -name '*.xml' | sed -n "${i}p")
        echo "Mapping record $i of $numfiles ($f)"
        o=${f/.xml/.ttl}
        o=${o/$RECORDSINPUTFOLDER/}
        java -jar /x3ml/x3ml-engine.exejar \
            --input $f \
            --x3ml $RECORDMAPPING \
            --policy $GENERATOR \
            --output $RECORDSOUTPUTFOLDER/$o \
            --format text/turtle
    done
    ) &
done
wait