import uvicorn

from app.core.config import Settings

if __name__ == "__main__":
    settings = Settings.from_env()
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port)
