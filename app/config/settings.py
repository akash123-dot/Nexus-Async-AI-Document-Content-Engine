import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic_settings import BaseSettings
load_dotenv()




# class XToken:
#     X_CLIENT_ID = os.getenv("X_CLIENT_ID")
#     X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
#     X_REDIRECT_URI = os.getenv("X_REDIRECT_URI")







class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    #redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_MAX_CONNECTIONS: int = 20

    # RabbitMQ
    RABBITMQ_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


    # Google / LLM
    GOOGLE_API_KEY: str

     # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    BUCKET_NAME: str

    # pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX: str

    # news api
    NEWS_API_KEY: str

    # Bluesky secret password
    BLUESKY_PASSWORD_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()








llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=30,
    max_retries=3,
    api_key=settings.GOOGLE_API_KEY
)