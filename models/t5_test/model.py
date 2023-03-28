'''
t5_test model
Executes Google's T5 model on the input json file and returns the output.
The model itself is one of the defaults provided by the transformers library.
It will likely have poor performance, but works as a test.
'''

from transformers import T5Tokenizer, T5ForConditionalGeneration

class Model:
  def __init__(self):
    self.tokenizer = T5Tokenizer.from_pretrained('t5-small', model_max_length=92)
    self.model = T5ForConditionalGeneration.from_pretrained('t5-small')
  
  def predict(self, input_json):
    with open(input_json, "r") as f:
      input_text = f.read()
    input_ids = self.tokenizer.encode(input_text, return_tensors="pt")
    outputs = self.model.generate(input_ids, max_length=92)
    return self.tokenizer.decode(outputs[0], skip_special_tokens=True)