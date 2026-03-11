from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from dotenv import load_dotenv
import asyncio
import os
load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", api_key=GOOGLE_API_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("vectortesting")

async def save_to_pinecone(chunks, user_id):
    try:
        print(f"Attempting to save {len(chunks)} chunks to index.")



        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            namespace = f"user_{user_id}"
        )

        await vector_store.aadd_documents(chunks)

        print("Successfully saved to Pinecone.")
        return True
    
    
    except Exception as e:
        print(f"PINECONE ERROR: {e}") 
       
        print(f"Error Type: {type(e)}")
        return False
    



