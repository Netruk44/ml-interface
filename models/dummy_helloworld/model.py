'''
dummy_helloworld model
This model doesn't read the input json file, it just
returns a static string, "Hello, world!".
'''

# Requirements: None

class Model:
    def __init__(self):
        pass

    def predict(self, input_json):
        return "Hello, world!"
