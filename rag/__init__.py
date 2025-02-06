from .indexer import IndexerRetriever 
from .generator import Generator

class RAGSystem:
    def __init__(self, document_folder="documents"):
        self.indexer = IndexerRetriever(document_folder)
        self.generator = Generator()
    
    def query(self, question, k=3):
        context = self.indexer.retrieve(question, k=k)
        response = self.generator.generate(question, context)
        return response

# rags = IndexerRetriever(document_folder="documents")
# rag = RAGSystem()
# question = "What's up"
# relevant_docs = rags.retrieve(question, k=3)

# print(f"Relevant documents for '{question}':")
# for i, doc in enumerate(relevant_docs):
#     print(f"\nDocument {i+1}:")
#     print(doc[:500] + "...")