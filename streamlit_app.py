import streamlit as st
import os
from PIL import Image
from dotenv import load_dotenv
from utils import *

def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
            html, body, [class*="st-"] { font-family: 'Poppins', sans-serif; }
            .stApp { background: linear-gradient(to right bottom, #f0f4f8, #e8f0f7); }
            h1 { font-weight: 700 !important; color: #1e293b; }
            h2 { font-weight: 600 !important; color: #334155; }
            .home-container { text-align: center; padding-top: 2rem; }
            div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] > div {
                border: 1px solid #e0e0e0; border-radius: 15px; padding: 2rem 1.5rem !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: all 0.3s ease;
                background-color: white; height: 100%; display: flex; flex-direction: column;
                align-items: center; justify-content: center;
            }
            div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] > div:hover {
                transform: translateY(-8px); box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            .results-grid .st-emotion-cache-1xw8zd0 {
                border: 1px solid #e0e0e0 !important; border-radius: 12px !important; padding: 1rem !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important; height: 100% !important;
                background-color: white; display: flex; flex-direction: column; justify-content: space-between;
            }
            .results-grid img { border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 4px 8px rgba(0,0,0,0.08); }
        </style>
    """, unsafe_allow_html=True)

load_dotenv()
DATASET_IMAGES_LOCATION = os.environ.get("DATASET_IMAGES_LOCATION", "URL")
S3_VECTOR_BUCKET_NAME = os.environ.get("S3_VECTOR_BUCKET_NAME", "your-s3-bucket")
S3_VECTOR_INDEX_NAME = os.environ.get("S3_VECTOR_INDEX_NAME", "your-s3-index")
ES_INDEX_NAME = os.environ.get("ES_INDEX_NAME", "fashion-products-index")

def render_home_page():
    st.markdown("<div class='home-container'>", unsafe_allow_html=True)
    st.title("Welcome to the World of Vector Search ")
    st.markdown("Choose a backend to explore search capabilities.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.header("📦 S3 Vector Search")
            st.markdown("")
            if st.button("Launch S3 Search", type="primary", use_container_width=True):
                st.session_state.page = 's3_search'
                st.rerun()
    with col2:
        with st.container():
            st.header("⚡ Elasticsearch Vector Search")
            st.markdown("")
            if st.button("Launch Elasticsearch Search", use_container_width=True):
                st.session_state.page = 'elasticsearch'
                st.rerun()

def render_s3_search_page():
    if st.button("⬅️ Back to Home"):
        st.session_state.page = 'home'
        st.rerun()
    st.title("🔍 S3 Vector Search")
    st.markdown("Search for similar items using natural language or by uploading an image.")
    with st.sidebar:
        st.header("S3 Configuration")
        bucket_name = st.text_input("Vector Bucket Name", value=S3_VECTOR_BUCKET_NAME)
        index_name = st.text_input("Index Name", value=S3_VECTOR_INDEX_NAME)
        k = st.slider("Number of Results", 1, 30, 3, key="s3_k")
    st.header("Search Items")
    search_method = st.radio("Search method:", ["Text Search", "Image Search"], horizontal=True, key="s3_method")
    query_prompt, uploaded_image, search_button = None, None, False
    if search_method == "Text Search":
        with st.form(key="s3_text_form"):
            query_prompt = st.text_input("Enter search query:", placeholder="e.g., red dress, blue jeans...")
            search_button = st.form_submit_button("🔍 Search", type="primary")
    else:
        uploaded_image = st.file_uploader("Upload an image:", type=['png', 'jpg', 'jpeg'], key="s3_uploader")
        if uploaded_image:
            st.image(Image.open(uploaded_image), caption="Uploaded Image", width=300)
        search_button = st.button("🔍 Search", type="primary")
    if search_button:
        perform_search(search_method, query_prompt, uploaded_image, k, bucket_name, index_name, "S3")

def render_elasticsearch_page():
    if st.button("⬅️ Back to Home"):
        st.session_state.page = 'home'
        st.rerun()
    st.title("⚡ Elasticsearch Vector Search")
    st.markdown("Search for similar items using natural language or by uploading an image.")
    with st.sidebar:
        st.header("Elasticsearch Configuration")
        index_name = st.text_input("Index Name", value=ES_INDEX_NAME)
        k = st.slider("Number of Results", 1, 30, 3, key="es_k")
    st.header("Search Items")
    search_method = st.radio("Search method:", ["Text Search", "Image Search"], horizontal=True, key="es_method")
    query_prompt, uploaded_image, search_button = None, None, False
    if search_method == "Text Search":
        with st.form(key="es_text_form"):
            query_prompt = st.text_input("Enter search query:", placeholder="e.g., summer dress with flowers")
            search_button = st.form_submit_button("🔍 Search", type="primary")
    else:
        uploaded_image = st.file_uploader("Upload an image:", type=['png', 'jpg', 'jpeg'], key="es_uploader")
        if uploaded_image:
            st.image(Image.open(uploaded_image), caption="Uploaded Image", width=300)
        search_button = st.button("🔍 Search", type="primary")
    if search_button:
        # For ES, we pass None for bucket_name as it's not needed
        perform_search(search_method, query_prompt, uploaded_image, k, None, index_name, "Elasticsearch")


def display_search_results(results, query_time_ms, search_engine):
    if not results:
        st.warning("No results found. Try a different search query/image.")
        return
    st.success(f"Found {len(results)} similar items using {search_engine}! (Query time: {query_time_ms:.2f} ms)")
    st.markdown("<div class='results-grid'>", unsafe_allow_html=True)
    sorted_results = sorted(results, key=lambda x: x['distance'])
    for row_start in range(0, len(sorted_results), 3):
        cols = st.columns(3)
        row_items = sorted_results[row_start:row_start + 3]
        for col_idx, element in enumerate(row_items):
            with cols[col_idx]:
                with st.container(border=True):
                    metadata = element.get('metadata', {})
                    item_id = element.get('key', 'N/A')
                    distance = element.get('distance', 0)
                    item_name = metadata.get('item_name_in_en_us', 'Unknown Item')
                    img_full_path = metadata.get('img_full_path', '')
                    try:
                        if DATASET_IMAGES_LOCATION == "S3" and img_full_path:
                            st.image(get_image_from_s3(img_full_path), use_container_width='auto')
                        elif img_full_path:
                            st.image(img_full_path, use_container_width='auto')
                        else:
                            st.markdown("🖼️ *Image not available*")
                    except Exception:
                        st.error("Could not load image.")
                    st.markdown(f"**{item_name}**")
                    st.markdown(f"`Item ID: {item_id}` | `Score: {distance:.4f}`")
    st.markdown("</div>", unsafe_allow_html=True)

def perform_search(method, query, image, k, bucket_name, index, engine):
    if (method == "Text Search" and not query) or (method == "Image Search" and not image):
        st.warning(f"Please provide input for the {method.lower()}.")
        return
    with st.spinner(f"Searching with {engine}..."):
        try:
            results, query_time_ms = None, 0
            temp_path = None
            if method == "Image Search":
                temp_dir = "temp_images"
                if not os.path.exists(temp_dir): os.makedirs(temp_dir)
                temp_path = os.path.join(temp_dir, image.name)
                with open(temp_path, "wb") as f: f.write(image.getbuffer())

            if engine == "S3":
                if method == "Text Search":
                    results, query_time_ms = search_similar_items_from_text(query, k, bucket_name, index)
                else:
                    results, query_time_ms = search_similar_items_from_image(temp_path, k, bucket_name, index)
            elif engine == "Elasticsearch":
                if method == "Text Search":
                    results, query_time_ms = search_similar_items_from_text_es(query, k, index)
                else:
                    results, query_time_ms = search_similar_items_from_image_es(temp_path, k, index)
            
            if temp_path: os.remove(temp_path)
            display_search_results(results, query_time_ms, engine)
        except Exception as e:
            st.error(f"Error during search: {e}")
            st.info("Please check your AWS/Elasticsearch credentials and configuration.")


def main():
    st.set_page_config(page_title="Search App", page_icon="", layout="wide")
    load_css()
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    page_router = {
        'home': render_home_page,
        's3_search': render_s3_search_page,
        'elasticsearch': render_elasticsearch_page
    }
    page_router[st.session_state.page]()

if __name__ == "__main__":
    main()

