'''
dummy_readjson model
This model reads the input json file and returns the contents.
'''

# Requirements: None

class Model:
    def __init__(self):
        pass

    def predict(self, input_json):
        with open(input_json, "r") as f:
            return f.read()