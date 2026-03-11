from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import llm
import json





prompt = ChatPromptTemplate.from_messages([
("system", """
### ROLE
You are a Senior Content Strategist and Data Architect. Your task is to transform a User Question and a Configuration JSON into a structured Content Blueprint JSON.


### INSTRUCTIONS & LOGIC
1. ANALYSIS: Analyze the 'ContentType' and 'Domain' to determine the thematic direction.
2. SECTION SCALING (STRICT RULE): The 'Length' parameter determines the exact number of items in the "sections" array:
   - "Very Short": 1-2 sections
   - "Short": 3-5 sections
   - "Medium": 6-9 sections
   - "Long": 10-14 sections
   - "Very Long": 15-18 sections
3. TONE & STYLE: Adapt the section titles based on 'Tone', 'WritingStyle', and 'Audience'.
4. RISK HANDLING: If 'risk_level' is high or 'sensitive_topic_flag' is true, include sections for "Nuanced Perspectives" or "Balanced Analysis".
5. OUTPUT FORMAT: Return ONLY a valid JSON object. No preamble, no conversational text, no markdown blocks unless requested.

### OUTPUT STRUCTURE
{{
  "metadata_summary": {{
    "target_length_count": "number of sections decided",
    "disclaimer_required": "boolean based on requires_disclaimer"
  }},
  "sections": [
    "Title of Section 1",
    "Title of Section 2",
    ...
  ],
  "depth_allocation": {{
    "intro": "short/medium/long",
    "body_sections": "short/medium/long",
    "conclusion": "short/medium/long",
    
  }},
  "flow_type": "e.g., analytical_progression, chronological, problem-solution, or argumentative ... etc.",
}}

Context:
{context}
"""),
("human", "{question}")
])


chain = prompt | llm


async def generate_planing(question: str, content: dict):
  # print("CONTENT TYPE:", type(content))
  # print("CONTENT VALUE:", repr(content))
  content = json.dumps(content, indent=2)
   
  response = await chain.ainvoke({
      "context": content,
      "question": question,
    })
  
  return response.content