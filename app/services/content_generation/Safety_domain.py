from app.schemas.content_gen_schemas import Creativity,Tone, WritingStyle, ContentType, Audience




async def safety_domain(content: dict):
    domains = ["politics", "health", "finance", "legal" ]
    has_domain = any(domain in content["domain"] for domain in domains)
    if has_domain:
        content.update({"risk_level": "high",
                        "sensitive_topic_flag": True,
                        "requires_disclaimer": True
                        })

    else:
        content.update({"risk_level": "low",
                        "sensitive_topic_flag": False,
                        "requires_disclaimer": False
                        })

    return content




async def compute_temperature(content: dict):
    
   
    creativity_base = {
        Creativity.low.value: 0.2,
        Creativity.medium.value: 0.5,
        Creativity.high.value: 0.85,
    }

    temperature = creativity_base.get(
        content.get("creativity", Creativity.medium.value),
        0.5,
    )

  
    tone_adjustment = {
        Tone.analytical.value: -0.2,
        Tone.formal.value: -0.2,
        Tone.authoritative.value: -0.15,
        Tone.professional.value: -0.1,
        Tone.neutral.value: -0.05,

        Tone.conversational.value: 0.05,
        Tone.friendly.value: 0.1,
        Tone.persuasive.value: 0.1,
        Tone.empathetic.value: 0.15,
        Tone.inspirational.value: 0.2,
        Tone.humorous.value: 0.25,
        Tone.casual.value: 0.2,
    }

    temperature += tone_adjustment.get(content.get("tone"), 0.0)

    style_adjustment = {
        WritingStyle.technical.value: -0.25,
        WritingStyle.expository.value: -0.15,
        WritingStyle.argumentative.value: -0.1,
        WritingStyle.descriptive.value: 0.05,
        WritingStyle.narrative.value: 0.15,
        WritingStyle.creative.value: 0.25,
    }

    temperature += style_adjustment.get(content.get("writing_style"), 0.0)


    content_type_caps = {
        ContentType.tweet.value: 0.8,
        ContentType.social_post.value: 0.85,
        ContentType.poem.value: 0.95,
        ContentType.story.value: 0.9,

        ContentType.report.value: 0.4,
        ContentType.whitepaper.value: 0.35,
        ContentType.case_study.value: 0.4,
        ContentType.press_release.value: 0.45,
        ContentType.email.value: 0.5,
    }

    max_temp_by_type = content_type_caps.get(
        content.get("content_type"), 1.0
    )


    audience_caps = {
        Audience.children.value: 0.6,
        Audience.beginner.value: 0.5,
        Audience.general.value: 0.6,
        Audience.intermediate.value: 0.55,
        Audience.professionals.value: 0.45,
        Audience.expert.value: 0.4,
        Audience.academics.value: 0.3,
    }

    max_temp_by_audience = audience_caps.get(
        content.get("audience"), 1.0
    )


    if content.get("risk_level") == "high":
        max_temp_by_safety = content.get("max_temperature", 0.3)
    else:
        max_temp_by_safety = 1.0

    # Final clamp
    max_allowed = min(
        max_temp_by_type,
        max_temp_by_audience,
        max_temp_by_safety,
    )

    temperature = max(0.0, min(temperature, max_allowed))
    round_temperature = round(temperature, 2)

    # content.update({"temperature": round_temperature})

    # return content

    return round_temperature
