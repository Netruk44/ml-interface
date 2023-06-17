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
import sys
import re

######################### Configuration
# OpenAI API Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Debug mode
# Instead of calling the api, return the content that would have been sent to the api
DEBUG = False

# Mock mode
# Instead of calling the real api, return a static response
RETURN_MOCK_RESPONSE = False

# Message tracing
# Send input json, output json, and the response from the api to an Azure Storage Queue
# Set this to your Azure Storage Connection String, needs Queue Add permissions only.
# If you would like to help me out with generating data, send me an e-mail at somethingelse@danieltperry.me and I can give you my SAS token.
TRACING_ENDPOINT = os.environ.get("TRACING_ENDPOINT")

######################### Auto-configuration
TRACING = TRACING_ENDPOINT is not None and TRACING_ENDPOINT != ""
TRACING = False # Manual override

if TRACING:
  from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy
  import gzip
  queue_name = "openmw-messages"
#########################

class Model:
  def __init__(self,
    model_name = "gpt-3.5-turbo",
    temperature = 1.0,
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

    location = input_json["location"]

    actor_name = input_json["actor"]
    player_name = input_json["player_name"]

    player_race = input_json["player_race"]
    actor_race = input_json["actor_race"]

    player_class = input_json["player_class"]
    # Touch-up the actor's class to rephrase '<class> Service' to something that ChatGPT understands better
    actor_class = input_json['actor_class']
    actor_class_extended = actor_class
    if actor_class.endswith(' Service'):
        actor_class = actor_class[:-len(' Service')]
        actor_class_extended = f'{actor_class} who offers their services to others'
    
    # Male/female text for actor and player
    actor_malefemale = 'male' if int(input_json['actor_is_female']) == 0 else 'female'
    player_malefemale = 'male' if int(input_json['player_is_female']) == 0 else 'female'

    # Actor faction description string
    optional_actor_faction_string = ''
    actor_faction = input_json["actor_faction"]
    actor_faction_rank = int(input_json["actor_faction_rank"])

    if actor_faction != '':
      # Generic faction description string for when rank isn't set.
      optional_actor_faction_string = f' You are a member of the "{actor_faction}".'

      # Replace the string entirely with a description of the faction rank
      if actor_faction_rank > -1:
        if actor_faction_rank < 4:
          optional_actor_faction_string = f' You are a low-ranking member of your faction, the "{actor_faction}".'
        elif actor_faction_rank < 7:
          optional_actor_faction_string = f' You are a mid-ranking member of your faction, the "{actor_faction}". You expect to be treated with respect.'
        else:
          optional_actor_faction_string = f' You are a high-ranking, well-known and respected member of your faction, the "{actor_faction}". You are a leader and a role model to your peers.'

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

        optional_player_faction_string = f' {player_name} is a member of the "{player_faction}", and'

        if player_faction_rank < 4:
          optional_player_faction_string += ' they\'re a low-ranking member of their faction.'
        elif player_faction_rank < 7:
          optional_player_faction_string += ' they\'re a a mid-ranking member of their faction.'
          if actor_faction.casefold() == player_faction.casefold() and actor_faction_rank < player_faction_rank:
            optional_player_faction_string += ' You should show respect for their position, as they outrank you.'
        else:
          optional_player_faction_string += ' they\'re a a high-ranking member of their faction. You should show respect for their position.'
    
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
      optional_actor_factoid_string = " You don't have much of a reputation. Feel free to make up a simple backstory for yourself."

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
          actor_state_string += 'a little bit tired'
      

      actor_state_string = f'You are {actor_state_string}.'

    if actor_level < 5:
      actor_state_string += ' You are inexperienced when it comes to combat.'
    elif actor_level > 20:
      actor_state_string += ' You are a veteran when it comes to combat.'

    # Actor inventory
    actor_inventory_string = 'In your possession, you have '

    # Gold and Store gold
    actor_gold = int(input_json["actor_inventory"]["gold"])
    actor_owned_store_gold = int(input_json["actor_inventory"]["store_gold"])

    if actor_gold == 0 and actor_owned_store_gold == 0:
      # Reset the start of the string
      actor_inventory_string = 'You do not currently posess any gold pieces, however your character may have some gold stored elsewhere depending on their background.'
    elif actor_gold == 0 and actor_owned_store_gold > 0:
      actor_inventory_string += f'no gold pieces on you, but the store you own has {actor_owned_store_gold} gold pieces in the lockbox.'
    elif actor_gold > 0 and actor_owned_store_gold == 0:
      actor_inventory_string += f'{actor_gold} gold pieces.'
    else:
      actor_inventory_string += f'{actor_gold} gold pieces, and the store you own has {actor_owned_store_gold} gold pieces in the lockbox.'
    
    # Actor inventory items

    # Do a rudimentary attempt at summarizing inventory contents based on shared prefixes.
    # TODO: Possibly train a T5 model to do this automatically.
    prefixes = {}

    for item in input_json["actor_inventory"]["items"]:
      prefix = item.split(' ')[0]
      if prefix not in prefixes:
        prefixes[prefix] = []
      prefixes[prefix].append(item)
    
    # Mention the sets of itmes the actor has, then fill any empty space with items
    max_item_count = 3
    items_remaining = max_item_count

    # Enumerate the prefixes ordered by the number of items they have.
    # Go from most items to least items.
    if len(prefixes) > 0:
      actor_inventory_string += ' In addition, you are wearing or otherwise carrying '
      first = True

      #for prefix in sorted(prefixes, key=lambda prefix: len(prefixes[prefix]), reverse=True):
      for i, prefix in enumerate(sorted(prefixes, key=lambda prefix: len(prefixes[prefix]), reverse=True)):
        items_remaining -= 1
        
        if first:
          first = False
        else:
          if items_remaining < 0:
            break
          elif items_remaining == 0 or i == len(prefixes) - 1:
            actor_inventory_string += ', and '
          else:
            actor_inventory_string += ', '
        
        items_with_same_prefix = prefixes[prefix]
        number_of_items_in_set = len(items_with_same_prefix)
        
        first_item_name = items_with_same_prefix[0]
        first_item_count = input_json["actor_inventory"]["items"][first_item_name]
        first_item_count = int(first_item_count)

        # Figure out the appropriate prefix (a couple of, a set of, a complete set of)
        set_descriptor = ''

        is_group_a_set = True

        if prefix == 'Scroll' or prefix == 'Potion':
          is_group_a_set = False
        
        if number_of_items_in_set == 1:
          # This may not be a set of items, but there may be more than one in this stack.
          if first_item_count == 1:
            set_descriptor = 'a'
          elif first_item_count == 2:
            set_descriptor = 'two'
          elif first_item_count < 10:
            set_descriptor = 'a few'
          else:
            set_descriptor = 'a stack of'
        else:
          if is_group_a_set:
            # Sets of armor, weapons, etc.
            if number_of_items_in_set == 2:
              set_descriptor = 'a couple pieces of'
            elif number_of_items_in_set < 7:
              set_descriptor = 'a set of'
            else:
              set_descriptor = 'a complete set of'
          else:
            # Scrolls, potions, etc.
            if number_of_items_in_set == 2:
              set_descriptor = 'a couple'
            elif number_of_items_in_set < 7:
              set_descriptor = 'a few different types of'
            else:
              set_descriptor = 'a variety of'
        
        # The shared prefix
        #actor_inventory_string += f'{set_descriptor} {prefix}'

        category = ''
        # Figure out the set description, armor/clothing/weapons/potions
        for item_name in items_with_same_prefix:
          # Common/Extravagent Clothing
          if (item_name.endswith("Shirt") 
          or item_name.endswith("Shoes") 
          or item_name.endswith("Pants")
          or item_name.endswith("Ring")
          or item_name.endswith("Belt")
          or item_name.endswith("Amulet")
          or item_name.endswith("Glove")
          or item_name.endswith("Skirt")
          or item_name.endswith("Robe")):
            category = 'clothing'

            # Robes are a special subset of clothing, check everything in the set to see if it's a robe.
            if any(other_item_name.endswith("Robe") for other_item_name in items_with_same_prefix):
              category = 'robes'

            break

          # Armor
          if (item_name.endswith("Cuirass")
          or item_name.endswith("Boots")
          or item_name.endswith("Greaves")
          or item_name.endswith("Shield")
          or item_name.endswith("Gauntlets")
          or item_name.endswith("Helm")
          or item_name.endswith("Bracer")
          or item_name.endswith("Pauldron")):
            category = 'armor'
            break

          # Weapons
          if (item_name.endswith("Bow")
          or item_name.endswith("Staff")
          or item_name.endswith("Shortsword")
          or item_name.endswith("Longsword")
          or item_name.endswith("Dagger")
          or item_name.endswith("Mace")
          or item_name.endswith("Axe")
          or item_name.endswith("Warhammer")
          or item_name.endswith("Katana")
          or item_name.endswith("Wakizashi")
          or item_name.endswith("Tanto")):
            category = 'weapon'
            break

          # Lockpicks
          if (item_name.endswith("Lockpick")
            or item_name.endswith("Probe")):
            category = 'lockpicking equipment'
            break
        
        # Fixups
        # 'a common clothing' -> 'a piece of common clothing' (correct grammar)
        if ((category == 'clothing' or category == 'armor')
            and number_of_items_in_set == 1):
          set_descriptor = 'a piece of'
        
        # 'a steel weapon' -> 'a steel longsword weapon' (be specific if there's only one item in the set)
        if (category == 'weapon' and number_of_items_in_set == 1):
          # Replace the shared prefix with the entire item name
          prefix = first_item_name
          # Alternatively:
          # category = '' # Will trigger the "len(category) == 0" check below

        # 'a Expensive robes' -> 'a set of Expensive robes'
        if (category == 'robes' and number_of_items_in_set == 1):
          set_descriptor = 'a set of'
        
        # 'a set of iron weapon' -> 'a set of iron weapons'
        if (category == 'weapon' and number_of_items_in_set > 1):
          category = 'weapons'
        #if category == 'weapon':
        #  if number_of_items_in_set == 1:
        #    category = 'weaponry'
        #  else:
        #    category = 'weapons'
        
        # 'a guide' -> 'a guide to Balmora'
        # If we don't know the category, but there's more to the name than just the prefix, use that.
        if (len(category) == 0                        # No category
            and len(first_item_name) > len(prefix)):  # There's more to the name than just the prefix

          if number_of_items_in_set == 1:
            category = first_item_name[len(prefix):]
            category = category.strip()

            if first_item_count > 1:
              category = f'{category}s'
          else:
            # More than likely this is an item with a common prefix.
            # 'a couple pieces of guide' -> 'a couple guides'
            set_descriptor = set_descriptor.replace(' pieces of', '')
            prefix = f'{prefix}s'
        
        if len(category) > 0:
          # Only add the space if there's a category
          category = f' {category}'

        actor_inventory_string += f'{set_descriptor} {prefix}{category}'

        #if items_remaining == 0:
        #  break
        #elif items_remaining == 1:
        #  actor_inventory_string += ', and '
        #else:
        #  actor_inventory_string += ', '

      if len(prefixes) > max_item_count:
        if len(prefixes) > max_item_count * 2:
          many_items_string = ' many'
        else:
          many_items_string = ''
        actor_inventory_string += f', among{many_items_string} other things'
      actor_inventory_string += '.'

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
        optional_player_factoid_string = f" You think you might have heard of {player_name} before, but you don't know much about them."
      elif player_reputation < 50:
        optional_player_factoid_string = f" You've heard of {player_name} before and have heard rumors about their previous deeds."
      elif player_reputation < 100:
        optional_player_factoid_string = f" {player_name} is starting to become well-known throughout the land. Because they've helped so many people, they've been talked about a lot."
      else:
        optional_player_factoid_string = f" {player_name} is a household name. Most people know someone that {player_name} has helped."
    # Does the player have a bounty?
    elif player_bounty > 0 and random.randint(0, 1000) < player_bounty:
      if player_bounty < 50:
        optional_player_factoid_string = f" You've heard a rumor that someone named \"{player_name}\" has a small bounty for something minor like trespassing."
      elif player_bounty < 1000:
        optional_player_factoid_string = f" {player_name} has a bounty for something serious like assault or pickpocketing."
      elif player_bounty < 5000:
        optional_player_factoid_string = f" {player_name} is a known criminal, likely a murderer. You know they are wanted by the authorities."
      else:
        optional_player_factoid_string = f" {player_name} is a known serial-killer, authority has made it known that the player should be fled from or killed on sight."
    
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
      player_state_string = f"{player_name}{also_string} appears in good health."
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
      
      player_state_string = f'{player_name} seems to be {player_state_string}.'
    
    if player_level < 5:
      also_string = ' also' if actor_level < 5 else ''
      player_state_string += f' {player_name}{also_string} looks inexperienced and fresh-faced.'
    elif player_level > 20:
      also_string = ' also' if actor_level > 20 else ''
      player_state_string += f' {player_name}{also_string} looks like a veteran, with many scars and a hardened expression.'

    # Describe the player's relative strength (using HP for reference)
    relative_strength_string = 'Hypothetically speaking, if you were to fight, then in terms of physical strength, '
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
      relative_strength_string += f'you think {player_name} would significantly overpower you.'
    elif strength_advantage == 1:
      relative_strength_string += 'you think you would be at a disadvantage.'
    elif strength_advantage == 0:
      relative_strength_string += 'you think you would be evenly matched.'
    elif strength_advantage == -1:
      relative_strength_string += 'you think you would have the advantage.'
    elif strength_advantage == -2:
      relative_strength_string += f'you think you could easily overpower {player_name}.'
    
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
      relative_magic_string += f'you{also_string} think {player_name} would significantly overpower you.'
    elif magic_advantage == 1:
      relative_magic_string += f'you{also_string} think you would be at a disadvantage.'
    elif magic_advantage == 0:
      relative_magic_string += f'you{also_string} think you would be evenly matched.'
    elif magic_advantage == -1:
      relative_magic_string += f'you{also_string} think you would have the advantage.'
    elif magic_advantage == -2:
      relative_magic_string += f'you{also_string} think you could easily overpower {player_name}.'
    
    if player_max_magicka < 100.0 and actor_max_magicka < 100.0 and magic_advantage != 0:
      # If everyone is bad at magic AND strength, add 'either' so the repetition doesn't sound as bad.
      # e.g.
      # "In terms of physical strength, you think the player would significantly overpower you. But neither of you look very strong. 
      #  In terms of magical strength, you think you could easily overpower the player. But neither of you appears well-versed in magic, either."
      either_string = ', either' if both_are_physically_weak else ''
      relative_magic_string += f" But neither of you appears well-versed in magic{either_string}."
    
    # Give an 'overall' description at the end by adding the two advantages.
    overall_advantage_string = 'Overall, you think to yourself that'
    overall_advantage = strength_advantage + magic_advantage

    if overall_advantage > 3: # 4
      overall_advantage_string += f" you should definitely avoid confrontation with {player_name}."
    elif overall_advantage > 1: # 2, 3
      overall_advantage_string += f" they're stronger than you. You wouldn't win a fight, if {player_name} wanted to have one."
    elif overall_advantage > -2: # -1, 0, 1
      overall_advantage_string += f" it would be a struggle to win in a fight against {player_name}, if their intentions are hostile."
    elif overall_advantage > -4: # -2, -3
      overall_advantage_string += f" you shouldn't be intimidated by {player_name}."
    else: # -4
      overall_advantage_string += f" {player_name} couldn't cause you any harm. even if they tried."

    # The messages from the in-game conversation.
    # TODO: Support 'system' messages from the game, such as '<X> was removed from your inventory.'
    # TODO: Only take the last N (2/4/10?) messages
    #   TODO: If there are removed messages, prepend a system message with something like "You and player_name talk for a <bit|while|long time>, with the conversation currently at..."
    #   TODO: Attempt: Create a model that summarizes the removed messages, and add that summary to the system message.
    existing_messages = [{
      "role": "assistant" if message["who"] == "actor" else "user",
      "content": message["text"]
    } for message in input_json["history"]]

    # Remove persuasion attempts and their replies from the messages.
    # e.g. Remove both 'Admire Fail' and 'Your tone lacks sincerity.'
    messages_to_remove = [
      "Admire Fail",
      "Intimidate Fail",
      "Taunt Fail",
      "Bribe Fail",
      "Admire Success",
      "Intimidate Success",
      "Taunt Success",
      "Bribe Success",
    ]

    removed_message = True

    while removed_message:
      removed_message = False

      for i, message in enumerate(existing_messages):
        if message["content"] in messages_to_remove:
          del existing_messages[i:i+2]
          removed_message = True
          break

    # The prompt that the player entered, to be answered by the AI.
    player_prompt = input_json["prompt"]

    # Add information about the actor's current disposition towards the player.
    # Scale from 1-100 to a 1-10 scale
    #   Theory: text model will be able to more easily intuit a single digit than a two digit number.
    #   Context: All the numbers from 1 up to like 500 are one single token to the model.
    #            It might be easier for the model to provide meaningful distinction between 10 different tokens than 100.
    #player_prompt = f'[NOTE: {actor_name}\'s current disposition towards {player_name} is {int(input_json["actor_disposition"]) // 10} / 10.]\n\n{original_player_prompt}'

    # An optional textual description of the actor's disposition towards the player.
    optional_disposition_message = []
    optional_disposition_description = None
    actor_disposition = int(input_json["actor_disposition"])

    # Add a little fuzzing to the disposition check (+/- 5), to ""simulate"" micro-changes in disposition as conversation naturally progresses.
    if actor_disposition >= 90 + (random.randint(0, 10) - 5):
      optional_disposition_description = 'adore'
    elif actor_disposition >= 70 + (random.randint(0, 10) - 5):
      optional_disposition_description = 'have a positive disposition towards'
    elif actor_disposition <= 30 + (random.randint(0, 10) - 5):
      optional_disposition_description = 'have a negative disposition towards'
    elif actor_disposition <= 10 + (random.randint(0, 10) - 5):
      optional_disposition_description = 'loathe'
    
    if optional_disposition_description:
      optional_disposition_message.append(f'Note: As a result of previous interactions with them, you currently {optional_disposition_description} {player_name}.')

    # The conversation as ChatGPT receives it.
    conversation = [
      # First system message, general guidance for the model.
      {"role": "system", "content": f"You are \"{actor_name}\", a {actor_malefemale} {actor_race} {actor_class} in the world of The Elder Scrolls III: Morrowind. You should always respond in-character as \"{actor_name}\" using character-appropriate dialogue based on your character's background and personality."},

      # Second system message, information about the character it is playing as.
      {"role": "system", "content": f"{actor_name}, you are a {actor_malefemale} {actor_race} {actor_class_extended} currently located in \"{location}\".{optional_actor_faction_string}{optional_actor_factoid_string} {actor_inventory_string} {actor_state_string}"},

      # Third system message, information about the player character.
      {"role": "system", "content": f"A {player_malefemale} {player_race} {player_class} approaches you and introduces themselves as \"{player_name}\".{optional_player_faction_string}{optional_player_factoid_string} {player_state_string} You begin talking."},

      # The current conversation from in-game
      *existing_messages,

      # What the player entered into the text box
      {"role": "user", "content": player_prompt},

      # An optional note to the model about its current disposition towards the player.
      *optional_disposition_message,
    ]

    output_json = {
      "model": self.model_name,
      "temperature": self.temperature,
      "messages": conversation
    }
    output_json_str = json.dumps(output_json, indent=2)
    
    if DEBUG:
      return output_json_str

    if RETURN_MOCK_RESPONSE:
      # Mock response for testing
      response = {
        "choices": [
          {
            "message": {
              "content": "Hello, world!"
            }
          }
        ]
      }
    else:
      response = openai.ChatCompletion.create(
        model=self.model_name,
        temperature=self.temperature,
        messages=conversation,
      )

    if TRACING:
      message_contents = json.dumps({
        "input_json": input_json,
        "output_json": output_json,
        "api_output": response,
      })
      message_contents = gzip.compress(message_contents.encode("utf-8"))
      self.queue_client.send_message(self.queue_client.message_encode_policy.encode(message_contents))

    # Can't do response.choices on the mock response, since it's a dict and not an object. Need to use response['choices'] instead.
    text_response = response.choices[0]['message']['content'] if not RETURN_MOCK_RESPONSE else response['choices'][0]['message']['content']
    text_response = self.clean_response(text_response)

    return text_response
  
  def clean_response(self, text):
    # Sometimes the model likes to encase the response in quotes, which is incorrect.
    text = text.strip('"')
    return text