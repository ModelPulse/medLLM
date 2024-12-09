# MedLLM - Using BreakYourLLM to Automate testing through CI/CD pipelines

This is a demo project aimed at showcasing the power of BreakYourLLM in robustly testing our LLM pipelines. 

## Installation
```bash
git clone https://github.com/ModelPulse/medLLM.git
cdd medLLM
pip install -r requirements.txt
```

## Running the server: 

```bash
uvicorn main:app --reload
        or
uvicorn main:app --reload --port 8001
```

## Note
- Due to security purposes, we have redacted the API keys in the env files in config folder. Please add your API keys.