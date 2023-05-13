'''
openai_chat model
Uses OpenAI's GPT Chat API to generate a response to the input json file.
'''

# Requirements:
# pip install openai
# os.environ["OPENAI_API_KEY"] needs to be set to your OpenAI API key

# Optional:
# pip install azure-storage-queue    # Message Tracing
# os.environ["TRACING_ENDPOINT"]     # Message Tracing - needs to be set to your Azure Storage Queue Connection String

import openai
import json
import os
import random

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Debug mode
# Instead of calling the api, return the content that would have been sent to the api
DEBUG = False

# Message tracing
# Send input json, output json, and the response from the api to an Azure Storage Queue
# Set this to your Azure Storage Connection String, needs Queue Add permissions only.
# If you would like to help me out with generating data, send me an e-mail at somethingelse@danieltperry.me and I can give you my SAS token.
TRACING_ENDPOINT = os.environ.get("TRACING_ENDPOINT")

TRACING = TRACING_ENDPOINT != ""
#TRACING = False

if TRACING:
  from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy
  import gzip
  queue_name = "openmw-messages"


class Model:
  def __init__(self,
    model_name = "gpt-3.5-turbo",
    temperature = 0.85, # Default: 0.7, which makes most NPCs sound like the same person with a different background.
    ):
    openai.api_key = OPENAI_API_KEY
    self.model_name = model_name
    self.temperature = temperature

    if TRACING:
      self.queue_client = QueueClient.from_connection_string(TRACING_ENDPOINT, queue_name=queue_name)
      self.queue_client.message_encode_policy = BinaryBase64EncodePolicy()
  
  def predict(self, input_json):
    with open(input_json, "r") as f:
      input_text = f.read()
    input_json = json.loads(input_text)

    # Actor faction description string
    optional_actor_faction_string = ''

    if input_json["actor_faction"]:
      optional_actor_faction_string = f' You are a member of the "{input_json["actor_faction"]}".'

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
      
        player_faction_rank = int(input_json["player_factions"][player_faction])

        optional_player_faction_string = f' The player is a member of the "{player_faction}".'

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

    # Description of the actor's state (health, magic, fatigue)
    actor_level = int(input_json["actor_level"])
    actor_current_health = float(input_json["actor_current_health"])
    actor_current_magicka = float(input_json["actor_current_magicka"])
    actor_current_fatigue = float(input_json["actor_current_fatigue"])
    actor_max_health = float(input_json["actor_max_health"])
    actor_max_magicka = float(input_json["actor_max_magicka"])
    actor_max_fatigue = float(input_json["actor_max_fatigue"])
    actor_health_percentage = actor_current_health / actor_max_health
    actor_magicka_percentage = actor_current_magicka / actor_max_magicka
    actor_fatigue_percentage = actor_current_fatigue / actor_max_fatigue
    
    actor_state_string = ''
    actor_in_good_health = True

    if actor_health_percentage > 0.5 and actor_magicka_percentage > 0.5 and actor_fatigue_percentage > 0.5:
      actor_state_string = "You are in good health."
    else: # At least one stat is below 50%
      actor_in_good_health = False
      # Build up description, then wrap it in 'You are <description>.'
      if actor_health_percentage < 0.5:
        if actor_health_percentage < 0.25:
          actor_state_string += 'severely injured'
        else:
          actor_state_string += 'injured'
      if actor_magicka_percentage < 0.5:
        if actor_state_string != '':
          actor_state_string += ', '
        actor_state_string += 'low on magicka'
      if actor_fatigue_percentage < 0.5:
        if actor_state_string != '':
          actor_state_string += ', and '
        if actor_fatigue_percentage < 0.25:
          actor_state_string += 'completely exhausted'
        else:
          actor_state_string += 'slightly worn-out'
      

      actor_state_string = f'You are {actor_state_string}.'

    if actor_level < 5:
      actor_state_string += ' You are inexperienced when it comes to combat.'
    elif actor_level > 20:
      actor_state_string += ' You are a veteran when it comes to combat.'

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
        optional_player_factoid_string = f" There's a rumor that someone named \"{input_json['player_name']}\" has a small bounty for something minor like trespassing."
      elif player_bounty < 1000:
        optional_player_factoid_string = f" {input_json['player_name']} has a bounty for something serious like assault or pickpocketing."
      elif player_bounty < 5000:
        optional_player_factoid_string = f" {input_json['player_name']} is a known criminal, likely a murderer. You know they are wanted by the authorities."
      else:
        optional_player_factoid_string = f" {input_json['player_name']} is a known serial-killer, authority has made it known that the player should be fled from or killed on sight."
    
    # Description of player's state
    player_level = int(input_json["player_level"])
    player_current_health = float(input_json["player_current_health"])
    player_current_magicka = float(input_json["player_current_magicka"])
    player_current_fatigue = float(input_json["player_current_fatigue"])
    player_max_health = float(input_json["player_max_health"])
    player_max_magicka = float(input_json["player_max_magicka"])
    player_max_fatigue = float(input_json["player_max_fatigue"])
    player_health_percentage = player_current_health / player_max_health
    player_magicka_percentage = player_current_magicka / player_max_magicka
    player_fatigue_percentage = player_current_fatigue / player_max_fatigue
    
    player_state_string = ''
    player_in_good_health = True

    if player_health_percentage > 0.5 and player_magicka_percentage > 0.5 and player_fatigue_percentage > 0.5:
      also_string = ' also' if actor_in_good_health else ''
      player_state_string = f"The player is{also_string} in good health."
    else: # At least one stat is below 50%
      player_in_good_health = False
      # Build up description, then wrap it in 'The player looks <description>.'
      if player_health_percentage < 0.5:
        if player_health_percentage < 0.25:
          player_state_string += 'severely injured, with open wounds visible'
        else:
          player_state_string += 'injured, bleeding slightly'
      if player_magicka_percentage < 0.5:
        if player_state_string != '':
          player_state_string += ', '
        player_state_string += 'drained from magicka use'
      if player_fatigue_percentage < 0.5:
        if player_state_string != '':
          player_state_string += ', and '
        if player_fatigue_percentage < 0.25:
          player_state_string += 'completely exhausted, gasping for breath'
        else:
          player_state_string += 'slightly worn-out, breathing hard'
      
      player_state_string = f'The player seems to be {player_state_string}.'
    
    if player_level < 5:
      player_state_string += ' The player looks inexperienced and fresh-faced.'
    elif player_level > 20:
      player_state_string += ' The player looks like a veteran, with many scars and a hardened expression.'

    # Describe the player's relative strength (using HP for reference)
    relative_strength_string = 'In terms of physical strength, if you were to fight, '
    strength_advantage = 0 # + = player, 0 = even, - = actor

    if not player_in_good_health or not actor_in_good_health:
      relative_strength_string += 'assuming both of you were in perfect condition, '
    
    if player_max_health > actor_max_health * 1.25:
      strength_advantage = 1
      if player_max_health > actor_max_health * 1.5:
        strength_advantage = 2
    elif player_max_health < actor_max_health * 0.75:
      strength_advantage = -1
      if player_max_health < actor_max_health * 0.5:
        strength_advantage = -2

    if strength_advantage == 2:
      relative_strength_string += 'you think the player would significantly overpower you.'
    elif strength_advantage == 1:
      relative_strength_string += 'you think you would be at a disadvantage.'
    elif strength_advantage == 0:
      relative_strength_string += 'you think you would be evenly matched.'
    elif strength_advantage == -1:
      relative_strength_string += 'you think you would have the advantage.'
    elif strength_advantage == -2:
      relative_strength_string += 'you think you could easily overpower the player.'
    
    both_are_physically_weak = player_max_health < 100.0 and actor_max_health < 100.0 and strength_advantage != 0
    if both_are_physically_weak:
      relative_strength_string += " But neither of you look very strong."
    
    # Describe the player's relative magical strength
    magic_advantage = 0 # + = player, 0 = even, - = actor

    if player_max_magicka > actor_max_magicka * 1.25:
      magic_advantage = 1
      if player_max_magicka > actor_max_magicka * 1.5:
        magic_advantage = 2
    elif player_max_magicka < actor_max_magicka * 0.75:
      magic_advantage = -1
      if player_max_magicka < actor_max_magicka * 0.5:
        magic_advantage = -2
    
    if (magic_advantage >= 0 and strength_advantage < 0) or (magic_advantage < 0 and strength_advantage >= 0):
      # The player is better at magic and the actor is better at strength or vice versa
      relative_magic_string = 'However, in terms of magical strength, '
    else:
      # Either the player or actor is always better, or they're both the same.
      relative_magic_string = 'And in terms of magical strength, '
    
    #also_string = ' also' if ((magic_advantage > 0 and strength_advantage > 0) or (magic_advantage < 0 and strength_advantage < 0)) else ''
    also_string = ' also' if magic_advantage == strength_advantage else ''
    if magic_advantage == 2:
      relative_magic_string += f'you think the player would{also_string} significantly overpower you.'
    elif magic_advantage == 1:
      relative_magic_string += f'you think you would{also_string} be at a disadvantage.'
    elif magic_advantage == 0:
      relative_magic_string += f'you think you would{also_string} be evenly matched.'
    elif magic_advantage == -1:
      relative_magic_string += f'you think you would{also_string} have the advantage.'
    elif magic_advantage == -2:
      relative_magic_string += f'you think you could{also_string} easily overpower the player.'
    
    if player_max_magicka < 100.0 and actor_max_magicka < 100.0 and magic_advantage != 0:
      # If everyone is bad at magic AND strength, add 'either' so the repetition doesn't sound as bad.
      # e.g.
      # "In terms of physical strength, you think the player would significantly overpower you. But neither of you look very strong. 
      #  In terms of magical strength, you think you could easily overpower the player. But neither of you appears well-versed in magic, either."
      either_string = ', either' if both_are_physically_weak else ''
      relative_magic_string += f" But neither of you appears well-versed in magic{either_string}."
    
    # Touch-up the actor's class to rephrase '<class> Service' to something that ChatGPT understands better
    actor_class = input_json['actor_class']
    if actor_class.endswith(' Service'):
        actor_class = actor_class[:-len(' Service')]
        actor_class = f'{actor_class} who offers their services to others'

    # The setup prompt for the first 'chat' message.
    setup_prompt = f"""
You are a role-playing game character in the world of The Elder Scrolls III: Morrowind.

Respond in-character using descriptive language. Don't repeat exactly word-for-word the description below. Also, don't use quotation around your entire response, it's understood that your response is dialogue.

== Context ==
You are a character named "{input_json["actor"]}", you are a {input_json["actor_race"]} {actor_class}.{optional_actor_faction_string}{optional_actor_factoid_string}

The player is named "{input_json["player_name"]}", they are a {input_json["player_race"]} {input_json["player_class"]}.{optional_player_faction_string}{optional_player_factoid_string}

{actor_state_string} {player_state_string}

{relative_strength_string} {relative_magic_string}

You and the player are located in "{input_json["location"]}". The player greets you.
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

    output_json = {
      "model": self.model_name,
      "temperature": self.temperature,
      "messages": conversation
    }
    output_json_str = json.dumps(output_json, indent=2)
    
    if DEBUG:
      return output_json_str

    response = openai.ChatCompletion.create(
      model=self.model_name,
      temperature=self.temperature,
      messages=conversation,
    )
    # Mock response for testing
    '''response = {
      "choices": [
        {
          "message": {
            "content": "Hello, world!"
          }
        }
      ]
    }'''

    if TRACING:
      message_contents = json.dumps({
        "input_json": input_json,
        "output_json": output_json,
        "api_output": response,
      })
      message_contents = gzip.compress(message_contents.encode("utf-8"))
      self.queue_client.send_message(self.queue_client.message_encode_policy.encode(message_contents))

    return response.choices[0]['message']['content']
    #return response['choices'][0]['message']['content']