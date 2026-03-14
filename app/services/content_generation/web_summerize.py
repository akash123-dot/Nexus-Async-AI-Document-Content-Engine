import requests
from datetime import datetime, timedelta 
import re
from app.config.settings import llm, settings

NEWS_API_KEY = settings.NEWS_API_KEY


today = datetime.today()
from_date = today - timedelta(days=10)




async def search_web(question:str)->str:
    raw_text = ""
    news = f"https://newsapi.org/v2/everything?q={question}&from={from_date.strftime('%Y-%m-%d')}&to={today.strftime('%Y-%m-%d')}&sortBy=relevancy&apiKey={NEWS_API_KEY}"

    response = requests.get(news)

    if response.status_code != 200:
        return "No news found"

    data = response.json()

    for artical in data["articles"]:
        text =artical["content"]
        raw_text += text

    clean_text = re.sub(r'\[\+\d+ chars\]', '', raw_text)

    clean_text = re.sub(r'\n+', '\n', clean_text).strip()
    max_chars = 3000  
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

        print(f"web_summary: {response.content}")

        return response.content
    
    except Exception as e:
        return f"Error generating content"

    