from enum import Enum
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime 


# Enum Definitions for Categorical Choices
class ContentType(str, Enum):
    blog = "blog"
    essay = "essay"
    report = "report"
    article = "article"
    email = "email"
    story = "story"
    tweet = "tweet"
    social_post = "social_post"
    newsletter = "newsletter"
    whitepaper = "whitepaper"
    case_study = "case_study"
    product_description = "product_description"
    press_release = "press_release"
    script = "script"
    poem = "poem"


class Domain(str, Enum):
    politics = "politics"
    economy = "economy"
    technology = "technology"
    health = "health"    
    finance = "finance"
    science = "science"
    education = "education"  
    entertainment = "entertainment"
    sports = "sports" 
    business = "business"
    lifestyle = "lifestyle" 
    travel = "travel"
    food = "food" #
    fashion = "fashion"
    environment = "environment"
    culture = "culture"
    marketing = "marketing"



class Tone(str, Enum):
    analytical = "analytical"
    casual = "casual"
    persuasive = "persuasive"
    neutral = "neutral"
    formal = "formal"
    friendly = "friendly"
    professional = "professional"
    humorous = "humorous"
    inspirational = "inspirational"
    authoritative = "authoritative"
    conversational = "conversational"
    empathetic = "empathetic"


class Length(str, Enum):
    very_short = "very_short"  # < 200 words
    short = "short"  # 200-500 words
    medium = "medium"  # 500-1000 words
    long = "long"  # 1000-2000 words
    very_long = "very_long"  # > 2000 words


class Audience(str, Enum):
    general = "general"
    expert = "expert"
    beginner = "beginner"
    intermediate = "intermediate"
    children = "children"
    teenagers = "teenagers"
    professionals = "professionals"
    academics = "academics"


class Creativity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class StructureType(str, Enum):
    none = "none"
    basic = "basic"
    detailed = "detailed"
    custom = "custom"


class WritingStyle(str, Enum):
    descriptive = "descriptive"
    narrative = "narrative"
    expository = "expository"
    argumentative = "argumentative"
    technical = "technical"
    creative = "creative"


# Main Pydantic Schema
class ContentGenerationConfig(BaseModel):
    # Categorical choices (enums)
    content_type: ContentType 
    domain: Domain
    tone: Tone = Tone.neutral
    length: Length = Length.medium
    audience: Audience = Audience.general
    creativity_level: Creativity = Creativity.medium
    structure_type: StructureType = StructureType.basic
    writing_style: Optional[WritingStyle] = None
    topic: str
    #realtime search
    web_search: bool = False
    realtime_search: bool = False
    # Open-ended fields
    keywords: List[str] = Field(default_factory=list, description="Key phrases to include")
    language: str = Field(default="English", description="Output language")
    
    # optional fields
    target_word_count: Optional[int] = Field(None, description="Specific word count target")
    include_examples: bool = Field(default=False, description="Include real-world examples")
    include_statistics: bool = Field(default=False, description="Include data and statistics")
    include_citations: bool = Field(default=False, description="Include sources and references")
    call_to_action: Optional[str] = Field(None, description="Specific CTA to include")
    # avoid_topics: List[str] = Field(default_factory=list, description="Topics to avoid")
    special_instructions: Optional[str] = Field(None, description="Any additional requirements")
    
    class Config:
        use_enum_values = True



class ContentGenerationMetadata(BaseModel):
    unique_task_id: str 
    user_id: int
    task_type: str



class SingleTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question: str
    task_status: str
    task_result: Optional[str]






DataT = TypeVar("DataT")


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unique_task_id: str
    task_type: str
    task_status: str
    task_result: Optional[str]
    created_at: datetime


class TaskListResponse(BaseModel, Generic[DataT]):
 
    data: List[TaskOut]
    next_cursor: Optional[str] = None
    has_next: bool