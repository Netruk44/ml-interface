#! /bin/bash

VENV_NAME=openmw_ml
VENV_DIR="$HOME/.venv/$VENV_NAME"
REQUIREMENTS_FILE="$(dirname "$0")/requirements.txt"

# Check if 'init' or 'clean' was passed as an argument
if [ "$1" == "init" ] || [ ! -d "$VENV_DIR" ]; then
    
    # Check if the venv already exists
    if [ -d "$VENV_DIR" ]; then
        echo "ERROR: Virtual environment already exists."
        exit 1
    fi

    echo "Initializing virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "Installing requirements..."
    pip install -r "$REQUIREMENTS_FILE"
    deactivate
    echo "Init completed, ready to run models."
    exit 0
elif [ "$1" == "clean" ]; then
    echo "Cleaning virtual environment..."
    rm -rf "$VENV_DIR"
    exit 0
fi

# Activate the venv and start the interface script
source "$VENV_DIR/bin/activate"
python3 "$(dirname "$0")/ml-interface.py" "$@"
deactivate