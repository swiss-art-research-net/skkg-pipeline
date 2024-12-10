# !/bin/bash

usage() { echo "Usage: $0 [-i <input folder>] [-o <output folder>] [-m <mapping file>] [-g <generator policy>] [-b <batch size>] [-j <java transform service endopoint>]" 1>&2; exit 1; }

while getopts ":i:o:m:g:b:j:" o; do
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
    echo curl -X POST "$SERVER_URL?mappingFile=$RECORDMAPPING&generatorPolicy=$GENERATOR&inputFile=$file&outputFile=$output_file"
    curl -X POST "$SERVER_URL?mappingFile=$RECORDMAPPING&generatorPolicy=$GENERATOR&inputFile=$file&outputFile=$output_file"
    echo
}

export -f process_file
export SERVER_URL
export RECORDSOUTPUTFOLDER
export RECORDMAPPING
export GENERATOR

# process a batch of files
process_batch() {
    batch=("$@")
    echo "Processing batch of ${#batch[@]} files:"
    for file in "${batch[@]}"; do
        process_file "$file"
    done
}

batch=()

for file in "$RECORDSINPUTFOLDER"/*.xml; do
    if [ -f "$file" ]; then
        batch+=("$file")

        # Process the batch if we reach the batch size
        if [ "${#batch[@]}" -eq "$BATCHSIZE" ]; then
            process_batch "${batch[@]}"
            batch=() # Reset the batch
        fi
    else
        echo "No XML files found in the directory."
        break
    fi
done

# Process any remaining files in the batch
if [ "${#batch[@]}" -gt 0 ]; then
    process_batch "${batch[@]}"
fi
