from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import re

def clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)   
    text = re.sub(r'[ \t]+', ' ', text)       
    text = re.sub(r' *\n *', '\n', text)      
    return text.strip()



def analyze_text(docs):
    total_chars = 0
    total_lines = 0

    for doc in docs:
        text = doc.page_content
        total_chars += len(text)
        total_lines += text.count("\n")

    
    return {
        "total_chars": total_chars,
        "total_lines": total_lines,
        "avg_chars_per_line": total_chars / total_lines if total_lines > 0 else total_chars
    }



# CHARS_PER_TOKEN = 4 

def choose_chunk_strategy(stats):
    avg_chars_per_line = stats.get("avg_chars_per_line", 0)

    if avg_chars_per_line == 0:
        return 256, 50


    if avg_chars_per_line < 40:
        return 256, 50    


    elif avg_chars_per_line < 80:
        return 384, 75   

    
    else:
        return 512, 100  





async def read_text(directory):
    file_loader = TextLoader(directory, encoding="utf-8")
    documents = await file_loader.aload()

    for doc in documents:
        doc.page_content = clean_text(doc.page_content)

    stats = analyze_text(documents)
    return documents, stats

async def chunks_text_data(docs, user_id, file_id, file_name, chunk_size, chunk_overlap):
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
        

    return chunks