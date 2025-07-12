from fastapi import FastAPI
from app.routers import api
from app.middleware.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from app.utils.logging import logger
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI()

app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return {"detail": "Rate limit exceeded"}, 429

app.include_router(api.router)

@app.on_event("startup")
async def startup():
    logger.info("App started")

app.add_middleware(SlowAPIMiddleware)