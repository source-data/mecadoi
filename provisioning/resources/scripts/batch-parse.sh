#!/bin/bash

code_folder="${1}"
input_folder="${2}/RC"
output_folder="${3}"

recipient_email="thomas.eidens@embo.org"

cd "${code_folder}"
source .venv/bin/activate
output_batch_parse="$(python3 -m src.cli.main batch parse -o "${output_folder}" "${input_folder}")"

echo "${output_batch_parse}" | mutt -s "[MECADOI] batch parsing" -- "${recipient_email}"
echo "${output_batch_parse}"
