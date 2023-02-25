from pydantic import BaseSettings


class Settings(BaseSettings):
    TG_BOT_TOKEN: str
    BASE_USERS_PATH: str = 'users'

    class Config:
        env_file = '.env'


settings = Settings()