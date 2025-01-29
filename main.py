from rag.indexer import IndexerRetriever
from rag import RAGSystem

rags = IndexerRetriever(document_folder="documents")
rag = RAGSystem()
question = "what is Nigeria's national anthem?"
relevant_docs = rags.retrieve(question, k=3)

print(f"Relevant documents for '{question}':")
for i, doc in enumerate(relevant_docs):
    print(f"\nDocument {i+1}:")
    print(doc[:500] + "...")

print(rag.query(question=question))
