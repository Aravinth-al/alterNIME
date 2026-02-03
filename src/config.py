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

# UPGRADED MODEL: Smarter logic, better at chaining
# src/config.py

# ... (keep other settings) ...

# UPDATE TO THE SMALLER MODEL
# LLM Settings
OLLAMA_API_URL = "http://localhost:11434/api/chat"

# SWITCH TO LLAMA 3.2 (3B Parameters)
MODEL_NAME = "llama3.2" 
FORMULA_MODEL_NAME = "llama3.2"

# DEBUG SETTINGS
DEBUG_MODE = True