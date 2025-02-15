import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from itsdangerous import BadSignature, TimestampSigner
from passlib.context import CryptContext
from src.config import settings
from src.database import Session, User, sessions_collection, users_collection

SECRET_KEY = settings.SECRET_KEY
SESSION_COOKIE_NAME = "session"

router = APIRouter(prefix="/users")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
signer = TimestampSigner(SECRET_KEY)


def JSONResponseWithCookie(session: Session, *args, **kwargs):
    response = JSONResponse(*args, **kwargs)

    signed_cookie = signer.sign(
        json.dumps(session.model_dump(mode="json", by_alias=True))
    ).decode()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        signed_cookie,
        max_age=60 * 60 * 24,
        httponly=True,
        secure=settings.ENV == settings.PROD_ENV,
        samesite=None if settings.ENV == settings.PROD_ENV else "lax",
    )
    return response


async def get_current_user(request: Request):
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        unsigned_data = signer.unsign(session_cookie, max_age=60 * 60 * 24).decode()
        session = Session(**json.loads(unsigned_data))
    except (BadSignature, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid session data")

    db_session = await sessions_collection.find_one(
        {
            "_id": session.id,
            "username": session.username,
        }
    )
    if not db_session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await users_collection.find_one({"username": session.username})
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return User(**user)


@router.post("/register")
async def register(user: User):
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        return JSONResponse(
            content={"detail": "User already exists"},
            status_code=status.HTTP_409_CONFLICT,
            headers={"WWW-Authenticate": "Bearer realm='Login required'"},
        )

    hashed_password = pwd_context.hash(user.password)
    user.password = hashed_password
    await users_collection.insert_one(user.model_dump(by_alias=True))

    session = Session(username=user.username)
    await sessions_collection.insert_one(session.model_dump(by_alias=True))

    return JSONResponseWithCookie(
        session,
        content={"message": "User created"},
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login")
async def login(user: User):
    db_user = await users_collection.find_one({"username": user.username})
    if not db_user:
        return JSONResponse(
            content={"detail": "User not found"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer realm='Login required'"},
        )
    if not pwd_context.verify(user.password, db_user["password"]):
        return JSONResponse(
            content={"detail": "Invalid password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer realm='Login required'"},
        )

    session = Session(username=user.username)
    await sessions_collection.delete_many({"username": user.username})
    await sessions_collection.insert_one(session.model_dump(by_alias=True))

    return JSONResponseWithCookie(
        session,
        content={"message": "Logged in"},
    )


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return JSONResponse(user.model_dump(mode="json", exclude={"password"}))


@router.post("/logout")
async def logout(request: Request, user: User = Depends(get_current_user)):
    await sessions_collection.delete_many({"username": user.username})
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
