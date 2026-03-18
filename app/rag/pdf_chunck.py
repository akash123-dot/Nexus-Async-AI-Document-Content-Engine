# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from pinecone import Pinecone
# from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import PyPDFLoader  
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re




def clean_pdf_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)  
    text = re.sub(r'[ \t]+', ' ', text)       
    text = re.sub(r' *\n *', '\n', text)     
    return text.strip()


def analyze_pdf(docs):
    total_chars = 0
    total_lines = 0

    valid_docs = [doc for doc in docs if doc.page_content.strip()]  

    for doc in valid_docs:
        text = doc.page_content
        total_chars += len(text)
        total_lines += text.count("\n")

    pages = len(valid_docs)
    if pages == 0:
        return {"pages": 0, "total_chars": 0, "avg_chars_per_page": 0,
                "avg_lines_per_page": 0}

    return {
        "pages": pages,
        "total_chars": total_chars,
        "avg_chars_per_page": total_chars / pages,
        "avg_lines_per_page": total_lines / pages,
    }



CHARS_PER_TOKEN = 4  

def choose_chunk_strategy(stats):
    avg_chars = stats.get("avg_chars_per_page", 0)
    avg_lines = stats.get("avg_lines_per_page", 0)

    if avg_chars == 0:
        return 256, 50

    # Convert character-based stats to token estimates
    avg_tokens_per_page = avg_chars / CHARS_PER_TOKEN
    avg_chars_per_line = avg_chars / avg_lines if avg_lines > 0 else avg_chars
    avg_tokens_per_line = avg_chars_per_line / CHARS_PER_TOKEN

    print(f"Estimated tokens/page: {avg_tokens_per_page:.0f}")
    print(f"Estimated tokens/line: {avg_tokens_per_line:.0f}")

    
    if avg_tokens_per_page < 200:        
        chunk_size = 128
        overlap = 25

    elif avg_tokens_per_page < 500:
        if avg_tokens_per_line < 10:     
            chunk_size = 256
            overlap = 50
        else:                           
            chunk_size = 384
            overlap = 75

    else:                                
        chunk_size = 512
        overlap = 100

    return chunk_size, overlap


async def read_pdf(directory):
    file_loder = PyPDFLoader(directory)
    documents = await file_loder.aload()

    for doc in documents:
        doc.page_content = clean_pdf_text(doc.page_content)

    stats = analyze_pdf(documents)          

    return documents, stats


async def chunks_pdf_data(docs,user_id, file_id, file_name, chunk_size, chunk_overlap):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            ". ",
            "? ",
            "! ",
            " ",
            ""
        ]
    )
    chunks = text_splitter.split_documents(docs)
    chunks = [c for c in chunks if len(c.page_content.strip()) > 50]

    for chunk in chunks:
        chunk.metadata["source"] = user_id
        chunk.metadata["doc_id"] = file_id
        chunk.metadata["file_name"] = file_name
        chunk.metadata["page"] = chunk.metadata.get("page")

    return chunks



