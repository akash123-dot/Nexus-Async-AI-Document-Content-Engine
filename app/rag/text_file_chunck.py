from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader




def analyze_text(docs):
    total_chars = 0
    total_lines = 0

    for doc in docs:
        text = doc.page_content
        total_chars += len(text)
        total_lines += text.count("\n")

    pages = len(docs)

   

    return {
    "pages": pages,
    "total_chars": total_chars,
    "avg_chars_per_page": total_chars / pages if pages > 0 else 0,
    "avg_lines_per_page": total_lines / pages if pages > 0 else 0,
    "avg_chars_per_line": total_chars / total_lines if total_lines > 0 else total_chars
    }



def choose_chunk_strategy(stats):

    avg_chars = stats.get("avg_chars_per_page", 0)
    avg_lines = stats.get("avg_lines_per_page", 0)

    if avg_chars == 0:
        return 256, 50

    avg_chars_per_line = stats.get("avg_chars_per_line") or (
        avg_chars / avg_lines if avg_lines > 0 else avg_chars)



    if avg_chars_per_line < 40:
        return 200, 40   
    elif avg_chars_per_line < 80:
        return 300, 60   
    else:
        return 400, 80   





async def read_text(directory):
    file_loder = TextLoader(directory, encoding="utf-8")
    documents = await file_loder.aload()
    stats = analyze_text(documents)
    return documents, stats

async def chunks_text_data(docs, user_id, file_id, file_name, chunk_size=256, chunk_overlap=50):
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