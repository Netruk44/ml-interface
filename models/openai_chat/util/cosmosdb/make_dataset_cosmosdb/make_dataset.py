# make_dataset.py
# Creates a Huggingface Dataset from the CosmosDB database.
# Intended for creating a dataset to train T5 / some smaller text model.

# Requirements:
# pip install azure-cosmos
# pip install tqdm
# pip install datasets
#
# os.environ["COSMOS_CONNECTION_STRING"] - set to your cosmosdb connection string

import os
from azure.cosmos import CosmosClient
from tqdm import tqdm
from datasets import Dataset, Value
import random

dataset_name = 'openmw_disposition'

COSMOS_CONNECTION_STRING = os.environ['COSMOS_CONNECTION_STRING']
COSMOS_DATABASE_NAME = 'openmw_conv'

collections_to_include = [
    'api_output',
    'js_input',
    'js_output',
    'disposition',
]

def get_collection(collection_name):
    return db.get_container_client(collection_name)

def get_documents(collection):
    return collection.query_items(
        query='SELECT * FROM c',
        enable_cross_partition_query=True
    )

def get_row(documents):
    api_output = documents['api_output']
    json_input = documents['js_input']
    json_output = documents['js_output']
    disposition = documents['disposition']

    # UPDATE
    # Input:
    # Start with the conversation history
    messages = json_output['messages'].copy()
    # First, replace the final message with the player's original prompt
    # Replacing the message containing the actor's current disposition
    messages[-1]["content"] = json_input['prompt']

    # Add the model's response to the dialogue
    messages.append({"role": "assistant", "content": api_output['choices'][0]['message']['content']})

    # Flatten to just the content
    messages = [message['content'] for message in messages]

    # Join the messages into a single string
    input_str = '\n'.join(messages)

    # Output:
    disposition_change = disposition['disposition_change']
    # Output just the disposition modified by +/- 5
    #disposition_change = int(random.randint(-5, 5) + disposition['disposition_change'])
    output_str = str(disposition_change)

    return {
        'id': api_output['id'],
        'input': input_str,
        'output': output_str,
    }

client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
db = client.get_database_client(COSMOS_DATABASE_NAME)


# all_documents['api_output'][<id>]
all_documents = {}

for collection_name in tqdm(collections_to_include, desc='Collections'):
    collection = get_collection(collection_name)
    all_documents[collection_name] = {document['id']: document for document in list(get_documents(collection))}
    print(f'{collection_name}: {len(all_documents[collection_name])}')

# Create a dataset from the documents
# Dataset has the following columns:
# - id: string, the conversation id
# - input: string, the complete input for the model
# - output: string, the output the model should produce
dataset_rows = []

all_message_ids = set(all_documents[collections_to_include[0]].keys())
for conversation_id in all_message_ids:
    #for collection_name in collections_to_include:
    #    if conversation_id not in all_documents[collection_name]:
    #        print(len(all_documents[collection_name]))
    #        raise Exception(f'Conversation {conversation_id} not found in collection {collection_name}')
    conversation_documents = {collection_name: all_documents[collection_name][conversation_id] for collection_name in collections_to_include}
    dataset_rows.append(get_row(conversation_documents))


column_names = dataset_rows[0].keys()
dataset_dict = {column_name: [row[column_name] for row in dataset_rows] for column_name in column_names}

dataset = Dataset.from_dict(dataset_dict)
dataset.save_to_disk(dataset_name)