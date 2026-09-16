# VisionIQ

VisionIQ is a multimodal content intelligence agent system capable of image and video understanding, visual product identification, knowledge retrieval (RAG), and agentic orchestration powered by Azure AI services.

---

## Project Structure

```text
visioniq/
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── services/
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── models/
│   └── config.py
├── agent/
│   ├── agent.py
│   ├── tools.py
│   └── prompts.py
├── services/
│   ├── vision/
│   ├── video/
│   ├── product_search/
│   └── rag/
├── data/
│   ├── products/
│   └── evaluation/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── evaluation.md
│   └── responsible-ai.md
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Environment Configuration
Copy the example environment file and fill in your Azure AI credentials:
```bash
cp .env.example .env
```

### 2. Backend Setup & Local Run
Create a virtual environment, install dependencies, and start the FastAPI server:
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Option A: Run directly from backend directory (Recommended)
cd backend
uvicorn main:app --reload --port 8000

# Option B: Run from project root
uvicorn backend.main:app --reload --port 8000
```
The backend API will be available at `http://localhost:8000` (Health check: `http://localhost:8000/api/health`).

### 3. Frontend Setup & Local Run
In a separate terminal, navigate to the `frontend/` directory, install packages, and start the Vite development server:
```bash
cd frontend
npm install
npm run dev
```
The frontend UI will be running at `http://localhost:5173`.
