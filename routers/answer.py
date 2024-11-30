# Define the request and response models
from fastapi import FastAPI, HTTPException, APIRouter, Form, UploadFile, File, APIRouter
import json
import pandas as pd
import io
import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List
import requests
from dotenv import load_dotenv
from helpers.openai_client import openai_client

# load_dotenv(dotenv_path=".env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# token = os.getenv("vector_token")
token = os.getenv("eliquis_token")



answer_router = APIRouter()

# Define the request and response models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    context: list

# Define the function to retrieve context from the external API
def retrieve_context(question):
    # retrieval_endpoint = "https://client.app.vectorize.io/api/gateways/service/ob1f-98e000e80c6f/pfecf36e6/retrieve"
    retrieval_endpoint = "https://client.app.vectorize.io/api/gateways/service/o7be-476d5d63a0fb/p8aa3b75b/retrieve"   # website
    headers = {
        'Content-Type': 'application/json',
        'Authorization': token
    }
    data = {
        "question": question,
        "numResults": 5,
        "rerank": True
    }

    # Make the request to the external API
    response = requests.post(retrieval_endpoint, headers=headers, json=data)
    response.raise_for_status()  # Raise exception for 4XX/5XX responses

    # Parse the response JSON and convert 'values' to a JSON object
    values = response.json()['record']['value']
    try:
        json_data = json.loads(values)
        return json_data['related_documents']
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error decoding JSON from retrieval service: {e}")

# Define the function to generate an answer with citations
def answer_question_with_citations(chunks, question):
    # Prepare the context with citations in markdown format
    context = ""
    for chunk in chunks:
        source_id = chunk['chunkid']
        # source_url = f"https://source.url/{source_id}"  # Adjust URL as needed for each source's unique URL
        source_url = chunk['source']
        context += f"[source={source_id}&link={source_url}]: {chunk['text']}\n\n"

    # Formulate the prompt
    prompt = f"""You are a assistant helping cardiologist doctors provide information on medicine dosage, side effects and alternative medicine.  You are tasked with classifying the question into a category, and based on the category answering the question using provided chunks of information. Your goal is to provide an accurate answer within the guardrails while citing your sources using a specific markdown format.

Here is the question you need to answer:
<question>
{question}
</question>

Classify the question into one of the following categories:

<categories>
1) Question is about dosage of a medicine for a particular disease.
2) Question is about the side effect of medicine 
3) Alternative medicine for particular disease
</categories>

<guardrails>
Based on the category of the questions use the following guardrails and answer the questions:
if question falls into: 
1) category 1: Question is about dosage of a medicine for a particular disease. DO the following: 
  -> Should specify the dosage of the medicine: 
        a) Standard dosages for adults and children
        b) Dose adjustments for specific disease conditions
        c) Dosing in special populations (elderly, pregnant women, etc.)
  -> Should specify the side effects of the medicine
        a) Common side effects
        b) Rare but serious adverse reactions
        c) Black box warnings
  -> A note at the end: "For each of the suggestions please look into the citations for verification"

2) category 2: Question is about the side effect of medicine. DO the following:
  -> Also the side effects of the medicine
    a) Common side effects
    b) Rare but serious adverse reactions
    c) Black box warnings
  -> Drug Interactions:
    a) Interactions with other medications
    b) Food interactions
  -> Alternative Medications:
    a) Other drugs in the same class
  -> A note at the end: "For each of the suggestions please look into the citations for verification"

3) category 3: Alternative medicine for particular disease. DO the following:
  -> all medicine options
  -> Also the side effects of the medicine
    a) Common side effects
    b) Rare but serious adverse reactions
  -> A note at the end: "For each of the suggestions please look into the citations for verification"
</guardrails>


Below are chunks of information that you can use to answer the question. Each chunk is preceded by a 
source identifier in the format [source=X&link=Y], where X is the source number and Y is the URL of the source:

<chunks>
{context}
</chunks>

Your task is to answer the question using the information provided in these chunks following the above guardrails.
Don't provide information about the category in your answers, but do mention the guardrails topics. 
When you use information from a specific chunk in your answer, you must cite it using a markdown link format. 
The citation should appear at the end of the sentence where the information is used.

If you cannot answer the question using the provided chunks, say "Sorry I don't know".

The citation format should be as follows:
[Chunk source](URL)

For example, if you're using information from the chunk labeled [source=3&link=https://example.com/page], your citation would look like this:
[Chunk 3](https://example.com/page).
"""

    # # Query OpenAI API
    # openai.api_key = OPENAI_API_KEY
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ]
    # )

    # client = OpenAI()
    # completion = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ]
    # )

    # Call the OpenAI API with ChatCompletion
    completion = openai_client.chat.completions.create(model="gpt-4o", 
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )



    # Extract and return the answer
    answer = completion.choices[0].message.content.strip()
    return answer

# FastAPI endpoint
@answer_router.post("/answer", response_model=AnswerResponse)
async def answer_question(question_request: QuestionRequest):
    question = question_request.question

    # Retrieve context from the external API
    try:
        chunks = retrieve_context(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Generate answer with citations
    try:
        answer = answer_question_with_citations(chunks, question)
        return AnswerResponse(answer=answer, context=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in OpenAI API call: {e}")

# To run the app, use: uvicorn main:app --reload
