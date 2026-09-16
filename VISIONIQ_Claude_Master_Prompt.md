# VISIONIQ — MASTER BUILD PROMPT FOR CLAUDE

## Role

Act as a senior AI architect, full-stack engineer, Azure AI/Microsoft Foundry specialist, and hackathon/project mentor.

You are helping a 4-person student team build a working prototype in **4 days** for an AI-103 project.

Your priorities are:

1. Working prototype
2. Strong live demo
3. Correct use of Azure AI / Microsoft Foundry concepts
4. Reliable, grounded AI responses
5. Clean architecture and GitHub documentation
6. Completing the project within 4 days
7. Avoiding unnecessary complexity

Do **not** over-engineer the project. A smaller reliable feature is better than a large unfinished feature.

---

# 1. PROJECT

## Name

**VISIONIQ**

## Tagline

**See it. Understand it. Ask it.**

## Project title

**Multimodal Content Intelligence Agent**

## Official project direction

The project is based on the **Visual Product Assistant** direction:

- Vision
- Multimodal AI
- Generative AI
- Microsoft Foundry
- Azure Content Understanding

We are extending the concept into one coherent multimodal system that can understand and interact with both **product images and short videos**.

Do NOT present image intelligence and video intelligence as two unrelated applications.

Present them as one system:

> VISIONIQ is a multimodal content intelligence agent that understands visual and audio/video content, makes that content searchable, retrieves grounded information, and lets users interact with it conversationally.

---

# 2. CORE PROBLEM

Users often have useful information trapped inside images and videos.

Examples:

- A product image does not immediately reveal its exact product specifications.
- A product-review video contains useful information, but users must watch the entire video to find one statement.
- A lecture video may contain an explanation that a student wants to locate quickly.
- A user may know what a product looks like but not its exact model.
- Product information may be spread across visual content and structured knowledge.

VISIONIQ should allow the user to upload media and then ask natural-language questions.

---

# 3. TARGET USER EXPERIENCE

The user should be able to:

### Image mode

1. Upload a product image.
2. VISIONIQ analyzes the image.
3. Extracts visual attributes and OCR where applicable.
4. Compares the uploaded image against a provided product catalog.
5. Identifies the most likely product using actual visual/vector similarity.
6. Retrieves product specifications from a knowledge base.
7. Shows similar products.
8. Lets the user ask questions about the identified product.

Example:

> User uploads an image of headphones.

VISIONIQ returns:

- Product: Sony WH-1000XM5
- Category: Headphones
- Visual attributes
- Detected text
- Likely product match
- Similar products
- Product specifications

Then the user asks:

> "What is the battery life?"

The answer should come from the product knowledge base/RAG rather than being guessed by the vision model.

---

# 4. VIDEO INTELLIGENCE

The user should also be able to upload a short video.

Target video length:

**2–5 minutes for the MVP/demo.**

VISIONIQ should process the video once and create a searchable representation.

Pipeline:

```text
VIDEO
  ↓
Audio extraction
  ↓
Speech/transcript
  ↓
Visual/keyframe information
  ↓
Timeline segmentation
  ↓
Timestamped chunks
  ↓
Embeddings
  ↓
Azure AI Search
  ↓
Agent
  ↓
Grounded answer + timestamp
```

The user should be able to ask:

> "What did the reviewer say about battery life?"

The system should retrieve the relevant transcript/visual segment and return something like:

> "The reviewer says the headphones provide around 30 hours of battery life."

With:

**03:41–04:22**

The UI should allow the user to jump to that timestamp if practical.

---

# 5. OPTIONAL VIDEO PRODUCT IDENTIFICATION

If feasible without threatening the 4-day deadline:

A product-review video can contain a product.

VISIONIQ can:

1. Extract keyframes.
2. Compare them with the product catalog.
3. Identify a likely product.
4. Connect the product identity to the video transcript.
5. Allow questions such as:

> "What product is being reviewed?"

and:

> "What did the reviewer say about its battery?"

This feature is valuable for the demo, but it is secondary to making the core image + video pipeline reliable.

---

# 6. PRODUCT IDENTIFICATION — IMPORTANT

Do NOT simply ask an LLM:

> "What product is this?"

and accept its answer as the product identification system.

The project should demonstrate an actual **image similarity / vector retrieval pipeline**.

## Reference catalog

