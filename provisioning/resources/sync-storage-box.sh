#!/bin/bash

LOCAL_FOLDER="$1"
S3_BUCKET="$2"

echo "$(date) Syncing MECADOI storage box"
rsync --recursive storage-box:ejp/ "${LOCAL_FOLDER}"
aws s3 sync "${LOCAL_FOLDER}" "s3://${S3_BUCKET}/ejp"
