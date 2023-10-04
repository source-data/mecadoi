#!/bin/bash

# If any command fails, exit immediately with that command's exit status
set -eo pipefail

ENV_FILE=.env.ci python -m unittest $@
