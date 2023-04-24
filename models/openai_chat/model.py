'''
openai_chat model
Uses OpenAI's GPT Chat API to generate a response to the input json file.
'''

# Requirements:
# pip install openai
# os.environ["OPENAI_API_KEY"] needs to be set to your OpenAI API key

import openai
import json
import os
import random

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Instead of calling the api, return the content that would have been sent to the api
DEBUG = False

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

    # Actor faction description string
    optional_actor_faction_string = ''

    if input_json["actor_faction"]:
      optional_actor_faction_string = f' You are a member of the {input_json["actor_faction"]} faction.'

      rank = int(input_json["actor_faction_rank"])
      if rank > -1:
        if rank < 4:
          optional_actor_faction_string += ' You are a low-ranking member of your faction.'
        elif rank < 7:
          optional_actor_faction_string += ' You are a mid-ranking member of your faction. You expect to be treated with respect.'
        else:
          optional_actor_faction_string += ' You are a high-ranking, well-known and respected member of your faction. You are a leader and a role model to your peers.'

    # Player faction description string
    optional_player_faction_string = ''
    
    if 'player_factions' in input_json:
      # "player_factions": {
      #   "faction_name": 1,
      #   ...
      # Where '1' is the rank of the player in that faction from 1-10.

      optional_player_faction_string = ''

      if len(input_json["player_factions"]) > 0:
        # If there's only one faction, describe that one
        if len(input_json["player_factions"]) == 1:
          player_faction = next(iter(input_json["player_factions"].keys()))
        else:
          # Otherwise for now, only care about the highest rank faction.
          # TODO: Prioritize the faction that the actor is a member of.
          # Order the keys by their value:
          sorted_factions = sorted(input_json["player_factions"], key=input_json["player_factions"].get, reverse=True)
          # Get the first key:
          player_faction = sorted_factions[0]
      
        player_faction_rank = input_json["player_factions"][player_faction]

        optional_player_faction_string = f' The player is a member of the {player_faction} faction.'

        if player_faction_rank < 4:
          optional_player_faction_string += ' The player is a low-ranking member of their faction.'
        elif player_faction_rank < 7:
          optional_player_faction_string += ' The player is a mid-ranking member of their faction. Respect should be shown if you are a subordinate member of the same faction.'
        else:
          optional_player_faction_string += ' The player is a high-ranking member of their faction. You should show respect for their position.'
    
    # Optional interesting factoid about the actor
    optional_actor_factoid_string = ''

    # Does the actor have a reputation?
    # Reputation is a number from 0-150
    # For the player, each increase comes from completing a quest for someone.
    # NPCs have a predetermined reputation. Commoners are 0, guards are 6, Sellus Gravius is 12, etc.
    actor_reputation = int(input_json["actor_reputation"])
    if actor_reputation > 0:
      if actor_reputation < 5:
        optional_actor_factoid_string = " You're not very well-known. You've done a little bit of work for a few people, but nobody really knows who you are."
      elif actor_reputation < 10:
        optional_actor_factoid_string = " You've completed jobs for a few people in the past, and people are starting to know who you are."
      elif actor_reputation < 20:
        optional_actor_factoid_string = " You've started to build a name for yourself. In certain circles, you're becoming well-known."
      elif actor_reputation < 50:
        optional_actor_factoid_string = " People generally know who you are. You've had an impact on many people's lives."
      elif actor_reputation < 100:
        optional_actor_factoid_string = " You're a well-known and respected person. You've completed many tasks for a lot of people throughout your career, and they've talked about you a lot."
      else:
        optional_actor_factoid_string = " You're a legend. You've impacted countless people throughout your lifespan, and as a result everybody knows your name."
    else:
      optional_actor_factoid_string = " The character you're playing as doesn't have any reputation. Feel free to make up a simple backstory for them."

    # Optional interesting factoid about the player the actor may know about.
    optional_player_factoid_string = ''

    player_reputation = int(input_json["player_reputation"])
    player_bounty = int(input_json["player_bounty"])
    #player_is_werewolf = int(input_json["player_is_werewolf"])
    #player_werewolf_kills = int(input_json["player_werewolf_kills"])

    # Is the player famous enough to be recognized by this actor?
    # Generate a number 0-150, if the number is less than the player's reputation, then the actor knows the player.
    # Note: This will result in the ai model only sometimes knowing about the player, since it rolls separately for each message.
    if random.randint(0, 150) < player_reputation:
      if player_reputation < 10:
        optional_player_factoid_string = " You think you might have heard of the player's name before, but you don't know much about them."
      elif player_reputation < 50:
        optional_player_factoid_string = " You've heard of the player's name before and have heard rumors about their previous deeds."
      elif player_reputation < 100:
        optional_player_factoid_string = " The player is starting to become well-known throughout the land. Because they've helped so many people, they've been talked about a lot."
      else:
        optional_player_factoid_string = " The player is a household name. Most people know someone that the player has helped."
    # Does the player have a bounty?
    elif player_bounty > 0 and random.randint(0, 1000) < player_bounty:
      if player_bounty < 50:
        optional_player_factoid_string = " You've heard that the player has a small bounty for something minor like trespassing."
      elif player_bounty < 1000:
        optional_player_factoid_string = " You've heard that the player has a bounty for something serious like assault or pickpocketing."
      elif player_bounty < 5000:
        optional_player_factoid_string = " The player is a known criminal, likely a murderer. You know they are wanted by the authorities."
      else:
        optional_player_factoid_string = " The player is a known serial-killer, authority has made it known that the player should be fled from or killed on sight."

    # The setup prompt for the first 'chat' message.
    setup_prompt = f"""
You are a role-playing game character in the world of The Elder Scrolls III: Morrowind.

Respond in-character using descriptive language. Reply with only your dialogue, no description of your actions should be mentioned.

== Context ==
You are a character named "{input_json["actor"]}", you are a {input_json["actor_race"]} {input_json["actor_class"]}.{optional_actor_faction_string}{optional_actor_factoid_string}

The player is named "{input_json["player_name"]}", they are a {input_json["player_race"]} {input_json["player_class"]}.{optional_player_faction_string}{optional_player_factoid_string}

You and the player are located in "{input_json["location"]}". The player greets your character.
"""

    # The messages from the in-game conversation.
    existing_messages = [{
      "role": "assistant" if message["who"] == "actor" else "user",
      "content": message["text"]
    } for message in input_json["history"]]

    # The prompt that the player entered, to be answered by the AI.
    player_prompt = input_json["prompt"]

    # Add information about the actor's current disposition towards the player.
    # Scale from 1-100 to a 1-10 scale
    #   Theory: text model will be able to more easily intuit a single digit than a two digit number.
    #   Context: All the numbers from 1 up to like 500 are one single token to the model.
    #            It might be easier for the model to provide meaningful distinction between 10 different tokens than 100.
    player_prompt = f'[NOTE: Your current disposition towards the player is {int(input_json["actor_disposition"]) // 10} / 10.]\n\n{player_prompt}'
    
    # The messages sent to the API
    conversation = [
      {"role": "system", "content": "You are a role-playing game character in the world of The Elder Scrolls III: Morrowind."},
      {"role": "user", "content": setup_prompt},
      *existing_messages,
      {"role": "user", "content": player_prompt},
    ]

    if DEBUG:
      return json.dumps({
        "model": self.model_name,
        "temperature": self.temperature,
        "messages": conversation
      }, indent=2)

    response = openai.ChatCompletion.create(
      model=self.model_name,
      temperature=self.temperature,
      messages=conversation,
    )

    return response.choices[0]['message']['content']