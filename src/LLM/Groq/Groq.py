from config.common_config import options
from src.utils.Logger import Logger
from src.utils.Singleton import Singleton
from groq import AsyncGroq
class GroqHandler(metaclass=Singleton):
    def __init__(self, logger: Logger = None, api_key: str = None):
        if logger is None:
            self.__logger = Logger().get_simple_logger("KnowledgePitt")
        else:
            self.__logger = logger
        self.__logger.info("Initializing GroqHandler...")
        self.__client = AsyncGroq(api_key=api_key)

    async def get_response(self, user_message: str, system_prompt: str, model: str = "llama-3.1-8b-instant"):
        response = await self.__client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content

    async def get_response_stream(self, user_message: str, system_prompt: str, model: str = "llama-3.1-8b-instant"):
        response_stream = await self.__client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100000,
            stream=True
        )
        async for chunk in response_stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    