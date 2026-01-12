from pydantic import BaseModel

# --- REQUEST MODELS ---
class QueryRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # explicit, hybrid, local, global