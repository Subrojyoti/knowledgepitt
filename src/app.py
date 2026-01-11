import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from contextlib import asynccontextmanager
from celery import Celery

from src.utils.Logger import Logger
from src.Document.document_handler import DocumentHandler
from src.LightRag.rag_handler import LightRagService
from config.common_config import options



# --- CELERY SETUP ---
celery_app = Celery(
    "knowledgepitt",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

# --- GLOBAL INITIALIZATION ---
# This runs when the Celery Worker starts.
# Because DocumentHandler is a Singleton, the heavy OCR models load here 
# and stay in RAM, ready for tasks.
logger = Logger().get_simple_logger("KnowledgePitt")
doc_handler = DocumentHandler(logger=logger)

@celery_app.task(bind=True, max_retries=3)
def process_pdf_celery(self, file_path: str, job_id: str):
    """
    Worker receives a FILE PATH.
    It reuses the global 'doc_handler' instance (no model reloading).
    """
    try:
        # 1. Process
        markdown = doc_handler.process_pdf(file_path)
        
        # 2. Ingest to RAG (Assuming synchronous or separate call)
        # rag_service.ingest_information(markdown)

        # 3. Cleanup (Optional: delete the temp file to save space)
        # os.remove(file_path)

        return {"job_id": job_id, "status": "completed", "chars": len(markdown)}
    except Exception as exc:
        # Exponential backoff retry
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# --- FASTAPI SETUP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize RAG service for the API
    app.state.rag_service = LightRagService()
    await app.state.rag_service.initialize()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    job_ids = []
    
    for file in files:
        job_id = str(uuid.uuid4())
        ext = file.filename.split(".")[-1].lower()
        
        # 1. SAVE TO DISK (Prevents RAM overflow on large files)
        file_path = os.path.join(options['file_upload_dir'], f"{job_id}.{ext}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        if ext == "pdf":
            # 2. DISPATCH TASK (Send path, not bytes)
            process_pdf_celery.delay(file_path, job_id)
            status = "queued"
        else:
            # Handle text immediately
            # (Note: For large text files, reading directly might still be risky, but okay for now)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            app.state.rag_service.ingest_information([text])
            status = "completed"
            
        job_ids.append({"id": job_id, "status": status})
    
    return {"jobs": job_ids}