from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain_google_genai import ChatGoogleGenerativeAI
from pinecone import Pinecone
from app.config.settings import settings
from app.config.settings import llm

GOOGLE_API_KEY = settings.GOOGLE_API_KEY
PINECONE_API_KEY = settings.PINECONE_API_KEY
PINECONE_INDEX = settings.PINECONE_INDEX


# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=5,
#     convert_system_message_to_human=True,
#     api_key=GOOGLE_API_KEY
# )

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", api_key=GOOGLE_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

async def retrive_answer(question, user_id, file_id) -> dict:
    
    vector_store = PineconeVectorStore(embedding=embeddings,
                                       index=index,
                                       namespace=f"user_{user_id}",
                                       )
    

    comparison_keywords = ["difference", "compare", "vs", "versus", "contrast"]
    use_mmr = any(kw in question.lower() for kw in comparison_keywords)

    if use_mmr:
        result = await vector_store.amax_marginal_relevance_search(
            query=question, k=10, fetch_k=30, filter={"doc_id": file_id}
        )
    else:
        result_with_score = await vector_store.asimilarity_search_with_score(query=question,
                                                                         k=10,
                                                                         filter={"doc_id": file_id,}
                                                                                 )                                                                    
        valid_score = 0.4

        result = [doc for doc, score in result_with_score if score >= valid_score]
        
        if not result:
            result = [doc for doc, score in result_with_score[:5]]

    content = []
    for doc in result:
        file_name = doc.metadata.get('file_name', '')
        page = doc.metadata.get('page')
        page_info = f"[Source: {file_name} | Page: {page}]" if page is not None else f"[Source: {file_name}]"
        content.append(f"{page_info}\n{doc.page_content}")
    

      
    return {"content": content}





prompt = ChatPromptTemplate.from_messages([
("system", """
You are a strict QA assistant.

Rules:
- Answer ONLY from the provided context
- If the context contains enough info to make a logical inference, provide it
- If the answer is not present → say "I cannot find this in the provided document"
- Be precise and structured
- If source/page info is available in context, reference it in your answer

Context:
{context}
"""),
("human", "{question}")
])

rag_chain = prompt | llm




async def generate_answer(question: str, user_id: int, file_id: int):

    if len(question.split(" ")) < 3:
        question = f"Explain the {question} section of the document"

    docs = await retrive_answer(question=question, user_id=user_id, file_id=file_id)
    content = docs["content"]
    # print(content)
    response = await rag_chain.ainvoke({
        "context": "\n\n".join(content),
        "question": question,
    })
    # print(response.content)
    # print(response.additional_kwargs)

    return response.content



