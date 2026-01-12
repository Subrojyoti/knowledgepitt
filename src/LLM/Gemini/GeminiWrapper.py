from src.LLM.Gemini.Gemini import Gemini
from src.utils.Logger import Logger
from src.utils.Singleton import Singleton
import numpy as np
class GeminiWrapper(Gemini, metaclass=Singleton):
    def __init__(self, logger: Logger = None, api_key: str = None):
        super().__init__(logger=logger, api_key=api_key)
        if logger is None:
            self.__logger = Logger().get_simple_logger("KnowledgePitt")
        else:
            self.__logger = logger
        self.__logger.info("Initializing GeminiWrapper...")

    async def embedding_wrapper(self, texts: list[str]) -> np.ndarray:
        self.__logger.info("Generating embeddings for texts...")
        try:
            response = await super().google_embedding(model="text-embedding-004", texts=texts)
            if hasattr(response.embeddings[0], 'values'):
                data = [e.values for e in response.embeddings]
            else:
                data = response.embeddings
            if len(data) > len(texts):
                data = data[:len(texts)]
            self.__logger.info("Embeddings generated successfully.")
            return np.array(data)
        except Exception as e:
            self.__logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def llm_model_func(self, prompt, system_prompt=None, history=[], **kwargs) -> str:
        model = kwargs.get("model", "gemini-2.5-flash-lite")
        if kwargs.get("stream", False):
            return self.get_response_stream(
                model=model,
                user_message=prompt,
                system_prompt=system_prompt
            )
        else:
            response = await self.get_response(
                model=model,
                user_message=prompt,
                system_prompt=system_prompt
            )
            return response.text
        