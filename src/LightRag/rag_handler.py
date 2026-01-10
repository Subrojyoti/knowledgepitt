from config.common_config import options
from src.LLM.Gemini import Gemini, GeminiWrapper
from src.utils.Logger import Logger
from src.utils.Singleton import Singleton
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.gemini import gemini_model_complete
class LightRagService(metaclass=Singleton):
    def __init__(self, rag: LightRAG, service: str = "gemini"):
        self.__rag=rag
        