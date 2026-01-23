import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')

# Database Paths
KNOWLEDGE_BASE_FILE = os.path.join(RESOURCES_DIR, 'knowledge_base.json')
FAISS_INDEX_FILE = os.path.join(RESOURCES_DIR, 'faiss_index.bin')

# LLM Settings
OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_K_M" 
# Use the lighter model for high-frequency formula tasks as requested
FORMULA_MODEL_NAME = "qwen2.5-coder:1.5b"