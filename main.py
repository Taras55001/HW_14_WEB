from fastapi import FastAPI
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware

from src.conf.config import redis_config
from src.routes import users, contacts, auth

app = FastAPI()

origins = [
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(contacts.router)


@app.on_event("startup")
async def startup():
    """
    Function to initialize Redis and FastAPILimiter on application startup.
    """
    r = await redis.Redis(host=redis_config.host, password=redis_config.password, port=redis_config.port,
                          db=0, encoding="utf-8",
                          decode_responses=True)
    await FastAPILimiter.init(r)


@app.get("/")
def read_root():
    """
    Default route to indicate that the application has started.
    """
    return {"message": "Application started"}
