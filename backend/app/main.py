"""FastAPI application — OCR Clinical Text Analysis."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import analysis, pipeline_results, degradation, documents, notes, experiments, results

app = FastAPI(
    title="OCR Clinical Text Analysis API",
    description="Full-stack API for OCR error analysis and clinical text processing pipeline.",
    version="1.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analysis.router)
app.include_router(pipeline_results.router)
app.include_router(degradation.router)
app.include_router(documents.router)
app.include_router(notes.router)
app.include_router(experiments.router)
app.include_router(results.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