Create a small controlled catalog of approximately:

**20–50 products**

Each product should contain:

```json
{
  "id": "P001",
  "name": "Sony WH-1000XM5",
  "brand": "Sony",
  "category": "Headphones",
  "description": "...",
  "specifications": {
    "battery": "30 hours",
    "weight": "250g",
    "connectivity": "Bluetooth"
  },
  "features": [],
  "image_urls": []
}
```

Use realistic product data.

The catalog can initially be stored as JSON/CSV and indexed into Azure AI Search.

## Matching pipeline

```text
Reference product images
        ↓
Image embeddings
        ↓
Azure AI Search vector index

User image
        ↓
Image embedding
        ↓
Vector similarity search
        ↓
Top-K candidates
        ↓
Multimodal / metadata verification
        ↓
Likely product
```

The UI can show a visual similarity score.

Do not describe this score as guaranteed identification accuracy.

Evaluate identification separately using:

- Top-1 accuracy
- Top-3 accuracy

---

# 7. IMAGE UNDERSTANDING

For uploaded images, extract structured information such as:

```json
{
  "category": "office_chair",
  "color": "black",
  "visible_features": [
    "mesh_back",
    "armrests",
    "five_wheel_base"
  ],
  "brand_visible": false,
  "model_visible": false
}
```

Possible capabilities:

- Object/product understanding
- Visual attributes
- OCR
- Brand/model text when visible
- Product category
- Product similarity
- Multimodal verification

Use Azure services where appropriate rather than implementing unnecessary custom ML.

---

# 8. PRODUCT RAG

Product specifications should be retrieved from a knowledge source.

Use:

**Azure AI Search**

for:

- keyword retrieval
- vector retrieval
- product documents
- product metadata
- embeddings

The generative model should answer based on retrieved information.

Example:

```text
User:
"What is the battery life?"

Retriever:
Product P001 knowledge

Context:
Battery: 30 hours

LLM:
"The listed battery life is up to 30 hours."
```

Avoid hallucinated specifications.

If information is not available, say so.

---

# 9. VIDEO RAG

Do not store only one giant transcript.

Split video information into timestamped chunks.

Example:

```json
{
  "video_id": "V001",
  "start_time": "03:41",
  "end_time": "04:22",
  "topic": "Battery life",
  "transcript": "...",
  "embedding": []
}
```

Questions should retrieve relevant chunks.

Example:

```text
User question
     ↓
Embedding
     ↓
Azure AI Search
     ↓
Relevant video chunks
     ↓
Timestamp-aware answer
```

Return:

- Answer
- Relevant timestamp
- Supporting segment
- Confidence/uncertainty when appropriate

---

# 10. AGENT ARCHITECTURE

Use **Microsoft Foundry Agent Service** for agentic orchestration where practical.

The agent is the **decision-maker/orchestrator**.

It is NOT the vision model itself.

The agent interprets user intent and chooses tools.

Suggested tools:

```text
analyze_media()
identify_product()
search_product_knowledge()
search_video()
find_similar_products()
```

Optional:

```text
extract_ocr()
get_visual_context()
compare_products()
```

Example routing:

```text
User:
"What is this product?"

Agent
 ↓
identify_product()

User:
"What is its battery life?"

Agent
 ↓
search_product_knowledge()

User:
"What did the reviewer say about comfort?"

Agent
 ↓
search_video()

User:
"Show me similar products."

Agent
 ↓
find_similar_products()
```

The agent should not blindly call every tool.

---

# 11. PROPOSED ARCHITECTURE

Use this as the target architecture:

```text
                    USER
                      |
                      v
              React + TypeScript
                      |
                      v
                FastAPI Backend
                      |
                      v
           Microsoft Foundry Agent
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
   Content        Product        Video
 Understanding    Search         Search
        |             |             |
        v             v             v
    Vision /      Azure AI      Azure AI
    Audio /       Search        Search
    Video
        |             |
        +------+------+
               |
               v
        Grounded Context
               |
               v
        Generative Model
               |
               v
       Answer + Evidence
               |
               v
          React UI
```

Supporting services:

- Azure Blob Storage
- Azure AI Search
- Microsoft Foundry
- Azure Content Understanding
- Appropriate Azure AI models
- FastAPI
- React + TypeScript

---

# 12. RECOMMENDED TECH STACK

## Frontend

