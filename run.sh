#!/bin/bash
# Run script for NIST SP 800-22 Analyzer

# Get the script's directory path
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run using the python executable inside the virtual environment
"$DIR/venv/bin/python" "$DIR/gui.py"
