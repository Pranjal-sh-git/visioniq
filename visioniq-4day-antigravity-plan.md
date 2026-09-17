# VisionIQ — 4-Day Antigravity Build Plan

**Multimodal Content Intelligence Agent** | AI-103 Team Project | 4-person team, 4 days

Har din ke end mein ek **validation checklist** hai — jab tak wo saare checks pass nahi hote, agle din shift mat karo. Yeh isliye taaki demo din se pehle koi silent breakage na mile.

---

## Day 1 — Foundation + Image Intelligence

**Goal:** End of Day 1 tak, "upload image → identify product → get grounded spec answer" pipeline kaam karna chahiye — chahe abhi UI rough ho.

### Morning — Setup
- Azure resource group + Microsoft Foundry project create karo
- Model access request/enable karo (vision + generation model)
- Azure AI Search resource banao
- Azure Blob Storage banao
- FastAPI backend skeleton (`backend/main.py`, `routes/`, `config.py`)
- React + TypeScript frontend skeleton (Vite recommended)
- `.env` + `.env.example` set karo — secrets kabhi commit mat karo

**Copy-paste prompt for Antigravity:**
```
Set up a FastAPI backend skeleton with a health-check route at GET /api/health,
CORS enabled for localhost:5173, and config.py loading Azure keys from .env.
Also scaffold a Vite + React + TypeScript frontend with a single page that
calls /api/health and displays the response.
```

### Afternoon — Product dataset + embeddings
- Create 20–50 product catalog as JSON (id, name, brand, category, description, specifications, features, image_urls)
- Generate image embeddings for each catalog product image
- Push embeddings into Azure AI Search vector index
- Build `identify_product()` — user image → embedding → vector search → top-K candidates

**Copy-paste prompt for Antigravity:**
```
Create a products.json catalog with 25 realistic products across 3-4 categories
(e.g. headphones, chairs, shoes, watches) following this schema:
{id, name, brand, category, description, specifications, features, image_urls}.
Then write a script that generates image embeddings for each product's image
and indexes them into an Azure AI Search vector index named "product-catalog".
```

### Evening — Product RAG
- `search_product_knowledge()` — retrieves product spec from catalog/index by product id
- Wire a basic `/api/product/identify` and `/api/product/{id}` endpoint
- LLM answers ONLY from retrieved spec text — no guessing

**Copy-paste prompt for Antigravity:**
```
Implement POST /api/product/identify (accepts an image, returns top-3 matched
products with similarity scores) and GET /api/product/{id} (returns full spec).
Then implement a simple RAG function: given a product_id and a user question,
retrieve the product's spec fields and have the LLM answer strictly from that
context. If the field isn't present, it must say so instead of guessing.
```

### Day 1 — Validation Checklist ✅
Run these before calling Day 1 done — do it live, not "should work":

1. **Health check**: `curl http://localhost:8000/api/health` → 200 OK with expected JSON
2. **Catalog integrity**: open `products.json`, confirm all 20–50 entries have non-empty `id`, `name`, `specifications`
3. **Index populated**: query Azure AI Search index directly (Azure portal or REST) → vector count matches catalog size
4. **Identification works on a KNOWN image**: upload an exact catalog product photo → top-1 result is that same product (sanity check — not the eval set yet)
5. **Identification degrades gracefully on an UNKNOWN image**: upload something not in catalog → system returns "no confident match" rather than a false-confident wrong product
6. **RAG grounding test**: ask for a spec field that EXISTS (e.g. battery life) → correct value returned
7. **RAG honesty test**: ask for a spec field that DOES NOT exist in that product's JSON → system says it's not available, does NOT hallucinate a number
8. **No secrets in git**: `git status` / `git diff --cached` shows no `.env` or API keys staged

If any of 1–8 fail, fix before Day 2 — this pipeline is the backbone everything else builds on.

---

## Day 2 — Video Intelligence + Agent

**Goal:** End of Day 2 tak, "upload short video → ask question → get grounded answer with timestamp" kaam karna chahiye, aur agent tool-routing basic level pe kaam kare.

