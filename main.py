from fastapi import FastAPI
from gateway.router import router as gateway_router

app = FastAPI(
    title="Transactworld",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.include_router(gateway_router)
