import os
from dotenv import load_dotenv
from app.config.settings import llm
load_dotenv()



async def content_generation(prompt: str, temperature: float, toolcall: callable = None) -> str:
    llm.temperature = temperature

    tool_output = ""
    if toolcall:
        raw_text = await toolcall() 
        tool_output = raw_text.strip()


    messages = [
        ("system", "You are a professional content generator."),

    ]

    if tool_output:
        human_text = f"{prompt}\n\nHere is the news report to summarize:\n{tool_output}"
    else:
        human_text = prompt

    messages.append(("human", human_text))

    try:
        response = await llm.ainvoke(messages)

        clean_text = " ".join(response.content.split())

        return {"content": clean_text, "status": "success"}

    except Exception as e:
        return {"content": f"Error generating content: {e}", "status": "failed"}