### Morning — Video processing pipeline
- Video upload endpoint (accept 2–5 min video)
- Audio extraction → transcript (speech-to-text)
- Keyframe extraction at intervals
- Segment transcript into timestamped chunks (e.g. every 20–40s or by topic shift)
- Generate embeddings per chunk

**Copy-paste prompt for Antigravity:**
```
Implement POST /api/video/analyze: accept a video file (2-5 min), extract audio,
transcribe it, extract keyframes at ~10s intervals, and split the transcript
into timestamped chunks of the form
{video_id, start_time, end_time, topic, transcript, embedding}.
Cache all of this to disk/DB keyed by video_id so it's never reprocessed.
```

### Afternoon — Video RAG + summary
- Index video chunks into Azure AI Search (separate index or filtered by video_id)
- `search_video()` — question → embedding → retrieve matching chunk(s) → answer + timestamp
- Auto-generate video summary + key topics list

**Copy-paste prompt for Antigravity:**
```
Implement POST /api/video/search: given a video_id and a natural-language
question, embed the question, retrieve the most relevant timestamped chunk(s)
from the video's indexed segments, and return a grounded answer plus the
start_time/end_time of the supporting segment. Also implement a summary
endpoint that returns a short summary and 3-5 key topics for a processed video.
```

### Evening — Foundry Agent + tool routing
- Define agent tools: `analyze_media()`, `identify_product()`, `search_product_knowledge()`, `search_video()`, `find_similar_products()`
- Wire agent decision logic: route user message to the correct tool, not "call everything"
- Test each tool path independently with a scripted message

**Copy-paste prompt for Antigravity:**
```
Set up a Microsoft Foundry Agent with these tools: identify_product,
search_product_knowledge, search_video, find_similar_products. Write the
routing/orchestration logic so that:
- "What is this product?" -> identify_product
- "What is its battery life?" -> search_product_knowledge
- "What did the reviewer say about X?" -> search_video
- "Show me similar products" -> find_similar_products
Log which tool was selected for each test message so we can verify routing.
```

### Day 2 — Validation Checklist ✅

1. **Video processes once**: process a test video, confirm transcript/keyframes/embeddings are cached — re-running the same question does NOT re-trigger full video processing (check logs/timestamps)
2. **Transcript sanity**: manually read 2-3 chunks against the actual video audio — do they roughly match?
3. **Timestamp accuracy**: ask a question with a known answer location in the video → returned timestamp range is within ~10-15s of the actual moment
4. **Video RAG honesty**: ask something NOT covered in the video → system says it couldn't find that, doesn't fabricate a timestamp
5. **Agent routing — 4 test messages**, one per tool, confirm correct tool fires each time (log/print the selected tool name)
6. **Agent doesn't over-call**: send one simple question → confirm only ONE tool was invoked, not all four
7. **End-to-end video path**: upload → process → ask 2 different questions → both return grounded answers + timestamps without errors in console/server logs

