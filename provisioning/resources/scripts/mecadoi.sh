#!/bin/bash

# from https://stackoverflow.com/a/4346420
# abort the script if there is an error
set -e
# treat references to unset variables as errors
set -u
# treat any failure inside a pipeline as an error (bash-only)
set -o pipefail

batch_dir="{{ batch_dir }}"
code_dir="{{ code_dir }}"
logs_dir="{{ logs_dir }}"
recipient_email="thomas.eidens@embo.org"
sync_dir="{{ sync_dir }}"
s3_bucket_name="{{ s3_bucket_name }}"

# for debugging
# cmd_test() {
#     echo "Success! args: $@"
# }
# cmd_sleep() {
#     duration=$1
#     echo "Sleeping for ${duration} seconds..."
#     sleep "${duration}"
# }

cmd_sync() {
    echo "$(date) Syncing MECADOI storage box"
    # Move all files from the FTP server to the local directory. --remove-source-files indicates to rsync that transferred
    # files should be deleted from the source directory. It also handles the case where a file is downloaded while it is
    # being uploaded. Per the documentation: "Starting with 3.1.0, rsync will skip the sender-side removal (and output an
    # error) if the file's size or modify time has not stayed unchanged."
    rsync --recursive --remove-source-files storage-box:ejp/ "${sync_dir}"

    # Sync all files in the local folder to an S3 bucket for archival.
    aws s3 sync "${sync_dir}" "s3://${s3_bucket_name}/ejp"
}

_execute_batch_command() {
    command="$@"
    command_name="${1}"

    cd "${code_dir}"
    source .venv/bin/activate
    output_batch_command="$(python3 -m src.cli.main batch ${command})"
    cd -
    echo "python3 -m src.cli.main batch ${command}

${output_batch_command}" | mutt -s "[MECADOI] batch ${command_name}" -- "${recipient_email}"
    echo "${output_batch_command}"

    echo "$(date) Syncing MECADOI batch dir"
    aws s3 sync "${batch_dir}" "s3://${s3_bucket_name}/batch"
}

cmd_parse() {
    echo "$(date) Batch parse"
    _execute_batch_command parse -o "${batch_dir}" "${sync_dir}/RC"
}

cmd_deposit() {
    echo "$(date) Batch deposit"
    _execute_batch_command deposit -o "${batch_dir}" --after "$(date --date='last week' "+%F")" --dry-run
}

with_lock() {
    command="$@"

    lock_file="/var/lock/mecadoi"
    wait_for_lock_in_seconds=120
    (
        if ! flock --wait=${wait_for_lock_in_seconds} 9; then
            echo "Failed to acquire lock"
            exit 1
        fi
        cmd_${command}
    ) 9>"${lock_file}"
}

with_lock "$@"
