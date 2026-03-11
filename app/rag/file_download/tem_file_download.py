import tempfile
import os
from supabase import create_async_client, AsyncClient
from app.config.settings import BUCKET_NAME
from app.rag.pdf_chunck import read_pdf, chunks_pdf_data, choose_chunk_strategy
from app.rag.officeword_chunk import read_doc, chunks_doc_data, choose_chunk_strategy
from app.rag.text_file_chunck import read_text, chunks_text_data, choose_chunk_strategy
from app.rag.save_vectordb import save_to_pinecone
# from dotenv import load_dotenv

# load_dotenv()


# BUCKET_NAME = "file_store"
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
# supabase : AsyncClient = create_async_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


PROCESSOR_MAP = {
    ".pdf": (read_pdf, choose_chunk_strategy, chunks_pdf_data),
    ".docx": (read_doc, choose_chunk_strategy, chunks_doc_data),
    ".doc": (read_doc,  choose_chunk_strategy, chunks_doc_data),
    ".txt": (read_text, choose_chunk_strategy, chunks_text_data),
    # ".json": (read_json, chunks_json_data) # Add when ready
    }

async def processing_file_message(file_path, user_id, file_id, file_name, supabase:AsyncClient):


    file_data = await supabase.storage.from_(BUCKET_NAME).download(file_path)
    
    suffix = os.path.splitext(file_path)[1].lower()

    if suffix not in PROCESSOR_MAP:
        return False

  

    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    

    try:
       
        with open(temp_path, "wb") as f:
            f.write(file_data)

        read_data_func, strategy_func, chunks_data_func = PROCESSOR_MAP[suffix]

        read_data, stats = await read_data_func(temp_path)

        chunk_size, overlap = strategy_func(stats)
      
        print("Chunk size:", chunk_size)
        print("Overlap:", overlap)
        # print(read_data)
        print(stats)
      
        chunks = await chunks_data_func(
            docs=read_data,
            user_id=user_id,
            file_id=file_id,
            file_name=file_name,
            chunk_size=chunk_size,
            chunk_overlap=overlap
        )

        # print("Namespace:", user_id)
        # print("Chunks count:", len(chunks))

        status = await save_to_pinecone(chunks, user_id)

        print("Status:", status)
        return bool(status)

    finally:
      
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass