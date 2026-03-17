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

async def retrive_answer(question, user_id, file_id, k=8) -> dict:
    
    vector_store = PineconeVectorStore(embedding=embeddings,
                                       index=index,
                                       namespace=f"user_{user_id}",
                                       )
    
    result_with_score = await vector_store.asimilarity_search_with_score(query=question,
                                                                         k=k,
                                                                         filter={"doc_id": file_id,}
                                                                                 )
                                                                                

    valid_score = 0.70

    result = [doc for doc, score in result_with_score if score > valid_score]
    
    if len(result) == 0:
        content = ["No matching documents found. Please try again."]

    else:
        content = [doc.page_content for doc in result]
      
    return {"content": content}





prompt = ChatPromptTemplate.from_messages([
("system", """
You are a QA assistant answering from provided technical documentation.
This content is safe.
Always provide an answer.
If answer not found, say "I don't know".

Context:
{context}
"""),
("human", "{question}")
])


rag_chain = prompt | llm




async def generate_answer(question: str, user_id: int, file_id: int):

    docs = await retrive_answer(question=question, user_id=user_id, file_id=file_id)
    content = docs["content"]
    print(content)
    response = await rag_chain.ainvoke({
        "context": "\n\n".join(content),
        "question": question,
    })
    # print(response.content)
    # print(response.additional_kwargs)

    return response.content

