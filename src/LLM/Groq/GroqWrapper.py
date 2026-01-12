from src.LLM.Groq.Groq import GroqHandler
from src.utils.Logger import Logger
from src.utils.Singleton import Singleton
class GroqWrapper(GroqHandler, metaclass=Singleton):
    def __init__(self, logger: Logger = None, api_key: str = None):
        super().__init__(logger=logger, api_key=api_key)
        if logger is None:
            self.__logger = Logger().get_simple_logger("KnowledgePitt")
        else:
            self.__logger = logger
        self.__logger.info("Initializing GroqWrapper...")
    
    async def llm_model_func(self, prompt, system_prompt=None, history=[], **kwargs) -> str:
        model = kwargs.get("model", "llama-3.1-8b-instant")
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
            return response