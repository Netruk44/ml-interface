#! /bin/bash

# This script is a short wrapper around a python script that
# generates text, intended for OpenMW but probably useful for
# other applications.

# Set the PYTHONPATH to the directory containing the libraries
# needed for execution
# By default, this folder is located alongside the script in a
# directory called pythonpath
export PYTHONPATH="$(dirname $0)/pythonpath"

# Call the python script
python3 "$(dirname $0)/ml-interface.py" "$@"