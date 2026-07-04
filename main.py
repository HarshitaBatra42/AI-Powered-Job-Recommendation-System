from xml.parsers.expat import model

from fastapi import FastAPI
from pydantic import BaseModel
from recommender import recommend_jobs
import google.generativeai as genai

import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
app = FastAPI()

# -----------------------------
# REQUEST MODEL
# -----------------------------
class ResumeRequest(BaseModel):
    resume_text: str

# -----------------------------
# HEALTH CHECK (IMPORTANT)
# -----------------------------
@app.get("/")
def home():
    return {"status": "API running"}

# -----------------------------
# RECOMMENDATION ENDPOINT
# -----------------------------

@app.post("/recommend")
def get_recommendations(data: ResumeRequest):

    # Step 1: get results safely
    results = recommend_jobs(data.resume_text)

    # Step 2: safety checks
    if not results:
        return []

    # Step 3: return top 5 safely
    return results[:5]


class ChatRequest(BaseModel):
    message: str
    skills: list
    job: str
    history: list = []


@app.post("/chat")
def chat(req: ChatRequest):

    conversation = ""

    for msg in req.history:
        conversation += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )

    try:

        model = genai.GenerativeModel(
            "models/gemini-2.5-flash"
        )

        prompt = f"""
You are an AI Career Assistant.

User Skills:
{req.skills}

Target Job:
{req.job}

Previous Conversation:
{conversation}

Current Question:
{req.message}

Continue the conversation naturally.
Use previous messages when answering.
Give practical career guidance.
"""

        response = model.generate_content(
            prompt
        )

        return {
            "response": response.text
        }

    except Exception as e:

        return {
            "response": str(e)
        }