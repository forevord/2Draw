from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.checkout import router as checkout_router
from app.api.health import router as health_router
from app.api.process import router as process_router
from app.api.results import router as results_router
from app.api.upload import router as upload_router
from app.api.webhook import router as webhook_router

app = FastAPI(
    title="2Draw API",
    version="0.1.0",
    description="AI-powered paint-by-number generator backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(process_router, prefix="/api/v1")
app.include_router(results_router, prefix="/api/v1")
app.include_router(checkout_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")