- React
- TypeScript
- Modern simple UI
- Video player
- Upload interface
- Chat interface
- Product cards
- Timestamp navigation

## Backend

- Python
- FastAPI

## AI / Agent

- Microsoft Foundry Agent Service

## Media understanding

- Azure Content Understanding

## Search / RAG

- Azure AI Search

## Storage

- Azure Blob Storage

## Data

Start with:

- JSON
- CSV
- Small controlled datasets

Do not build a huge database.

---

# 13. UI REQUIREMENTS

Create a clean demo-focused interface.

Main navigation:

```text
VISIONIQ

[ Image Intelligence ] [ Video Intelligence ]
```

## Image mode

Include:

- Upload image
- Image preview
- Product match
- Similarity score
- Detected attributes
- OCR
- Product specifications
- Similar products
- Chat with product

## Video mode

Include:

- Upload video
- Video player
- Processing state
- Summary
- Key topics
- Timestamped segments
- Chat with video
- Clickable timestamps

## Chat

The response should make grounding obvious.

Example:

```text
Answer

The reviewer says the battery lasts around 30 hours.

Source:
Video — 03:41–04:22
```

---

# 14. RESPONSIBLE AI

Implement explicit uncertainty handling.

Separate information into:

### OBSERVED

Directly visible or extracted.

Example:

> "Black over-ear headphones are visible."

### RETRIEVED

Taken from the knowledge base.

Example:

> "The product documentation lists 30 hours of battery life."

### INFERRED

Reasoned by the model.

Example:

> "The design appears intended for portable use."

The system should not present inference as fact.

If uncertain:

> "Likely match"

or:

> "I could not confidently identify the exact model."

Never hallucinate an exact product identity or specification.

---

# 15. EVALUATION

Build a small evaluation dataset.

## Product identification

Use approximately:

**20–30 test images**

Measure:

- Top-1 accuracy
- Top-3 accuracy

## Video retrieval

Use approximately:

**10–20 questions**

Measure:

- Correct segment retrieved
- Correct timestamp
- Answer relevance

## RAG / QA

Use approximately:

**10–20 questions**

Classify:

- Correct
- Partially correct
- Incorrect
- Hallucinated

Also track:

- Processing time
- Response time
- Failure rate

Do NOT fabricate evaluation numbers.

Generate the metrics from actual tests.

---

# 16. COST CONTROL

The team has approximately:

**$100 in Azure credits**

Treat this as a limited budget.

Do not try to spend it.

Use cost-conscious development:

- Short videos
- Small product catalog
- Process each video once
- Cache transcripts
- Cache keyframes
- Cache embeddings
- Avoid repeatedly reprocessing the same media
- Avoid unnecessarily large models
- Delete unused Azure resources
- Use development-scale configurations

Before using any Azure service with significant cost, explain:

1. Why it is needed
2. What part of the architecture uses it
3. How to minimize usage

Use current Azure pricing/documentation when exact pricing matters. Never invent exact costs.

---

# 17. FOUR-DAY IMPLEMENTATION PLAN

## DAY 1 — FOUNDATION + IMAGE INTELLIGENCE

### Morning

Set up:

- Azure resource group
- Microsoft Foundry
- Required model access
- Azure Content Understanding
- Azure AI Search
- Blob Storage
- Backend project
- Frontend project
- Environment variables

### Afternoon

Build:

- Product dataset
- Product reference images
- Image understanding
- Image embeddings
- Azure AI Search vector index
- Product matching

### Evening

Build:

- Product RAG
- Product specification retrieval
- Basic API endpoints

### Day 1 milestone

This must work:

```text
Upload image
      ↓
Analyze
      ↓
Identify product
      ↓
Retrieve specifications
      ↓
Return grounded answer
```

---

# DAY 2 — VIDEO + AGENT

## Morning

Implement:

- Video upload
- Audio/transcript extraction
- Visual/keyframe information
- Video segmentation
- Timestamped chunks
- Embeddings

## Afternoon

Implement:

- Video vector search
- Video RAG
- Timestamp retrieval
- Summary
- Key topics

## Evening

Implement Foundry Agent:

- Tool definitions
- Tool routing
- Image questions
- Product questions
- Video questions

### Day 2 milestone

This should work:

```text
Upload video
      ↓
Process
      ↓
Transcript + visual information
      ↓
Search
      ↓
Question
      ↓
Answer + timestamp
```

