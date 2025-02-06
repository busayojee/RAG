from pathlib import Path
from typing import Dict, List
import base64
import gc
import os
import pickle
import streamlit as st
from rag import RAGSystem
from rag.indexer import Docx2txtLoader, PyPDFLoader, TextLoader
from streamlit_pdf_viewer import pdf_viewer
import time

# Constants
PATH_DOCUMENTS = Path("documents")
PATH_SESSION_STATE = Path("session_state.pkl")
FILE_TYPES = ["pdf", "docx", "txt"]
MAX_PREVIEW_LENGTH = 500




# Session Stuffs
def initialize_session_state():
    defaults = {
        "saved_files": [],
        "file_previews": {},
        "messages": [],
        "rag_initialized": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_session_state():
    try:
        with open(PATH_SESSION_STATE, 'wb') as f:
            # Filter out any keys starting with "delbtn_"
            state = {k: v for k, v in st.session_state.items() if not k.startswith("delbtn_")}
            print(f"saving session_state: {state}")
            pickle.dump(state, f)
    except Exception as e:
        print(f"Error during saving session state: {e}")

def load_session_state():
    try:
        if PATH_SESSION_STATE.exists():
            with open(PATH_SESSION_STATE, "rb") as f:
                state = pickle.load(f)
                st.session_state.update(state)
    except Exception as e:
        st.error(f"Error loading session state: {str(e)}")

# File Op
def initialize_rag_system():
    PATH_DOCUMENTS.mkdir(exist_ok=True)
    rag_system = RAGSystem(str(PATH_DOCUMENTS))
    if not st.session_state.rag_initialized:      
        st.session_state.rag_initialized = True
    return rag_system

def save_uploaded_file(file):
    save_path = PATH_DOCUMENTS / file.name
    with save_path.open("wb") as f:
        f.write(file.getbuffer())

def delete_file(filename, rag):
    file_path = PATH_DOCUMENTS / filename
    if file_path.exists():
        print("Exists")
        file_path.unlink()
    rag.indexer.update_vector_db()
    if filename in st.session_state.saved_files:
        st.session_state.saved_files.remove(filename)
    if filename in st.session_state.file_previews:
        del st.session_state.file_previews[filename]
    save_session_state()
    st.rerun()

# UI Stuffs
def setup_page_styling():
    st.markdown("""
    <style>
    /* Main Background */
    .stApp {{
        background-color: #F8F9FA;
        color: #212529;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #2C2F33 !important;
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
        font-size: 16px !important;
    }}

    /* Headings */
    h1, h2, h3, h4, h5, h6 {{
        color: #000000 !important;
        font-weight: bold;
    }}

    /* Fix Text Visibility */
    p, span, div {{
        color: #212529 !important;
    }}

    /* File Uploader */
    .stFileUploader>div>div>div>button {{
        background-color: #FFC107;
        color: #000000;
        font-weight: bold;
        border-radius: 8px;
    }}

    /* Fix Navigation Bar (Top Bar) */
    header {{
        background-color: #1E1E1E !important;
    }}
    header * {{
        color: #FFFFFF !important;
    }}
    </style>
""", unsafe_allow_html=True)

def render_sidebar(rag):
    with st.sidebar:
        st.header("Instructions 📚")
        st.markdown("""
            1. Upload documents using the uploader below
            2. Ask questions about your documents
            3. Get answers
        """)
        
        st.header("Document Manager 📁")
        handle_file_uploads(rag)
        render_uploaded_files_list(rag)
        render_file_previews()

def handle_file_uploads(rag):
    uploaded_files = st.file_uploader(
        "Upload Documents", 
        type=FILE_TYPES, 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.saved_files:
                save_uploaded_file(file)
                st.session_state.saved_files.append(file.name)
                st.session_state.file_previews[file.name] = file.name
        
        rag.indexer.update_vector_db()
        save_session_state()
        # st.rerun()

def render_uploaded_files_list(rag):
    st.markdown("---")
    st.subheader("Uploaded Files")
    
    if not st.session_state.saved_files:
        st.info("No documents uploaded yet")
        return
    
    for filename in st.session_state.saved_files:
        cols = st.columns([4, 1])
        cols[0].caption(f"📄 {filename}")
        widget_key = f"delbtn_{filename.replace('.', '_').replace(' ', '_')}"
        if cols[1].button("❌", key=widget_key):
            delete_file(filename, rag)
            
            # save_session_state()
            # st.rerun()

def render_file_previews():
    st.markdown("---")
    st.subheader("File Previews")
    
    for filename in st.session_state.saved_files:
        with st.expander(f"📄 {filename}", expanded=True):
            try:
                name = st.session_state.file_previews.get(filename, None)
                if name:
                    save_path = Path(PATH_DOCUMENTS, filename)
                    if save_path.exists():   
                        if filename.endswith(".pdf"):
                            with open(save_path, "rb") as f:
                                pages = f.read()
                            pdf_viewer(
                                input=pages,
                                pages_to_render=[1])
                        elif filename.endswith(".docx"):
                            loader = Docx2txtLoader(str(save_path))
                            docs = loader.load()
                            if docs:
                                preview_text = docs[0].page_content[:500]
                                st.write(preview_text + ("..." if len(preview_text) == 500 else ""))
                            else:
                                st.warning("Empty DOCX file or couldn't extract text")
                    elif filename.endswith(".txt"):
                        with open(save_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        preview_text = content[:500]
                        st.write(preview_text + ("..." if len(preview_text) == 500 else ""))
                    st.caption(f"Preview of first content in {filename}")
            except Exception as e:
                st.error(f"Failed to generate preview: {str(e)}")

    st.markdown("---")


# Chat page
def reset_chat():
    st.session_state.messages = []
    save_session_state()
    gc.collect()

def render_chat_interface(rag):
    st.title("📄 Document Intelligence Assistant")
    
    if st.session_state.saved_files:
        st.success(f"✅ {len(st.session_state.saved_files)} documents loaded")
        col1, col2 = st.columns([6, 1])
        col2.button("Clear ↺", on_click=reset_chat)
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("Ask about your documents"):
            handle_user_query(prompt, rag)
    else:
        st.info("📤 Upload documents to begin analysis")

def handle_user_query(prompt, rag):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            for chunk in rag.query(prompt):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            # save_session_state()
        except Exception as e:
            st.error(f"Query error: {str(e)}")