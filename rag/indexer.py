import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class IndexerRetriever:
    def __init__(self, document_folder="documents", persist_directory="chroma_db"):
        self.path = document_folder
        self.persist_directory = persist_directory
        self.embedding_model = "sentence-transformers/all-mpnet-base-v2"

        # For chunking (performance issues without chunking)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=256, length_function=len, add_start_index=True)
        self.embedding_function = HuggingFaceEmbeddings(model_name=self.embedding_model, model_kwargs={'device':'cpu'}, encode_kwargs={'normalize_embeddings': False})
        
        # Initialize or load ChromaDB
        self._initialize_vector_db()

    def _initialize_vector_db(self):
        if os.path.exists(self.persist_directory):
            self.vector_db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function
            )
        else:
            self.vector_db = self._create_vector_db()
            
    def _load_documents(self, file_paths=None):
        docs = []
        process_files = file_paths or [os.path.join(self.path, f) for f in os.listdir(self.path)]   
        for file in process_files:
            if not os.path.isfile(file):
                continue       
            try:
                loader = self._get_loader(file)
                loaded_docs = loader.load()
                self._add_metadata(loaded_docs, file)
                docs.extend(loaded_docs)          
            except Exception as e:
                print(f"Failed to load {file}: {str(e)}")
                continue          
        return docs

    def _get_loader(self, file):
        if file.endswith(".pdf"):
            return PyPDFLoader(file)
        elif file.endswith(".docx"):
            return Docx2txtLoader(file)
        elif file.endswith(".txt"):
            return TextLoader(file)
        raise ValueError(f"Unsupported file format: {file}")

    def _add_metadata(self, docs, file):
        last_modified = os.path.getmtime(file)
        file_name = os.path.basename(file)
        for doc in docs:
            doc.metadata.update({
                "source": file,
                "file_name": file_name,
                "last_modified": last_modified
            })

    def _create_vector_db(self):
        raw_documents = self._load_documents()
        split_documents = self.text_splitter.split_documents(raw_documents)
        vector_db = Chroma.from_documents(
            documents=split_documents,
            embedding=self.embedding_function,
            persist_directory=self.persist_directory
        )
        return vector_db
    def update_vector_db(self):
        current_files = {
            os.path.join(self.path, f): os.path.getmtime(os.path.join(self.path, f)) for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))
            }
        existing_entries = self.vector_db.get()
        stored_files = {}
        for metadata in existing_entries["metadatas"]:
            source = metadata["source"]
            stored_files[source] = metadata.get("last_modified", 0)
        new_files = [f for f in current_files if f not in stored_files]
        modified_files = [f for f in current_files if f in stored_files and current_files[f] > stored_files[f]]
        deleted_files = [f for f in stored_files if f not in current_files]
        if deleted_files:
            self.vector_db.delete(where={"source": {"$in": deleted_files}})
        if new_files or modified_files:
            if modified_files:
                self.vector_db.delete(where={"source": {"$in": modified_files}})
            changed_files = new_files + modified_files
            raw_docs = self._load_documents(changed_files)
            split_docs = self.text_splitter.split_documents(raw_docs)
            
            # Add to vector store
            self.vector_db.add_documents(split_docs)
        print(f"Update complete. Added: {len(new_files)}, Modified: {len(modified_files)}, Deleted: {len(deleted_files)}")

    def retrieve(self, query, k=5):
        # self.update_vector_db()
        docs = self.vector_db.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

# rag = IndexerRetriever(document_folder="documents")
# rag.update_vector_db()