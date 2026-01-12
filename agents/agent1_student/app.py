import os
from fastapi import FastAPI
from langchain_community.chat_models import ChatOllama

app = FastAPI()

llm = ChatOllama(
    model="llama3",
    base_url="http://ollama:11434"
)

COLLECTION = os.getenv("COLLECTION", "agent1_student")

@app.post("/run")
async def run(payload: dict):
    question = payload.get("input", "")
    response = llm.invoke(question)
    return {"result": response.content, "collection": COLLECTION}
