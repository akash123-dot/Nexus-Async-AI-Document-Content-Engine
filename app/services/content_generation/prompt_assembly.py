import json

import re

def clean_json(text: str) -> str:
    text = text.strip()

    
    text = re.sub(r"^```json\s*", "", text)

    
    text = re.sub(r"\s*```$", "", text)

    return text.strip()




async def prompt_assembly(question, content, planing):
    # print("CONTENT TYPE:", type(content))
    # print("CONTENT VALUE:", repr(content))
    # print("PLANNING TYPE:", type(planing))
    # print("PLANNING VALUE:", repr(planing))
    content = clean_json(content)
    # 1. Parse Inputs
    if isinstance(content, str):
        contents = json.loads(content)
    elif isinstance(content, dict):
        contents = content
    # contents = json.loads(content)
    else: 
        raise ValueError("Invalid content type. Expected str or dict.")
    
    if isinstance(planing, str):
        planing_data = json.loads(planing)
    elif isinstance(planing, dict):
        planing_data = planing
    else: 
        raise ValueError("Invalid planing type. Expected str or dict.")

    # 2. Extract Variables
    # Content Logic
    sections = contents.get("sections", [])
    depth_allocation = contents.get("depth_allocation", {})
    flow_type = contents.get("flow_type", "Standard")

    # Planning/Meta
    content_type = planing_data.get("content_type", "Article")
    domain = planing_data.get("domain", "General")
    tone = planing_data.get("tone", "Neutral")
    audience = planing_data.get("audience", "General Public")
    creativity_level = planing_data.get("creativity_level", "Medium")
    writing_style = planing_data.get("writing_style", "Descriptive")
    
    # Safety & Config
    risk_level = planing_data.get("risk_level", "Low")
    sensitive_flag = planing_data.get("sensitive_topic_flag", False)
    req_disclaimer = planing_data.get("requires_disclaimer", False)
    
    # Specifics (Formatting lists for better readability)
    keywords = ", ".join(planing_data.get("keywords", []))
    target_word_count = planing_data.get("target_word_count", "Flexible")
    include_examples = "Yes" if planing_data.get("include_examples") else "No"
    include_citations = "Yes" if planing_data.get("include_citations") else "No"
    cta = planing_data.get("call_to_action", "None")
    instructions = planing_data.get("special_instructions", "None")
    language = planing_data.get("language", "English")

    # 3. Construct the Role Dynamically
    role_definition = f"You are an expert {domain} Content Strategist and Writer."

    section_block = "\n".join([f"{i+1}. {s}" for i, s in enumerate(sections)])
    depth_block = "\n".join(
    [f"- {k.replace('_', ' ').title()}: {v} detail" for k, v in depth_allocation.items()] )
    
    prompt = f"""
    ### SYSTEM ROLE
    {role_definition}
    Language: {language}

    ### CORE TASK
    Write a {content_type} regarding the following topic: "{question}"

    ### TARGET AUDIENCE PROFILE
    - **Who:** {audience}
    - **Tone:** {tone}
    - **Style:** {writing_style}
    - **Creativity Level:** {creativity_level} (Low=Factual, High=Imaginative)

    ### CONTENT SPECIFICATIONS
    1. **Word Count Goal:** {target_word_count} words
    2. **Keywords to Integrate:** {keywords}
    3. **Include Real-World Examples:** {include_examples}
    4. **Include Citations/References:** {include_citations}
    5. **Call to Action (End):** {cta}

    ### STRUCTURAL BLUEPRINT
    You must follow this flow strictly.
    **Flow Strategy:** {flow_type}

    **Section Outline:**
    {section_block}

    **Depth & Weighting (Focus Allocation):**
    {depth_block}
    *(Allocate content volume and detail based on these weights)*

    ### SAFETY & COMPLIANCE
    - **Risk Level:** {risk_level}
    - **Sensitive Topic:** {sensitive_flag}
    - **Mandatory Disclaimer:** {"You must include a disclaimer stating this is for informational purposes only." if req_disclaimer else "Not required."}

    ### SPECIAL INSTRUCTIONS
    {instructions}

    ### OUTPUT FORMAT
    - Do NOT use Markdown syntax.
    - Do NOT use symbols such as #, ##, **, *, or ---.
    - Do NOT bold any words.
    - Do NOT italicize text.
    - Do NOT add decorative separators.
    - Headings must be written as plain text without symbols
    """

    return prompt