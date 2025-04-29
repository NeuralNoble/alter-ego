from dotenv import load_dotenv; load_dotenv()
from pinecone import Pinecone
import os, json
from openai import OpenAI

INDEX_NAME = "personal-chatbot"

def load_chunks(filename="data/chunks.json"):
    """Load chunks from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def upsert_to_pinecone(chunks):
    """Upsert chunks to Pinecone"""
    # Initialize OpenAI client
    client = OpenAI()
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)
    
    # Process chunks in batches to avoid rate limits
    batch_size = 100
    total_chunks = len(chunks)
    
    print(f"Starting upsert of {total_chunks} chunks to Pinecone...")
    
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        batch_texts = [chunk["text"] for chunk in batch]
        
        # Get embeddings for the batch
        print(f"Getting embeddings for batch {i//batch_size + 1}...")
        embeddings = client.embeddings.create(
            input=batch_texts,
            model="text-embedding-3-small"
        ).data
        
        # Prepare vectors for upsert
        vectors = [
            {
                "id": f"chunk-{i + j}",
                "values": e.embedding,
                "metadata": {"text": batch[j]["text"]}
            }
            for j, e in enumerate(embeddings)
        ]
        
        # Upsert batch
        print(f"Upserting batch {i//batch_size + 1}...")
        index.upsert(vectors=vectors)
        
        # Print progress
        progress = min(i + batch_size, total_chunks)
        print(f"Progress: {progress}/{total_chunks} chunks processed")
    
    print("\nUpsert completed successfully!")
    print(f"Total chunks upserted: {total_chunks}")

if __name__ == "__main__":
    # Load existing chunks
    print("Loading chunks from data/chunks.json...")
    chunks = load_chunks()
    
    
    # Confirm before proceeding
    print("\nReady to upsert to Pinecone.")
    confirm = input("Do you want to proceed? (y/n): ")
    
    if confirm.lower() == 'y':
        upsert_to_pinecone(chunks)
    else:
        print("Upsert cancelled.") 