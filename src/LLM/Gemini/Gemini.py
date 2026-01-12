from config.common_config import options
from src.utils.Logger import Logger
from src.utils.Singleton import Singleton
from google import genai
from google.genai import types
class Gemini(metaclass=Singleton):
    def __init__(self, logger: Logger = None, api_key: str = None):
        if logger is None:
            self.__logger = Logger().get_simple_logger("KnowledgePitt")
        else:
            self.__logger = logger
        self.__logger.info("Initializing Gemini...")
        self.__client = genai.Client(api_key=api_key).aio

    async def google_embedding(self, model: str, texts: list[str]):
        response = await self.__client.models.embed_content(
            model=model,
            contents=texts
        )
        return response

    async def get_response(self, model: str, user_message: str, system_prompt: str, response_schema = None, response_mime_type = None):
        response = await self.__client.models.generate_content(
            model=model,
            contents = user_message,
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type=response_mime_type,
                response_schema=response_schema
            )
        )
        return response
    
    async def get_response_stream(self, model: str, user_message: str, system_prompt: str):
        async for chunk in self.__client.models.generate_content_stream(
            model=model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        ):
            yield chunk.text

        