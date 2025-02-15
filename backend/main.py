from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import images, users

app = FastAPI()

prod_cors_origins = [
    "https://bio-hue.vercel.app",
    "https://*.vercel.app",
]

local_cors_origins = ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        prod_cors_origins if settings.ENV == settings.PROD_ENV else local_cors_origins
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(images.router, tags=["Images"])


@api_router.get("/substrates")
async def list_substrates():
    return list(images.SUBSTRATES_CONFIG.keys())


app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Real-time infection monitoring"}


@app.get("/health")
async def health():
    return {"status": "ok"}
