# !/bin/bash

usage() { echo "Usage: $0 [-i <input folder>] [-o <output folder>] [-m <mapping file>] [-g <generator policy>] [-j <x3ml transform service endopoint>]" 1>&2; exit 1; }

while getopts ":i:o:m:g:j:" o; do
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
        j)
            SERVER_URL=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

process_file() {
    local file="$1"
    local output_file="$RECORDSOUTPUTFOLDER/$(basename "$file" .xml).ttl"
    echo
    if ! curl --silent -X POST "$SERVER_URL?mappingFile=$RECORDMAPPING&generatorPolicy=$GENERATOR&inputFile=$file&outputFile=$output_file"; then
        echo "Error: Failed to process file $file - Is the server running?" >&2
        exit 1
    fi
    echo
}

export -f process_file
export SERVER_URL
export RECORDSOUTPUTFOLDER
export RECORDMAPPING
export GENERATOR

for file in "$RECORDSINPUTFOLDER"/*.xml; do
    if [ -f "$file" ]; then
        process_file "$file"
    else
        echo "No XML files found in the directory."
        break
    fi
done