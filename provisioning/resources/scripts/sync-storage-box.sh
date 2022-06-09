#!/bin/bash

LOCAL_FOLDER="$1"
S3_BUCKET="$2"

echo "$(date) Syncing MECADOI storage box"

# Move all files from the FTP server to the local directory. --remove-source-files indicates to rsync that transferred
# files should be deleted from the source directory. It also handles the case where a file is downloaded while it is
# being uploaded. Per the documentation: "Starting with 3.1.0, rsync will skip the sender-side removal (and output an
# error) if the file's size or modify time has not stayed unchanged."
rsync --recursive --remove-source-files storage-box:ejp/ "${LOCAL_FOLDER}"

# Sync all files in the local folder to an S3 bucket for archival.
aws s3 sync "${LOCAL_FOLDER}" "s3://${S3_BUCKET}/ejp"
