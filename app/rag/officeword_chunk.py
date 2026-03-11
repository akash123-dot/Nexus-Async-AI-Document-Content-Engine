from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


def clean_docx_text(text: str) -> str:
    text = re.sub(r'\n\s*\n', '\n\n', text)  
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  
    text = re.sub(r'\s+', ' ', text)  
    return text.strip()


def analyze_docx(docs):
    total_chars = 0
    total_lines = 0

    for doc in docs:
        text = doc.page_content
        total_chars += len(text)
        total_lines += text.count("\n")

    pages = len(docs)

    avg_chars_per_page = total_chars / pages
    avg_lines_per_page = total_lines / pages

    return {
        "pages": pages,
        "total_chars": total_chars,
        "avg_chars_per_page": avg_chars_per_page,
        "avg_lines_per_page": avg_lines_per_page
    }



def choose_chunk_strategy(stats):

    avg_chars = stats.get("avg_chars_per_page", 0)
    avg_lines = stats.get("avg_lines_per_page", 0)

    print(avg_chars)
    print(avg_lines)

    if avg_chars == 0:
        return 256, 50  

    avg_chars_per_line = avg_chars / avg_lines if avg_lines > 0 else avg_chars

    if avg_chars < 800:
       
        chunk_size = 150  
        overlap = 30

    elif avg_chars < 2000:
        if avg_chars_per_line < 40:
        
            chunk_size = 200  
            overlap = 40
        else:

            chunk_size = 300  
            overlap = 60

    else:
        
        chunk_size = 400  
        overlap = 80      

    return chunk_size, overlap


async def read_doc(directory):
    file_loder = UnstructuredWordDocumentLoader(directory, mode="single")
    documents = await file_loder.aload()

    stats = analyze_docx(documents)

    for doc in documents:
        doc.page_content = clean_docx_text(doc.page_content)
    return documents, stats

async def chunks_doc_data(docs,user_id, file_id, file_name, chunk_size=100, chunk_overlap=20):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
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
        chunk.metadata["page"] = chunk.metadata.get("page_number", "N/A")

    return chunks
