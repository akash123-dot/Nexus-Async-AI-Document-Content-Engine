from .Safety_domain import safety_domain, compute_temperature
from .content_planning import generate_planing
from .prompt_assembly import prompt_assembly
from .llm_generation import content_generation
from .web_summerize import summarize_web
from .save_database import save_database
from sqlalchemy.ext.asyncio import AsyncSession


async def intent_parser(db: AsyncSession, content: dict, question: str) -> str:

    try:
    
        safety_domain_content = await safety_domain(content=content)
        # print("passed safety domain")
        temperature = await compute_temperature(content=safety_domain_content)
        # print("passed temperature")
        strategy_planing = await generate_planing(question=question, content=safety_domain_content)
        # print("passed planing")
        prompt_building = await prompt_assembly(question=question, content=strategy_planing, planing=safety_domain_content)
        # print("passed prompt")

        if content["web_search"] == True or content["realtime_search"] == True:
            content_response = await content_generation(prompt=prompt_building, temperature=temperature, toolcall= lambda: summarize_web(question=question))
        else:
            content_response = await content_generation(prompt=prompt_building, temperature=temperature, toolcall=None)
        # print("passed content generation")
        await save_database(db=db, task_status=content_response["status"], task_result=content_response["content"], unique_task_id=content["unique_task_id"], user_id=content["user_id"])

    

    except Exception as e:
        raise 


    