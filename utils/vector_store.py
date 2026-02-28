"""
vector_store.py — Knowledge Base Indexing & Retrieval Utility.

Uses FAISS for local vector storage and Gemini Embeddings for 
semantic search across mental health resources.
"""

import os
import faiss
import pickle
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import config

# Store for the singleton vector store instance
_vector_store = None

def get_embeddings():
    """Returns the local HuggingFace / Sentence-Transformers Embeddings instance."""
    # Using 'all-MiniLM-L6-v2' as it's small, fast, and excellent for RAG tasks
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def initialize_vector_store(force_rebuild: bool = False):
    """
    Load an existing vector store from disk or build a new one 
    from the files in data/knowledge_base/.
    """
    global _vector_store
    
    kb_path = os.path.join(config.DATA_DIR, "knowledge_base")
    index_path = os.path.join(config.DATA_DIR, "faiss_index")
    
    # Ensure KB directory exists
    os.makedirs(kb_path, exist_ok=True)

    # 1. Try loading from disk if it exists and we're not forcing rebuild
    if not force_rebuild and os.path.exists(index_path):
        try:
            print(f"[VectorStore] Loading existing index from {index_path}...")
            _vector_store = FAISS.load_local(
                index_path, 
                get_embeddings(),
                allow_dangerous_deserialization=True
            )
            return _vector_store
        except Exception as e:
            print(f"[VectorStore] Failed to load index: {e}. Rebuilding...")

    # 2. Rebuild from files
    print("[VectorStore] Building new vector store from knowledge_base/...")
    
    # Check if there are any files to index
    if not any(os.scandir(kb_path)):
        print("[VectorStore] No files found in knowledge_base/. Skipping build.")
        return None

    # Load PDFs and Text files
    pdf_loader = DirectoryLoader(kb_path, glob="./*.pdf", loader_cls=PyPDFLoader)
    txt_loader = DirectoryLoader(kb_path, glob="./*.txt", loader_cls=TextLoader)
    md_loader = DirectoryLoader(kb_path, glob="./*.md", loader_cls=TextLoader)

    docs = []
    docs.extend(pdf_loader.load())
    docs.extend(txt_loader.load())
    docs.extend(md_loader.load())

    if not docs:
        print("[VectorStore] Loaded 0 documents. Skipping build.")
        return None

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    splits = text_splitter.split_documents(docs)
    print(f"[VectorStore] Split into {len(splits)} chunks.")

    # Create and save FAISS index
    _vector_store = FAISS.from_documents(splits, get_embeddings())
    _vector_store.save_local(index_path)
    print(f"[VectorStore] FAISS index saved to {index_path}.")
    
    return _vector_store

def query_knowledge_base(query: str, k: int = 3) -> str:
    """
    Search the knowledge base for content semantically related to the query.
    Returns a concatenated string of the most relevant chunks.
    """
    global _vector_store
    
    if _vector_store is None:
        initialize_vector_store()
    
    if _vector_store is None:
        return ""

    results = _vector_store.similarity_search(query, k=k)
    
    context_parts = []
    for i, doc in enumerate(results):
        source = os.path.basename(doc.metadata.get("source", "Unknown"))
        context_parts.append(f"--- Context {i+1} (Source: {source}) ---\n{doc.page_content}")
    
    return "\n\n".join(context_parts)
