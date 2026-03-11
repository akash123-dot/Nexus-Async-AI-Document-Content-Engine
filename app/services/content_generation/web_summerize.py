import requests 
import re
from app.config.settings import llm, NEWS_API_KEY





async def search_web(question:str)->str:
    raw_text = ""
    news = f"https://newsapi.org/v2/everything?q={question}&from=2026-03-02&to=2026-03-02&sortBy=popularity&apiKey={NEWS_API_KEY}"

    response = requests.get(news)

    data = response.json()

    for artical in data["articles"]:
        text =artical["content"]
        raw_text += text

    clean_text = re.sub(r'\[\+\d+ chars\]', '', raw_text)

    clean_text = re.sub(r'\n+', '\n', clean_text).strip()
    max_chars = 2000  
    short_text = clean_text[:max_chars] + "..." if len(clean_text) > max_chars else clean_text

    return short_text


async def summarize_web(question: str) -> str:
    result = await search_web(question)
    
    messages = [
       
        ("system", "You are a professional content generator and summarizer. Summarize the text concisely and point out."),
        
        ("human", f"Summarize the following news report:\n\n{result}")
    ]
    
    try:
        response = await llm.ainvoke(messages)

        return response.content
    
    except Exception as e:
        return f"Error generating content"

    