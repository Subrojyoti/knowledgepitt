from config.common_config import options
from src.LLM.Gemini.GeminiWrapper import GeminiWrapper
from src.utils.Logger import Logger
from src.utils.Singleton import Singleton
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc


class LightRagService(metaclass=Singleton):
    def __init__(self, rag: LightRAG = None):
        self.__logger = Logger().get_simple_logger("KnowledgePitt")
        self.__gemini_client = GeminiWrapper(api_key=options['gemini_api_key'])

        if rag is not None:
            self.__rag = rag
        else:
            embedding_func_conf = EmbeddingFunc(
                embedding_dim=options['embedding_dimension'],
                max_token_size=8192,
                func=self.__gemini_client.embedding_wrapper
            )
            self.__rag = LightRAG(
                working_dir=options['working_dir'],
                workspace=options['workspace'],
                log_file_path=options['log_file_path'],
                embedding_func_conf=embedding_func_conf,
                llm_model_func=self.__gemini_client.llm_model_func
            )

    async def initialize(self):
        """Asynchronously initialize the LightRAG storages."""
        self.__logger.info("Initializing LightRAG storages...")
        await self.__rag.initialize_storages()
        self.__logger.info("LightRAG storages initialized.")

    async def ingest_information(self, texts: list[str], file_paths: list[str] = None):
        """Asynchronously ingest information into the LightRAG system."""
        self.__logger.info("Ingesting information into LightRAG...")
        try:
            track_id = await self.__rag.ainsert(input=texts, file_paths=file_paths)
            self.__logger.info(f"Information ingested successfully. Track ID: {track_id}")
            return track_id
        except Exception as e:
            self.__logger.error(f"Failed to ingest information: {e}")
            raise


    async def query(self, query: str):
        """Query the LightRAG system."""
        self.__logger.info(f"Querying LightRAG: {query}")
        try:
            result = await self.__rag.aquery(query, param=QueryParam(mode='hybrid', top_k=5, stream=True))
            if isinstance(result, str):
                yield result
            else:
                async for chunk in result:
                    yield chunk
        except Exception as e:
            self.__logger.error(f"Failed to query LightRAG: {e}")
            raise

    