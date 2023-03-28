'''
openai_chat model
Uses OpenAI's GPT Chat API to generate a response to the input json file.
'''

# Requirements:
# pip install openai

import openai
import json

# TODO: Add your OpenAI API key here
OPENAI_API_KEY = ""

class Model:
  def __init__(self,
    model_name = "gpt-3.5-turbo",
    temperature = 0.7,
    ):
    openai.api_key = OPENAI_API_KEY
    self.model_name = model_name
    self.temperature = temperature
  
  def predict(self, input_json):
    with open(input_json, "r") as f:
      input_text = f.read()
    input_json = json.loads(input_text)
    
    setup_prompt = f"""
You are a role-playing game character in the world of The Elder Scrolls III: Morrowind.

Respond in-character using descriptive language. Reply with only your dialogue, no description of your actions should be mentioned.

You are {input_json["actor"]}, a non-player character in Morrowind.

The player approaches your character and says, "{input_json["prompt"]}"
"""
    
    response = openai.ChatCompletion.create(
      model=self.model_name,
      temperature=self.temperature,
      messages = [
        {"role": "system", "content": "You are a role-playing game character in the world of The Elder Scrolls III: Morrowind."},
        {"role": "user", "content": setup_prompt},
      ])

    return response.choices[0]['message']['content']