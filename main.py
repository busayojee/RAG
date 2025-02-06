from rag.indexer import PyPDFLoader, Docx2txtLoader, TextLoader
from rag import RAGSystem
import streamlit as st
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer
import os
import pickle
import gc
import base64

def save_session_state():
    try:
        with open('session_state.pkl', 'wb') as f:
            # Filter out any keys starting with "delbtn_"
            state = {k: v for k, v in st.session_state.items() if not k.startswith("delbtn_")}
            print(f"saving session_state: {state}")
            pickle.dump(state, f)
    except Exception as e:
        print(f"Error during saving session state: {e}")

def load_session_state():
    if os.path.exists('session_state.pkl'):
        try:
            with open('session_state.pkl', 'rb') as f:
                loaded_state = pickle.load(f)
                for k, v in loaded_state.items():
                    if not k.startswith("delbtn_"):
                        st.session_state[k] = v
        except Exception as e:
            print(f"Error during loading session state: {e}")
    else:
        print("session_state.pkl not found")
    return None

load_session_state()

# Styling and setup
primary_color = "#007BFF"  # Bright blue for primary buttons
secondary_color = "#FFC107"  # Amber for secondary buttons
background_color = "#F8F9FA"  # Light gray for the main background
sidebar_background = "#2C2F33"  # Dark gray for sidebar (better contrast)
text_color = "#212529"  # Dark gray for content text
sidebar_text_color = "#FFFFFF"  # White text for sidebar
header_text_color = "#000000" 

path_ = "documents"
Path(path_).mkdir(exist_ok=True)

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


# st.title("📄 Build a RAG System with DeepSeek R1 & Ollama")
# Initialize your RAG system (do not store it in session state)
rag_system = RAGSystem(path_)

# Ensure a list exists for saved files
if 'saved_files' not in st.session_state:
    st.session_state.saved_files = []
if 'file_previews' not in st.session_state:
    st.session_state.file_previews = {}

def handle_file_deletion(filename):
    try:
        # Remove from local storage
        file_path = Path(path_, filename)
        if file_path.exists():
            file_path.unlink()
        rag_system.indexer.update_vector_db()
        if filename in st.session_state.saved_files:
            st.session_state.saved_files.remove(filename)
        if filename in st.session_state.file_previews:
            del st.session_state.file_previews[filename]
        save_session_state()
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting file {filename}: {str(e)}")

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    save_session_state()
    gc.collect()



with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1. Upload a PDF file using the uploader below.
    2. Ask questions related to the document.
    3. The system will retrieve relevant content and provide a concise answer.
    """)
    st.header("📁 Upload Documents")
    files = st.file_uploader("Upload your Documents here", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    
    if files:
        for file in files:
            if file.name not in st.session_state.saved_files:
                # Save file to disk
                save_path = Path(path_, file.name)
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                
                # Add to session state
                st.session_state.saved_files.append(file.name)
                st.session_state.file_previews[file.name] = file.name
        
        # Update vector DB
        rag_system.indexer.update_vector_db()
        save_session_state()
        # st.rerun()
    
    st.markdown("---")
    st.subheader("Uploaded Files")
    if st.session_state.saved_files:
        # Display each saved file with a delete button
        for filename in st.session_state.saved_files:
            cols = st.columns([0.8, 0.2])
            cols[0].write(filename)
            widget_key = f"delbtn_{filename.replace('.', '_').replace(' ', '_')}"
            if cols[1].button("❌", key=widget_key):
                handle_file_deletion(filename)
    else:
        st.write("No files uploaded yet.")
    
    st.markdown("---")
    st.subheader("File Previews")
    for filename in st.session_state.saved_files:
        with st.expander(f"📄 {filename}", expanded=True):
            try:
                name = st.session_state.file_previews.get(filename, None)
                if name:
                    save_path = Path(path_, filename)
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

# current_files = set(st.session_state.saved_files)
# if current_files:
#     try:
#         rag_system.indexer.update_vector_db()
#         st.success("Document processing completed!")
#     except Exception as e:
#         st.error(f"Error updating documents: {str(e)}")
if st.session_state.saved_files:
    st.success(f"{len(st.session_state.saved_files)} documents loaded in vector DB")
    
    col1, col2 = st.columns([6,1])
    with col2:
        st.button("Clear ↺", on_click=reset_chat)
    if "messages" not in st.session_state:
        reset_chat()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            streaming_response = rag_system.query(prompt)
            
            for chunk in streaming_response:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
else:
    st.info("Please upload a PDF file to start.")

save_session_state()
