from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(title="Scapegis API")

# Add rate limiter to app state
from app.core.rate_limit import limiter, custom_rate_limit_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# CORS - specific origins required for cookies
origins = [
    "http://localhost:3000",  # Frontend
    "http://localhost:8000",  # Backend docs
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
	logger.exception("Unhandled exception while processing request: %s", exc)
	# ensure CORS header is returned even on 500
	cors_origin = "*"
	try:
		cors_list = settings.CORS_ORIGINS
		if isinstance(cors_list, (list, tuple)) and len(cors_list) > 0:
			cors_origin = cors_list[0]
		elif isinstance(cors_list, str):
			cors_origin = cors_list
	except Exception:
		cors_origin = "*"

	return JSONResponse(
		status_code=500,
		content={"detail": "Internal Server Error"},
		headers={
			"Access-Control-Allow-Origin": cors_origin,
			"Access-Control-Allow-Credentials": "true",
		},
	)


@app.get("/health")
def health():
	# quick DB ping
	try:
		with engine.connect() as conn:
			conn.execute("SELECT 1")
		return {"status": "ok"}
	except Exception as e:
		logger.exception("Health check failed: %s", e)
		return JSONResponse(status_code=503, content={"status": "db_unreachable"})


app.include_router(api_router, prefix="/api/v1")
