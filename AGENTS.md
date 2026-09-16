# VisionIQ — Agent & Engineering Guidelines

This document establishes the architecture standards, technical stack, folder layout, security rules, and project boundaries for AI coding agents and human contributors working on VisionIQ.

---

## 1. Technology Stack

- **Backend**: Python + FastAPI
- **Frontend**: React + TypeScript (powered by Vite)
- **Agent Orchestration**: Microsoft Foundry Agent Service (`azure-ai-projects`)
- **Knowledge Base & RAG**: Azure AI Search (`azure-search-documents`)
- **Multimodal Intelligence**: Azure Content Understanding & Azure Vision (`azure-ai-contentunderstanding`)
- **Storage**: Azure Blob Storage (`azure-storage-blob`)

---

## 2. Project Folder Structure

All code must adhere to the following project structure:

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

## 3. Core Security & Secret Management Rule

> **CRITICAL RULE**: Never commit secrets, credentials, API keys, or connection strings to git.
> Always read credentials strictly from environment variables via `backend/config.py` matching `.env.example`.

---

## 4. Explicit "What NOT to Build" Boundaries

To keep VisionIQ focused, efficient, and maintainable, the following are strictly out of scope:

1. **No Kubernetes**: Do not create Helm charts, K8s manifests, or cluster deployments.
2. **No Microservices**: Keep the backend as a single, cohesive FastAPI modular monolith.
3. **No Mobile App**: Focus purely on the web dashboard (React/Vite).
4. **No Live Streaming**: Only process uploaded or URL-referenced image/video media files; no WebRTC or real-time RTSP/RTMP stream pipelines.
5. **No Custom Model Training**: Use pre-built Azure AI Foundry foundation models and Azure Content Understanding APIs.
6. **No Huge Product Database**: Rely on lightweight sample product catalogs in Azure AI Search.
7. **No Complex Auth / CI-CD**: Keep local execution and basic API access straightforward without enterprise OAuth/SSO hurdles or bloated pipelines.
8. **No Unnecessary Databases**: Avoid provisioning separate PostgreSQL, MongoDB, or Redis instances unless explicitly required. Azure AI Search and Blob Storage handle indexing and media storage.
9. **No Excessive UI Animation**: Maintain a clean, fast, and responsive user experience without heavy, distracting animations.
