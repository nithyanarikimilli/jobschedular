from pydantic_settings import BaseSettings
from pydantic import Field
import os
from dotenv import load_dotenv

# Robust upward discovery of .env file
current_dir = os.path.abspath(os.path.dirname(__file__))
for _ in range(5):
    env_path = os.path.join(current_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent
else:
    load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/smartqueue")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    JWT_SECRET: str = Field(default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    SECRET_KEY: str = Field(default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GEMINI_API_KEY: str = ""
    CORS_ORIGINS: str = Field(default="*")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def model_post_init(self, __context):
        # Synchronize SECRET_KEY if JWT_SECRET is explicitly set
        if self.JWT_SECRET != "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7":
            self.SECRET_KEY = self.JWT_SECRET
        
        # Convert postgres:// to postgresql:// for SQLAlchemy 1.4+ / 2.0+ compatibility
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

settings = Settings()