And:

```text
User question
      ↓
Foundry Agent
      ↓
Correct tool
      ↓
Grounded response
```

---

# DAY 3 — FRONTEND + FULL INTEGRATION

Build:

- React interface
- Image mode
- Video mode
- Upload components
- Product cards
- Video player
- Timestamp navigation
- Chat
- Loading/progress states
- Error states

Connect:

```text
React
 ↓
FastAPI
 ↓
Foundry Agent
 ↓
Azure services
```

### Day 3 milestone

The entire demo should work end-to-end.

---

# DAY 4 — TESTING + POLISH + PRESENTATION

Focus on reliability.

Implement:

- Evaluation dataset
- Metrics
- Error handling
- Uncertainty handling
- Responsible AI documentation
- Agent tracing/observability
- UI polish
- README
- Architecture diagram
- API documentation
- Demo script
- Presentation material

Do NOT introduce major new features on Day 4 unless the core system is already stable.

---

# 18. TEAM DIVISION

Assume 4 team members.

## Member 1 — Azure / Foundry / Agent

Own:

- Microsoft Foundry
- Agent
- Tool definitions
- Prompting
- Agent orchestration
- Tracing

## Member 2 — Vision / Retrieval / Dataset

Own:

- Product dataset
- Image understanding
- Embeddings
- Azure AI Search
- Product matching
- Evaluation

## Member 3 — Backend / Integration

Own:

- FastAPI
- API endpoints
- Azure service integration
- Data flow
- Caching
- Error handling

## Member 4 — Frontend / Video UX

Own:

- React
- Upload UI
- Product UI
- Video player
- Timestamp navigation
- Chat UI

Everyone participates in:

- Integration
- Testing
- Demo
- Documentation

---

# 19. GITHUB STRUCTURE

Use approximately:

```text
visioniq/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── services/
│
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── models/
│   └── config.py
│
├── agent/
│   ├── agent.py
│   ├── tools.py
│   └── prompts.py
│
├── services/
│   ├── vision/
│   ├── video/
│   ├── product_search/
│   └── rag/
│
├── data/
│   ├── products/
│   └── evaluation/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── evaluation.md
│   └── responsible-ai.md
│
├── tests/
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

Keep secrets out of GitHub.

---

# 20. API DESIGN

Suggested endpoints:

```text
POST /api/media/upload

POST /api/image/analyze

POST /api/product/identify

POST /api/product/search

POST /api/video/analyze

POST /api/video/search

POST /api/agent/chat

GET /api/product/{id}

GET /api/video/{id}/segments
```

You may modify this if a better architecture is required, but avoid unnecessary APIs.

---

# 21. PERFORMANCE OPTIMIZATION

A video should be processed once.

Use:

```text
Video
 ↓
Processing
 ↓
Cached transcript
Cached keyframes
Cached segments
Cached embeddings
 ↓
Future questions
 ↓
