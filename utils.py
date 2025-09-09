import os
import boto3
import time
from pathlib import Path
import json
import base64
from PIL import Image
from io import BytesIO
from typing import List, Union
from sagemaker.s3 import S3Downloader as s3down
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# --- CONFIGURATION ---
load_dotenv()
session = boto3.session.Session()
region = session.region_name

# AWS Clients
bedrock_client = boto3.client(
    "bedrock-runtime",
    region,
    endpoint_url=f"https://bedrock-runtime.{region}.amazonaws.com"
)
s3vectors = boto3.client("s3vectors", region_name=region)

# --- NEW ELASTICSEARCH CLIENT CONFIGURATION ---
ES_ENDPOINT = os.environ.get("ES_ENDPOINT")
ES_API_KEY = os.environ.get("ES_API_KEY")

es_client = None
if ES_ENDPOINT and ES_API_KEY:
    es_client = Elasticsearch(
        ES_ENDPOINT,
        api_key=ES_API_KEY
    )

# Model ID
multimodal_embed_model = 'amazon.titan-embed-image-v1'


# --- EMBEDDING GENERATION (Unchanged) ---
def get_titan_multimodal_embedding(
    image_path:str=None,
    description:str=None,
    dimension:int=1024,
    model_id:str=multimodal_embed_model
):
    payload_body = {}
    embedding_config = {"embeddingConfig": {"outputEmbeddingLength": dimension}}

    if image_path:
        # Logic to handle local, S3, or URL images and convert to base64
        if image_path.startswith('s3'):
            s3 = boto3.client('s3')
            bucket_name, key = image_path.replace("s3://", "").split("/", 1)
            obj = s3.get_object(Bucket=bucket_name, Key=key)
            base64_image = base64.b64encode(obj['Body'].read()).decode('utf-8')
            payload_body["inputImage"] = base64_image
        elif image_path.startswith(('http://', 'https://')):
            try:
                response = requests.get(image_path, stream=True)
                response.raise_for_status()
                image_content = response.content
                base64_image = base64.b64encode(image_content).decode('utf-8')
                payload_body["inputImage"] = base64_image
            except requests.exceptions.RequestException as e:
                raise Exception(f"Error downloading image from URL: {e}")
        else:
            with open(image_path, "rb") as image_file:
                input_image = base64.b64encode(image_file.read()).decode('utf8')
            payload_body["inputImage"] = input_image

    if description:
        payload_body["inputText"] = description

    assert payload_body, "please provide either an image and/or a text description"

    response = bedrock_client.invoke_model(
        body=json.dumps({**payload_body, **embedding_config}),
        modelId=model_id,
        accept="application/json",
        contentType="application/json"
    )
    return json.loads(response.get("body").read())


# --- S3 SEARCH FUNCTIONS (Unchanged) ---
def search_similar_items_from_text(query_prompt, k, vector_bucket_name, index_name):
    query_emb = get_titan_multimodal_embedding(description=query_prompt, dimension=1024)["embedding"]
    start_time = time.time()
    response = s3vectors.query_vectors(
        vectorBucketName=vector_bucket_name,
        indexName=index_name,
        queryVector={"float32": query_emb},
        topK=k,
        returnDistance=True,
        returnMetadata=True
    )
    end_time = time.time()
    query_time_ms = (end_time - start_time) * 1000
    return response["vectors"], query_time_ms

def search_similar_items_from_image(image_path, k, vector_bucket_name, index_name):
    query_emb = get_titan_multimodal_embedding(image_path=image_path, dimension=1024)["embedding"]
    start_time = time.time()
    response = s3vectors.query_vectors(
        vectorBucketName=vector_bucket_name,
        indexName=index_name,
        queryVector={"float32": query_emb},
        topK=k,
        returnDistance=True,
        returnMetadata=True
    )
    end_time = time.time()
    query_time_ms = (end_time - start_time) * 1000
    return response["vectors"], query_time_ms


# --- ELASTICSEARCH SEARCH FUNCTIONS ---
def _search_es(query_emb, k, index_name):
    """Helper function to perform k-NN search in Elasticsearch."""
    if not es_client:
        raise ConnectionError("Elasticsearch client not configured. Check your .env file for ES_ENDPOINT and ES_API_KEY.")

    knn_query = {
        "field": "embedding_img",  # IMPORTANT: This must match the vector field name in your ES index
        "query_vector": query_emb,
        "k": k,
        "num_candidates": 100
    }

    start_time = time.time()
    response = es_client.search(
        index=index_name,
        knn=knn_query,
        source=["id", "productDisplayName", "img_full_path"] # Specify fields to return
    )
    end_time = time.time()
    query_time_ms = (end_time - start_time) * 1000

    # Format the response to match the structure expected by the Streamlit UI
    results = []
    for hit in response['hits']['hits']:
        distance = 1.0 - hit['_score'] # Convert similarity score to distance
        results.append({
            'key': hit['_source']['id'],
            'distance': distance,
            'metadata': {
                'item_name_in_en_us': hit['_source']['productDisplayName'],
                'img_full_path': hit['_source']['img_full_path']
            }
        })
    return results, query_time_ms

def search_similar_items_from_text_es(query_prompt, k, index_name):
    """Search Elasticsearch with a text query."""
    query_emb = get_titan_multimodal_embedding(description=query_prompt, dimension=1024)["embedding"]
    return _search_es(query_emb, k, index_name)

def search_similar_items_from_image_es(image_path, k, index_name):
    """Search Elasticsearch with an image query."""
    query_emb = get_titan_multimodal_embedding(image_path=image_path, dimension=1024)["embedding"]
    return _search_es(query_emb, k, index_name)


# --- IMAGE UTILITY (Unchanged) ---
def get_image_from_s3(image_full_path):
    if image_full_path.startswith('s3'):
        local_data_root = './data/images'
        if not os.path.exists(local_data_root):
            os.makedirs(local_data_root)
        local_file_name = image_full_path.split('/')[-1]
        s3down.download(image_full_path, local_data_root)
        local_image_path = os.path.join(local_data_root, local_file_name)
        return Image.open(local_image_path)
    return None

