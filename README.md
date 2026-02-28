# AI Mental Health Support & Crisis Coordination System

A production-ready, multi-agent mental health companion built with **LangGraph**, **FastAPI**, and **LangChain**.

## 🧠 Core Architecture

The system uses a multi-agent orchestration approach to ensure safety, empathy, and responsible escalation:

1.  **Conversation Agent**: Manages session state and dialogue history.
2.  **Distress Analysis Agent**: Classifies emotion and risk level (Low, Moderate, High, Critical).
3.  **Risk Router**: A conditional node that redirects the flow based on risk level.
4.  **Support Strategy Agent**: Selects evidence-informed coping tools (GT, CBT, breathing) for lower risk.
5.  **Crisis Escalation Agent**: Activated for high risk; provides localized resources & immediate guidance.
6.  **Response Generator**: Formats final empathic output with mandatory safety disclaimers.

## 🚀 Quick Start (Demo Mode)

The system includes a `MockLLM` that allows you to run and test all scenarios instantly without any API keys or local LLM setup.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Test Scenarios
This script executes 3 predefined scenarios (Low, Moderate, and High risk) to show routing and safety behavior.
```bash
python demo/run_scenarios.py
```

### 3. Start the API Server
```bash
uvicorn app.main:app --reload --port 8000
```

## 🌐 API Endpoints

-   `POST /chat`: Primary interaction endpoint.
-   `GET /session/{id}/history`: Retrieve emotional history and detected trends.
-   `DELETE /session/{id}`: Privacy control; wipe session data.
-   `GET /health`: Health status and LLM configuration.

## 🛠️ Configuration

Copy `.env.example` to `.env` to configure LLM providers:
-   **Gemini**: Set `LLM_PROVIDER=gemini`, `MODEL_NAME=gemini-1.5-flash` (or pro), and provide `GOOGLE_API_KEY`.
-   **Ollama**: Set `LLM_PROVIDER=ollama` and `MODEL_NAME=llama3` for local models.
-   **Groq**: Set `LLM_PROVIDER=groq` and provide `GROQ_API_KEY`.
-   **Mock**: Default for instant demos.

## 🛡️ Safety & Privacy
-   **No Diagnosis**: The system is instruction-tuned to never provide clinical diagnoses.
-   **Crisis Override**: High-risk detection triggers immediate crisis escalation.
-   **Data Consent**: Emotional history tracking requires explicit user consent.
-   **Disclaimer**: Every response includes a mandatory medical disclaimer.
