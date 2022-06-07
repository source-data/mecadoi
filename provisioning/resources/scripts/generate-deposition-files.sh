#!/bin/bash

code_folder="${1}"
input_folder="${2}"
output_folder="${3}"
s3_bucket="${4}"
log_folder="${5}"

recipient_email="thomas.eidens@embo.org"

cd "${code_folder}"
source .venv/bin/activate
output_batch_run="$(python3 -m src.cli.main batch deposit --dry-run -o "${output_folder}" "${input_folder}/RC")"
echo "${output_batch_run}" >> "${log_folder}/batch-deposit-results.log"
echo "${output_batch_run}" | mutt -s "[MECADOI] batch deposit run" -- "${recipient_email}"
aws s3 sync "${output_folder}" "s3://${s3_bucket}/depositions"
