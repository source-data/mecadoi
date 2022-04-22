#!/bin/bash

folder="${1}"
recipient_email="thomas.eidens@embo.org"
# Set the ctime cutoff to the given value, or to "within the last day" if not given.
cutoff="${3:-"-1"}"

new_files=$(find "${folder}" -ctime "${cutoff}" -type f)

if [[ -n "${new_files}" ]]; then
    echo "${new_files}" | mutt -s "[MECADOI] new files from FTP box" -- "${recipient_email}"
fi