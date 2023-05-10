# dump_db.py
# Reads all documents from a CosmosDB collection and writes them to
# local directories of json files.

# Requirements:
# pip install azure-cosmos

import os
import json
from azure.cosmos import CosmosClient
from tqdm import tqdm

COSMOS_CONNECTION_STRING = os.environ['COSMOS_CONNECTION_STRING']
COSMOS_DATABASE_NAME = 'openmw_conv'

collections_to_dump = [
    'api_output',
    'js_input',
    'js_output',
]

client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
db = client.get_database_client(COSMOS_DATABASE_NAME)

def dump_collection(collection, collection_name):
    # Create a directory for the collection
    os.makedirs(f'dump/{collection_name}', exist_ok=True)

    # Read all documents from the collection
    for item in tqdm(collection.query_items(
        query='SELECT * FROM c',
        enable_cross_partition_query=True
    ), desc=collection_name):
        # Write each document to a json file
        with open(f'dump/{collection_name}/{item["id"]}.json', 'w') as f:
            json.dump(item, f, indent=2)

for collection_name in tqdm(collections_to_dump, desc='Collections'):
    collection = db.get_container_client(collection_name)
    dump_collection(collection, collection_name)