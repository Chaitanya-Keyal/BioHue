from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import images, users

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Set-Cookie"],
)

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(images.router, prefix="/api/images", tags=["Images"])


@app.get("/")
async def root():
    return {"message": "Real-time infection monitoring"}


@app.get("/health")
async def health():
    return {"status": "ok"}
