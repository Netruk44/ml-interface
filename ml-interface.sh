#! /bin/bash

VENV_NAME=openmw_ml
VENV_DIR="$(dirname "$0")/.venv/$VENV_NAME"
REQUIREMENTS_FILE="$(dirname "$0")/requirements.txt"

# Check if the venv exists, and create it if it doesn't
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "Installing requirements..."
    pip install -r "$REQUIREMENTS_FILE"
    deactivate
fi

# Activate the venv and start the interface script
source "$VENV_DIR/bin/activate"
python3 "$(dirname "$0")/ml-interface.py" "$@"
deactivate