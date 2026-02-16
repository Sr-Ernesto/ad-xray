from fastapi import FastAPI
from api.routes import scan, results
from api.database import init_db_pool, close_db_pool
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db_pool()
    yield
    # Shutdown
    await close_db_pool()

app = FastAPI(
    title="AD-XRAY API",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(scan.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AD-XRAY API is running"}
