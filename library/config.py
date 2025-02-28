from dotenv import load_dotenv
from pydantic_settings import BaseSettings



class BaseConfig(BaseSettings):
    openai_api_key: str
    elevenlabs_api_key: str
    assembly_ai_api_key: str

    class Config:
        env_file = '.env'
        extra = "ignore"
        case_insensitive = True
        case_insensitive = True


settings = BaseConfig()