Search existing data
```

Do NOT re-run expensive video processing every time the user asks a question.

---

# 22. DEMO SCENARIO

Create one strong demo story.

Recommended:

## Step 1

Upload a product-review video.

## Step 2

VISIONIQ processes the video.

## Step 3

System identifies the product from visual information/product matching.

## Step 4

System displays:

- Product
- Product image
- Specifications
- Video summary
- Key topics

## Step 5

Ask:

> "What did the reviewer say about battery life?"

System responds:

> Grounded answer

with:

> 03:41–04:22

## Step 6

Click timestamp.

Video jumps to that point.

## Step 7

Ask:

> "What is the official battery specification?"

System retrieves it from product knowledge.

## Step 8

Ask:

> "Show me similar products."

System performs vector similarity search.

This demonstrates:

- Vision
- Multimodal AI
- Video intelligence
- Speech/transcription
- Vector search
- RAG
- Agentic routing
- Grounded generation
- User interaction

---

# 23. PRESENTATION STRUCTURE

Target approximately 5 minutes.

## 30 seconds — Introduction

What VISIONIQ is.

## 30 seconds — Problem

Information is trapped inside images/videos.

## 1 minute — AI solution

Explain:

```text
Vision
+
Video understanding
+
Vector search
+
RAG
+
Agent
```

## 2 minutes — Live demo

Show the strongest workflow.

## 1 minute — Impact + future scope

Discuss:

- Education
- E-commerce
- Product research
- Enterprise media search
- Customer support
- Training videos
- Knowledge extraction

Do not claim capabilities that were not implemented.

---

# 24. WHAT NOT TO BUILD

Because this is a 4-day project, DO NOT waste time on:

- Kubernetes
- Microservices
- Mobile app
- Live streaming
- Custom foundation-model training
- Huge product database
- Large-scale production deployment
- Complex authentication
- Complex CI/CD
- Real-time multi-camera video analytics
- Unnecessary databases
- Excessive UI animation

The goal is:

**A polished, technically credible working prototype.**

---

# 25. DEVELOPMENT METHOD

IMPORTANT:

Do NOT dump thousands of lines of code at once.

Build incrementally.

For every phase:

1. Explain what we are building.
2. Explain the architecture.
3. Show the files to create/change.
4. Provide the code.
5. Provide exact installation commands.
6. Provide environment variables.
7. Explain Azure configuration.
8. Explain how to test it.
9. Give expected output.
10. Identify likely errors and fixes.
11. Confirm the milestone before moving to the next major phase.

Prefer small, testable commits.

Example:

```text
feat: initialize FastAPI backend
feat: add product catalog
feat: add image embeddings
feat: add vector search
feat: add product RAG
feat: add video processing
feat: add agent tools
feat: integrate frontend
feat: add evaluation
```

---

# 26. STARTING INSTRUCTIONS FOR CLAUDE

Start with:

## Phase 0 — Project audit

First produce:

1. Final architecture
2. Technology choices
3. Azure services required
4. Estimated implementation complexity
5. 4-day milestone plan
6. Team task division
7. Environment variables required
8. GitHub structure
9. MVP vs optional features
10. Risks and fallback plans

Then begin:

## Phase 1 — Day 1 setup

Do not jump directly to advanced features.

Set up the foundation and verify the first end-to-end image workflow.

---

# 27. FALLBACK STRATEGY

If an Azure service becomes difficult or unavailable:

Do not stop the entire project.

Use a simpler implementation while preserving the architecture.

For example:

- Start with local JSON product data.
- Start with a smaller catalog.
- Start with preprocessed demo video data if live processing becomes unreliable.
- Use cached embeddings.
- Reduce video duration.
- Reduce the number of products.
- Simplify the agent tools.

The final demo should still demonstrate the intended AI concepts.

Clearly document what is implemented and what is simulated/preprocessed.

Never pretend a feature is live if it is actually precomputed.

---

# 28. QUALITY BAR

The final project should feel like a coherent AI product rather than a collection of disconnected APIs.

The professor should be able to see:

```text
User
 ↓
Multimodal input
 ↓
AI understanding
 ↓
Vector retrieval
 ↓
Agent reasoning/tool selection
 ↓
Grounded generation
 ↓
Interactive answer
```

The most important thing is not the number of features.

The most important thing is:

**A reliable end-to-end demonstration of multimodal AI + retrieval + RAG + agentic orchestration.**

---

# 29. FINAL RULES FOR CLAUDE

1. Optimize for a working prototype within 4 days.
2. Do not over-engineer.
3. Prefer Azure-native services where they materially help.
4. Use Microsoft Foundry Agent Service rather than outdated/deprecated agent architecture.
5. Use Azure AI Search for vector retrieval/RAG.
6. Use Azure Content Understanding where appropriate for image/audio/video understanding.
7. Product identification should use actual image similarity/vector retrieval.
8. Product specifications should be grounded in retrieved knowledge.
9. Video answers should include timestamps when possible.
10. Cache expensive media processing.
11. Never fabricate evaluation results.
12. Never fabricate Azure pricing.
13. Keep secrets out of GitHub.
14. Clearly separate observed, retrieved, and inferred information.
15. Build incrementally.
16. Test every major milestone.
17. Keep the UI demo-friendly.
18. Do not add major features late in the project.
19. If a feature threatens the deadline, simplify it.
20. Always prioritize reliability over feature count.

## Final objective

Deliver a polished, working 4-day prototype of:

> **VISIONIQ — Multimodal Content Intelligence Agent**

that can understand product images and short videos, identify products through visual similarity, retrieve grounded product information, search video content, answer questions with timestamps, and use an agent to intelligently select the appropriate tools.
