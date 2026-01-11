from src.utils.Singleton import Singleton
import logging
import io
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
import asyncio
from concurrent.futures import ProcessPoolExecutor

class DocumentHandler(metaclass=Singleton):
    def __init__(self, logger=None):
        self.__logger = logger or logging.getLogger("KnowledgePitt")
        self.__logger.info("DocumentHandler initialized")
        self.__pipeline_options = PdfPipelineOptions(do_ocr=True)  # Fast: pdf_backend="dlparse_v2"

    @staticmethod
    def _process_pdf_worker(file_path_or_bytes, is_bytes=False):
        """Picklable - runs in separate process"""
        print(f"Worker processing: {'bytes' if is_bytes else file_path_or_bytes[:50]}...")
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=PdfPipelineOptions(do_ocr=True))
            }
        )
        source = io.BytesIO(file_path_or_bytes) if is_bytes else file_path_or_bytes
        result = converter.convert(source)
        return result.document.export_to_markdown()

    async def process_pdfs(self, sources: list) -> list[str]:
        """sources: list[str paths] or list[bytes]"""
        self.__logger.info(f"Processing {len(sources)} documents")
        loop = asyncio.get_running_loop()
        max_workers = min(4, len(sources), os.cpu_count() or 4)
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor, 
                    self._process_pdf_worker, 
                    source if isinstance(source, bytes) else source,
                    isinstance(source, bytes)
                )
                for source in sources
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [str(r) for r in results if not isinstance(r, Exception)]
        self.__logger.info(f"Completed {len(valid_results)}/{len(sources)}")
        return valid_results
