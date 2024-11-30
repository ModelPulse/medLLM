from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import json
import os
import requests

# Replace this with your OpenAI API key
load_dotenv(dotenv_path=".env")  # Loads the .env file

from routers.answer import answer_router
from fastapi.middleware.cors import CORSMiddleware

# exit()

# Initialize FastAPI app
app = FastAPI()
app.include_router(answer_router, prefix="")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005"],  # Or use ["*"] to allow all origins (for development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# To run the app, use: uvicorn main:app --reload
