from pydantic import BaseModel, EmailStr
from datetime import datetime


class SignUpSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
    
class LoginSchema(BaseModel):
    username: str
    password: str
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class FileMetadata(BaseModel):
   
    user_id: int
    file_name: str
    file_size: int
    file_type: str 
    extension: str
    storage_path: str

class AuthUserResponse(BaseModel):
    id: int
    username: str
    email: str
    message: str

    class Config:
        from_attributes = True  



class UserFileOut(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_size: int
    file_type: str
    extension: str
    storage_path: str
    created_at: datetime

    class Config:
        from_attributes = True  

class RetrieveAnswerSchema(BaseModel):
    question: str










class BlueskyConnectRequest(BaseModel):
    handle: str       # e.g. deyakash473.bsky.social
    app_password: str 


class PostRequest(BaseModel):
    text: str