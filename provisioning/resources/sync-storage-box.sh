#!/bin/bash

DEST="$1"

echo "$(date) Syncing MECADOI storage box"
rsync --recursive storage-box:ejp/ "${DEST}"
