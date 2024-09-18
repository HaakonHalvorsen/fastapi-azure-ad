import uvicorn
from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from pydantic import AnyHttpUrl, computed_field
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = ['http://localhost:8000']
    OPENAPI_CLIENT_ID: str = ""
    APP_CLIENT_ID: str = ""
    TENANT_ID: str = ""
    SCOPE_DESCRIPTION: str = "user_impersonation"

    @computed_field
    @property
    def SCOPE_NAME(self) -> str:
        return f'api://{self.APP_CLIENT_ID}/{self.SCOPE_DESCRIPTION}'

    @computed_field
    @property
    def SCOPES(self) -> dict:
        return {
            self.SCOPE_NAME: self.SCOPE_DESCRIPTION,
        }

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()
    yield

app = FastAPI(
    swagger_ui_oauth2_redirect_url='/oauth2-redirect',
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': settings.OPENAPI_CLIENT_ID,
    },
)

app = FastAPI()

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes=settings.SCOPES,
)

@app.get("/", dependencies=[Security(azure_scheme)])
async def root():
    return {"message": "Hello World"}

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)