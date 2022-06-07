#!/bin/bash

LOCAL_FOLDER="$1"
S3_BUCKET="$2"

echo "$(date) Syncing MECADOI storage box"
# use the checksum parameter to leave change time alone
rsync --checksum --recursive storage-box:ejp/ "${LOCAL_FOLDER}"
aws s3 sync "${LOCAL_FOLDER}" "s3://${S3_BUCKET}/ejp"
