import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
import asyncio
import json
from contextlib import asynccontextmanager

from src.utils.Logger import Logger
from src.Document.document_handler import DocumentHandler
from src.LightRag.rag_handler import LightRagService
from config.common_config import options
from src.JobSystem.job_manager import JobManager

class JobStatusManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_status(self, job_id: str, status: str, error: str = None):
        message = json.dumps({"job_id": job_id, "status": status, "error": error})
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

# --- GLOBAL INITIALIZATION ---
logger = Logger().get_simple_logger("KnowledgePitt")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Dependencies
    app.state.doc_handler = DocumentHandler(logger=logger)
    app.state.rag_service = LightRagService()
    await app.state.rag_service.initialize()
    
    # 2. Initialize Job Manager with status callback
    job_status_manager = JobStatusManager()
    app.state.job_status_manager = job_status_manager
    loop = asyncio.get_running_loop()

    def status_callback(job_id, status, error):
        asyncio.run_coroutine_threadsafe(
            job_status_manager.broadcast_status(job_id, status, error),
            loop
        )

    app.state.job_manager = JobManager(app.state.doc_handler, app.state.rag_service, on_status_change=status_callback)
    
    yield
    
    # 3. Clean up
    shutil.rmtree(options['file_upload_dir'])

app = FastAPI(lifespan=lifespan)

@app.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    job_ids = []
    
    for file in files:
        job_id = str(uuid.uuid4())
        ext = file.filename.split(".")[-1].lower()
        file_path = os.path.join(options['file_upload_dir'], f"{job_id}.{ext}")
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Submit to Manager
        if ext == "pdf":
            app.state.job_manager.submit_job(job_id, file_path)
            job_ids.append(job_id)
            
    return {"status": "queued", "job_ids": job_ids}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Real-time WebSocket endpoint for RAG Chat.
    """
    # 1. Accept the connection
    await websocket.accept()
    
    rag_service: LightRagService = app.state.rag_service
    
    try:
        while True:
            # 2. Wait for user message
            user_query = await websocket.receive_text()
            
            # Optional: Send a "processing" status
            await websocket.send_text("Thinking...") 
            
            try:
                # 3. Stream the response chunks from LightRAG
                async for chunk in rag_service.query(user_query):
                    # Send each token immediately to the client
                    await websocket.send_text(chunk)
                
                # 4. Signal end of turn (Optional protocol)
                # Some frontends like a specific token to know the stream is done
                await websocket.send_text("<<END_OF_TURN>>")
                
            except Exception as e:
                # Send error to client without crashing the connection
                await websocket.send_text(f"Error generating response: {str(e)}")
                
    except WebSocketDisconnect:
        # Handle client closing the tab
        logger.info("Client disconnected from WebSocket")

@app.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """
    Subscribes the client to real-time job status updates.
    """
    await app.state.job_status_manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, but keeping it open
            await websocket.receive_text()
    except WebSocketDisconnect:
        app.state.job_status_manager.disconnect(websocket)