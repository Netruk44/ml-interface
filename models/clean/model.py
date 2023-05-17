'''
clean model
Fake model. Deletes the virtualenv.
'''

# Requirements: None

import os
import sys

class Model:
    def __init__(self):
        pass

    def predict(self, input_json):
        # Remove the .venv directory relative to the home directory
        venv_dir = os.path.join(os.path.expanduser("~"), ".venv")
        openmwml_dir = os.path.join(venv_dir, "openmw_ml")
        print(f"Removing {openmwml_dir}")
        if os.path.exists(openmwml_dir):
            os.system(f"rm -rf {openmwml_dir}")

            # If the .venv directory is empty, remove it
            if len(os.listdir(venv_dir)) == 0:
                print(f"Removing {venv_dir} since it is empty")
                os.system(f"rm -rf {venv_dir}")
        else:
            print(f"WARNING: Directory does not exist.")
        return ""