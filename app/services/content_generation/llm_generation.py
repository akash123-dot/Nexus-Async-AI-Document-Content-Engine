import os
from dotenv import load_dotenv
from app.config.settings import llm
# load_dotenv()
import re

def clean_text(text: str) -> str:
   
    text = re.sub(r'\n{2,}', '\n', text)
   
    text = re.sub(r' {2,}', ' ', text)
 
    text = re.sub(r'\\n|\\t|\\r', ' ', text)
   
    text = text.strip()
    return text



async def content_generation(prompt: str, temperature: float, toolcall: callable = None) -> str:
    llm.temperature = temperature

    tool_output = ""
    if toolcall:
        raw_text = await toolcall() 
        tool_output = raw_text.strip()


    messages = [
        ("system", "You are a professional content generator. Your task is to process the provided "
            "news report based strictly on the user's instructions. If the report contradicts "
            "your internal knowledge, prioritize the information in the report."),

    ]

    if tool_output:
        human_text = f" Instructions:\n{prompt}\n\nHere is the source of the report:\n{tool_output}"
    else:
        human_text = prompt

    messages.append(("human", human_text))

    try:
        response = await llm.ainvoke(messages)

        clean_text = clean_text(response.content)


        return {"content": clean_text, "status": "success"}

    except Exception as e:
        return {"content": f"Error generating content: {e}", "status": "failed"}