If routing (#5/#6) is shaky, simplify the agent logic now — Day 3 integration will expose any flakiness immediately.

---

## Day 3 — Frontend + Full Integration

**Goal:** End of Day 3 tak, poora demo flow ek hi UI se click-through hona chahiye, image se video se chat tak, koi backend errors ke bina.

### Full day — Build + wire everything
- Image mode UI: upload, preview, product match card, similarity score, attributes, OCR, specs, similar products, chat
- Video mode UI: upload, video player, processing state, summary, key topics, timestamped segments (clickable), chat
- Wire React → FastAPI → Foundry Agent → Azure services end-to-end
- Loading states + error states (don't skip these — demo day disasters usually happen here)

**Copy-paste prompt for Antigravity:**
```
Build the React frontend with two tabs: "Image Intelligence" and "Video
Intelligence". Image tab: upload -> preview -> call /api/product/identify ->
show matched product card with similarity score, specs, and a chat box wired
to the agent. Video tab: upload -> call /api/video/analyze -> show a video
player, summary, key topics, and a chat box; when the agent returns a
timestamp, clicking it should seek the video player to that time. Add loading
spinners during processing and visible error messages on failure — no silent
failures.
```

### Day 3 — Validation Checklist ✅

1. **Cold-start image flow**: fresh browser tab, no cache → upload image → full result renders (product, specs, similar products) without console errors
2. **Cold-start video flow**: fresh browser tab → upload video → processing state shows → summary + segments render after completion
3. **Timestamp click works**: click a returned timestamp in chat → video player actually seeks to that point
4. **Chat continuity**: ask 2-3 follow-up questions in a row in the same session → each gets a correctly-routed, grounded answer
5. **Error states are visible, not silent**: intentionally break something (e.g. stop backend) → UI shows a clear error, not an infinite spinner or blank screen
6. **Browser console clean**: open DevTools console during a full demo run-through → zero unhandled errors/warnings
7. **Network tab check**: confirm no duplicate/redundant calls (e.g. video reprocessing on every question — should hit cache)
8. **Cross-browser sanity**: quick check in a second browser/incognito window — same result

Do the full demo script (upload → identify → ask questions → click timestamp → ask spec question → show similar products) end-to-end at least twice before stopping for the day.

---

## Day 4 — Testing + Polish + Presentation

**Goal:** Reliability over new features. Numbers on the slide should be real, not guessed.

### Morning — Evaluation
- Product identification: 20–30 test images → measure Top-1 and Top-3 accuracy
- Video retrieval: 10–20 questions → measure correct segment/timestamp retrieval
- RAG/QA: 10–20 questions → classify Correct / Partially correct / Incorrect / Hallucinated
- Track processing time, response time, failure rate

**Copy-paste prompt for Antigravity:**
```
Write an evaluation script that runs 25 test product images through
/api/product/identify and computes Top-1 and Top-3 accuracy against known
ground-truth labels. Write a second script that runs 15 test questions
against /api/video/search and records whether the correct segment/timestamp
was retrieved. Output both as a simple results table (CSV or markdown) —
do not hardcode or guess the numbers, compute them from actual runs.
```

### Afternoon — Polish + docs
- Responsible AI: make OBSERVED / RETRIEVED / INFERRED distinction visible in UI or at least documented
- Error handling pass on all endpoints
- README, architecture.md, api.md, evaluation.md, responsible-ai.md
- Remove/simplify anything that's flaky under time pressure — a smaller reliable feature beats a bigger broken one

### Evening — Presentation
- Finalize 5-minute demo script (intro → problem → solution → live demo → impact)
- Rehearse the live demo at least twice, including recovering from one likely failure point
- Prepare a fallback: if live Azure calls are unreliable, have one pre-recorded/cached run ready — clearly labeled as such, never presented as live if it isn't

### Day 4 — Validation Checklist ✅

1. **Eval numbers are real**: re-run the eval scripts once more right before presenting — confirm the numbers on the slide match a fresh run, not a stale one from earlier
2. **No fabricated claims**: read through the presentation script — every capability mentioned actually exists in the running app
3. **Full demo dry run (cold start)**: close everything, restart backend + frontend fresh, run the entire demo script once, time it — should fit in ~2 minutes
4. **Failure recovery rehearsed**: deliberately trigger one likely failure (slow network, bad image) during a dry run and confirm the team knows how to recover on stage
5. **Secrets check**: final `git log` / repo scan — no API keys, no `.env` committed anywhere in history
6. **README completeness**: someone outside the team could clone the repo and follow README to run it locally
7. **Docs match reality**: architecture.md / api.md reflect what's actually built, not the original aspirational plan
8. **Fallback labeled honestly**: if any part of the demo uses precomputed/cached data instead of live processing, this is clearly stated in the docs and the presentation — never passed off as live

---

## Quick reference — what NOT to build (per the master prompt)
Kubernetes, microservices, mobile app, live streaming, custom model training, huge product DB, complex auth, complex CI/CD, real-time multi-camera analytics, unnecessary databases, excessive UI animation. Agar koi feature deadline threaten kar raha hai, simplify karo — mat drop karo poora, bas scope choti karo.
