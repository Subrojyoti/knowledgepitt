# src/JobSystem/job_manager.py
import threading
import queue
import time
import logging
from dataclasses import dataclass, field
from typing import Dict

from src.utils.Singleton import Singleton
from src.utils.Logger import Logger
from src.Document.document_handler import DocumentHandler
from src.LightRag.rag_handler import LightRagService
import asyncio 

@dataclass
class Job:
    id: str
    file_path: str
    status: str = "queued"
    error: str = None
    created_at: float = field(default_factory=time.time)

class JobManager(metaclass=Singleton):
    def __init__(self, doc_handler: DocumentHandler, rag_service, on_status_change=None):
        self.logger = Logger().get_simple_logger("KnowledgePitt")
        self.doc_handler = doc_handler
        self.rag_service = rag_service
        self.on_status_change = on_status_change
        
        # Concurrency Tools
        self._queue = queue.Queue()
        self._semaphore = threading.Semaphore(3) # Limit to 3 concurrent OCR
        self._stop_event = threading.Event()
        
        # State Tracking
        self.jobs: Dict[str, Job] = {}
        
        # Start the worker immediately (daemon thread)
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self.logger.info("JobManager started background worker.")

    def _notify(self, job: Job):
        if self.on_status_change:
            try:
                self.on_status_change(job.id, job.status, job.error)
            except Exception as e:
                self.logger.error(f"Failed to notify status change: {e}")

    def submit_job(self, job_id: str, file_path: str):
        """External API calls this to add work"""
        job = Job(id=job_id, file_path=file_path)
        self.jobs[job_id] = job
        self._queue.put(job_id)
        self.logger.info(f"Job {job_id} queued.")
        self._notify(job)

    def get_job_status(self, job_id: str):
        job = self.jobs.get(job_id)
        return job.__dict__ if job else None

    def _worker_loop(self):
        """The internal loop running in the background thread"""
        while not self._stop_event.is_set():
            try:
                # Wait for a job (timeout allows checking stop_event)
                job_id = self._queue.get(timeout=1.0)
                
                # We have a job!
                self._process_job(job_id)
                self._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")

    def _process_job(self, job_id: str):
        job = self.jobs.get(job_id)
        if not job: return

        # ACQUIRE SEMAPHORE (The Gatekeeper)
        # This blocks if another job is currently doing OCR
        with self._semaphore:
            self.logger.info(f"Job {job_id}: Processing started...")
            job.status = "processing"
            self._notify(job)
            
            try:
                # 1. OCR
                markdown = self.doc_handler.process_pdf(job.file_path)
                
                # 2. RAG Ingestion
                # Use a new event loop for this thread to run the async task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the ingestion
                loop.run_until_complete(
                    self.rag_service.ingest_information([markdown])
                )
                loop.close()
                        
                job.status = "completed"
                self.logger.info(f"Job {job_id}: Ingested into RAG.")
                self._notify(job)
                
            except Exception as e:
                job.status = "failed"
                job.error = str(e)
                self.logger.error(f"Job {job_id} Failed: {e}")
                self._notify(job)