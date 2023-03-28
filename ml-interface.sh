#! /bin/bash

#Use conda run to start the interface script
CONDA_ENV_NAME=openmw_ml
conda run -n $CONDA_ENV_NAME python3 "$(dirname $0)/ml-interface.py" "$@"