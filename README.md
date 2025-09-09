
# Vector Search Showdown

An interactive Streamlit application to benchmark and compare the performance (latency and relevance) of Amazon S3 Vector Search and Elasticsearch Serverless 


## Features

#### Text-Based Search
- Enter natural language descriptions like "red dress", "blue jeans", "ankle boots"
- Uses Amazon Titan to convert text to embeddings
- Finds semantically similar fashion items
#### Image-Based Search
- Upload product images (PNG, JPG, JPEG)
- Generates embeddings from uploaded images
- Returns visually similar items from the catalog

#### Rich Metadata Display
- Product names and descriptions
- Categories (gender, master category, sub category)
- Attributes (color, season, usage, year)
- Similarity scores
- Product images (from Kaggle or S3)
#### Performance Metrics
- Real-time query execution times
- Configurable result count (1-30 items)
- Sorted results by similarity score
- Dual Backend Support: Seamlessly switch between S3 and Elasticsearch to perform vector searches.



## Performance Comparison
The primary goal of this project is to provide a practical comparison between two modern vector search solutions:

- Amazon S3 Vector Search

- Elasticsearch Serverless
#### This application allows you to evaluate:

Query Latency: How quickly does each backend return results for similar queries?

Result Relevance: How do the search results compare in quality and relevance?

Operational Simplicity: Understand the setup and query process for both technologies.
## Architecture

The application follows a simple yet powerful architecture:


```http
Fashion Dataset (Kaggle)
    ↓
Generate Embeddings (Bedrock Titan)
    ↓
Store in S3 Vectors & Elasticsearch Serverless
    ↓
Streamlit UI (Text/Image Search)
```

- Frontend: A Streamlit application provides the user interface.

- Embedding Model: Amazon Bedrock (Titan Multimodal) is used to convert all user queries (text or image) into 1024-dimension vector embeddings in real-time.

- Vector Databases:
    - Amazon S3 Vectors
    - Elasticsearch Serverless

- Data: Both backends are populated with the same dataset of vector embeddings, generated from the Fashion Product Images (44k documents) dataset.

## API Reference

#### 1. Clone the Repository

```http
  git clone https://github.com/tusharsingh007/vector-search.git
  cd vector-search


```

#### 2. Set Up a Virtual Environment

```http
# Create the environment
python3 -m venv .venv

# Activate it (on macOS/Linux)
source .venv/bin/activate

# On Windows, use: .venv\Scripts\activate
```
#### 3. Install Dependencies

```http
pip install -r requirements.txt
```
#### 4. Configure Your Environment
Create a file named .env in the root of the project folder and populate it with your credentials. Do not commit this file to Git.

```http
# .env file

# AWS Configuration (ensure your CLI is also configured)
AWS_REGION="us-east-1" 

# S3 Configuration
DATASET_IMAGES_LOCATION="URL"
S3_VECTOR_BUCKET_NAME="your-s3-bucket-with-vectors"
S3_VECTOR_INDEX_NAME="your-s3-vector-index"

# Elasticsearch Configuration
ES_ENDPOINT="your-elastic-cloud-endpoint:443"
ES_API_KEY="your-encoded-api-key"
ES_INDEX_NAME="Index-Name"
```


#### 5. Launch the Streamlit Application
Start the interactive search interface:
```http
./run_streamlit.sh
```


## Dataset Information

The Fashion Product Images Dataset includes:

- ~44,000 fashion products with images and metadata
- Categories: Men's, Women's, and Kids' fashion items
- Attributes: Product type, color, season, usage, brand information
- Images: High-quality product photos from various angles
- [Fashion Product Images Dataset](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset)


## Documentation

[Elasticsearch Serverless](https://www.elastic.co/docs/solutions/search/serverless-elasticsearch-get-started)

[Amazon S3 Vectors](https://aws.amazon.com/s3/features/vectors/)

