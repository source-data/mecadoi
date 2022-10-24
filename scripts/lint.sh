#!/bin/bash

# If any command fails, exit immediately with that command's exit status
set -eo pipefail

# use a bash array to pass multiple dirs as arguments
source_dirs=("./mecadoi" "./tests")

flake8 "${source_dirs[@]}"
echo "flake8 passed!"

black --check "${source_dirs[@]}"
echo "black passed!"

mypy "${source_dirs[@]}"
echo "mypy passed!"
