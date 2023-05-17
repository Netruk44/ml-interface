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
        # Remove the .venv directory relative to this file
        venv_dir = os.path.join(os.path.dirname(__file__), '../../' , ".venv")
        print(f"Removing {venv_dir}")
        if os.path.exists(venv_dir):
            os.system(f"rm -rf {venv_dir}")
        else:
            print(f"WARNING: Directory does not exist.")
        return ""