from pinecone import Pinecone
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
import os
load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("vectortesting")



async def delete_user_database(user_id:int, file_id:int):
    try:
        await run_in_threadpool(
            index.delete,
            namespace=f"user_{user_id}",
            filter={"doc_id": {"$eq": file_id}}
        )

        return True

    except Exception as e:
        raise e
