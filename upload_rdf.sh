#!/bin/bash

# Variables
SPARQL_ENDPOINT="http://192.168.178.34:9999/bigdata/namespace/big_dataset/sparql"
CONTENT_TYPE="application/n-triples"
PARTS_DIR="/Users/berke/PycharmProjects/AISysProj-1.4/"

# Loop through each part file
for part in ${PARTS_DIR}*.part*; do
    echo "Uploading $part..."
    curl -X POST "$SPARQL_ENDPOINT" \
         -H "Content-Type: $CONTENT_TYPE" \
         --data-binary "@$part"
    echo "Uploaded $part"
done