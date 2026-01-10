import os
from dotenv import load_dotenv

load_dotenv(override=True)
options = dict()

options["gemini_api_key"]=os.getenv("GEMINI_API_KEY")
options["groq_api_key"]=os.getenv("GROQ_API_KEY")
