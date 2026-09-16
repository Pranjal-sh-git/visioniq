# VisionIQ Architecture Overview

VisionIQ is a multimodal content intelligence agent system built on Azure AI services.

## High-Level Architecture

```
+-------------------------------------------------------------+
|                     React + Vite Frontend                   |
|       (Image Intelligence Tab | Video Intelligence Tab)      |
+------------------------------+------------------------------+
                               | REST / JSON
+------------------------------v------------------------------+
|                     FastAPI Backend                         |
|         (API Routing, CORS, Validation, Middleware)         |
+------------------------------+------------------------------+
                               |
+------------------------------v------------------------------+
|                 Agent Orchestration Layer                   |
|        (Microsoft Foundry Agent Service + Custom Tools)     |
+----+-------------------+--------------------+---------------+
     |                   |                    |               |
+----v-----+       +-----v----+         +-----v-----+   +-----v-----+
|  Azure   |       |  Azure   |         | Azure AI  |   |   Azure   |
| Content  |       |  Vision  |         |  Search   |   |   Blob    |
| Under-   |       | Service  |         | (Hybrid / |   |  Storage  |
| standing |       |          |         |  Vector)  |   |           |
+----------+       +----------+         +-----------+   +-----------+
```

## Core Components
1. **Frontend (React/TypeScript + Vite)**: Interactive UI for multimodal querying, video segment browsing, and visual product inspection.
2. **Backend (FastAPI)**: Lightweight REST API serving agent endpoints and handling media uploads.
3. **Agent & Tools (`agent/`)**: Powered by Microsoft Foundry Agent Service to orchestrate reasoning, function calling, and RAG execution.
4. **Services Layer (`services/`)**: Encapsulated service clients for Azure Content Understanding, Vision, Video temporal search, and Azure AI Search.
5. **Data & Docs (`data/`, `docs/`)**: Datasets, evaluation benchmarks, and architectural documentation.
