from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.config.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4


class AuthUser(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

class UserFileMetadata(Base):
    __tablename__ = "user_file_metadata"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=True)
    extension = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("AuthUser", backref="user_file_metadata")



class ContentGenerationTask(Base):
    __tablename__ = "content_generation_tasks"

    id = Column(Integer, primary_key=True)
    unique_task_id = Column(String, unique=True, nullable=False, index=True, default=uuid4)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    task_status = Column(String, nullable=False, default="pending")
    task_result = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("AuthUser", backref="content_generation_tasks")



class UserSocialAccounts(Base):
    __tablename__ = "user_social_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    social_platform = Column(String, nullable=False)
    app_password  = Column(String, nullable=False)
    handle = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("AuthUser", backref="user_social_accounts")



