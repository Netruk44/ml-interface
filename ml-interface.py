'''
ml-interface.py

This program acts as an interface between games and text-generating
models.

Usage: ml-interface.py <model_name> <input_json>

The input json should be a path to an input json file. The details
of that json file are left up to the specific model to interpret.

Model output will be written to stdout.
'''
import sys

def main():
    if len(sys.argv) == 1:
        print("Usage: ml-interface.py <model_name> <input_json>")
        sys.exit(1)

    model_name = sys.argv[1]
    # Override hack
    #model_name = "dummy_readjson"
    input_json = sys.argv[2] if len(sys.argv) > 2 else ''

    # Import the model
    # Models are available under models.model_name (if it exists)
    # First, check to make sure the specified model is valid
    try:
        model_module = __import__("models." + model_name, fromlist=["model"])
    except ImportError as e:
        print("Error: model {} not found".format(model_name))
        print(e)
        sys.exit(1)

    # Create an instance of the model
    model = model_module.model.Model()

    # Run the model
    output = model.predict(input_json)

    # Write the output to stdout
    print(output)

if __name__ == "__main__":
    main()