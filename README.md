# Nexus — Async AI Document & Content Engine

> **An async-first, production-grade AI backend** that lets users upload documents for intelligent Q&A retrieval and generate rich, configurable content — all powered by Gemini, Pinecone, RabbitMQ, and FastAPI.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Async%20Worker-FF6600?style=flat&logo=rabbitmq)](https://www.rabbitmq.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache%20%2B%20Status-DC382D?style=flat&logo=redis)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Async%20Pool-4169E1?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Dense%20Vectors-000000?style=flat)](https://www.pinecone.io/)
[![Supabase](https://img.shields.io/badge/Supabase-Storage-3ECF8E?style=flat&logo=supabase)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![Solo Build](https://img.shields.io/badge/Built%20by-Solo%20Developer-blueviolet?style=flat)]()

---

## The Problem

Most AI document tools are **synchronous black boxes** — you upload a file, the API hangs, times out, or gives you no visibility into what's happening. Content generation tools are either too rigid (fixed templates) or too loose (no guardrails). And almost none of them are built with production-grade concerns: retry logic, dead-letter queues, rate limiting, or async database pools.

**Nexus solves this** by building a fully async backend where every heavy operation — document processing, embedding generation, content creation — is offloaded to a message queue worker. The HTTP layer responds instantly with a tracking key. The client polls status. Nothing blocks. Nothing hangs.

---

## What is Nexus?

**Nexus** is a monolith-structured async AI backend with two primary engines:

- **Phase 1 — AI Document Engine:** Upload PDF, DOCX, TXT, or DOC files. Nexus processes them asynchronously via RabbitMQ, chunks and embeds them using Gemini + Pinecone, and lets you ask natural language questions against your own documents with filtered, scored vector retrieval.

- **Phase 2 — Content Engine:** Submit a highly configurable content generation request (tone, audience, domain, structure, creativity level, and more). Nexus queues it, optionally enriches it with real-time web search, and generates publication-quality content via Gemini — with full async status tracking.

- **Bonus — Bluesky Publisher:** Directly publish generated content to your Bluesky (bsky.app) social account, with credential encryption, pagination, and full content history management.

**Built solo. Runs on Docker Compose. Designed like it's going to production.**

---

## Architecture Overview

Nexus follows a **monolith architecture with async worker separation**. The FastAPI layer handles all HTTP concerns — auth, validation, rate limiting, routing — and immediately offloads any compute-heavy work to RabbitMQ. A background worker consumes jobs independently, updates Redis status, and ACKs the message on success.

```
┌─────────────────────────────────────────┐
│              FastAPI Layer              │
│  Auth · Validation · Rate Limit · REST  │
└────────────────┬────────────────────────┘
                 │ Publish Task
        ┌────────▼────────┐
        │    RabbitMQ     │  ← Retry x3 → Dead Letter Queue
        └────────┬────────┘
                 │ Consume
    ┌────────────▼────────────┐
    │   Async Background      │
    │       Worker            │
    │  Redis · Supabase ·     │
    │  Pinecone · Gemini ·    │
    │  PostgreSQL (async)     │
    └─────────────────────────┘
```

**Every database call in this project is fully async** — PostgreSQL uses an async connection pool, Supabase storage client is async, and Redis operations are non-blocking throughout.

---

## Phase 1 — AI Document Engine

### How it works end to end

A user can have **one active file at a time**. If a file already exists, they must delete it before uploading a new one. This design keeps the vector namespace clean and scoped per user.

#### Upload & Processing Flow

> **📹 GIF  — RAG Pipeline: File Upload → Supabase Storage → RabbitMQ → Chunking → Embedding → Pinecone**
<img width="1042" height="566" alt="Image" src="https://github.com/user-attachments/assets/27894a7a-226c-475f-ab59-b8b4d6dafdac" />



**Step-by-step:**

1. **File Validation** — Check type (`pdf`, `docx`, `txt`, `doc`) and enforce max file size. Rename file for safe storage.
2. **Supabase Upload** — File is uploaded to Supabase Storage. Metadata (filename, extension, user ID, file ID) is saved to PostgreSQL.
3. **Previous File Check** — If user already has a file, the old file is deleted from Supabase and pinecone also delete metadata from PostgreSQL before proceeding.
4. **Publish to RabbitMQ** — A task message is published. The HTTP endpoint returns a unique `file_id` immediately — no waiting.
5. **Background Worker picks up the task:**
   - Sets Redis status → `processing`
   - Opens async Supabase client and downloads the file
   - Routes to the correct reader based on file extension: `PDF Text Extractor`, `DOCX Text Extractor`, `TXT Reader`, or `DOC Reader`
   - **Analyzes text structure** to choose the **optimal chunking strategy**
   - Splits using `RecursiveCharacterTextSplitter.from_tiktoken_encoder` with `encoding_name="cl100k_base"` — token-aware splitting that respects
     real LLM token boundaries, preventing context overflow regardless of chunk character length
   - Attaches metadata to each chunk: `doc_id`, `file_name`, `page`
   - Generates dense embeddings using **Gemini Embedding 001** (dimension: **3072**, metric: **cosine**)
   - Stores vectors in **Pinecone** using `namespace = user_id`, filtered by `file_id`
   - Updates Redis status → `completed`
   - RabbitMQ **ACK** sent
6. **On failure:** Retries up to **3 times** → moves to **Dead Letter Queue (DLQ)** → Redis status → `failed` → triggers monitoring/alert

![Upload & RAG Worker Flow]
```mermaid
graph TD

User((User / Client)) -->|POST /upload| API[FastAPI Upload Endpoint]

subgraph File_Validation
    API --> A1[Check File Type txt pdf docx doc]
    A1 --> A2[Check Max File Size]
    A2 --> A3[Rename File]
end

A3 --> B1[Upload File to Supabase Storage]

B1 --> DB[(Save Metadata in PostgreSQL)]
B1 --> ErrCheck{Route Error?}

DB --> Exists{Previous File Exists?}

Exists -->|Yes| DeleteOld[Delete Old File]
Exists -->|No| Continue1[Continue]

DeleteOld --> Continue1

ErrCheck -->|Yes| DeleteSupabase[Delete File from Supabase]
ErrCheck -->|No| Continue2[Continue]

DeleteSupabase --> ReturnError[Return Error]
Continue2 --> Continue1

Continue1 --> FileID[Generate File ID]
FileID --> ReturnClient[Return file_id to Client]

FileID --> Publish[Publish Task to RabbitMQ]

subgraph Async_RAG_Worker
    Publish --> Worker[Background Worker]

    Worker --> RedisProcessing[Redis Status processing]
    RedisProcessing --> SupabaseClient[Open Async Supabase Client]
    SupabaseClient --> Download[Download File]

    Download --> Ext{File Extension}

    Ext -->|pdf| PDF[PDF Text Extractor]
    Ext -->|docx| DOCX[DOCX Text Extractor]
    Ext -->|txt| TXT[TXT Reader]
    Ext -->|doc| DOC[DOC Reader]

    PDF --> Analyze[Analyze Text Structure]
    DOCX --> Analyze
    TXT --> Analyze
    DOC --> Analyze

    Analyze --> Chunk[Choose Chunk Strategy]
    Chunk --> Split[RecursiveCharacterTextSplitter]
    Split --> Meta[Attach Metadata source doc_id file_name page]
    Meta --> Embed[Generate Embeddings GoogleGenerativeAI]
    Embed --> Pinecone[Store Vectors in Pinecone]

    Pinecone --> RedisDone[Update Redis Status completed]
    RedisDone --> Ack[RabbitMQ ACK]

    Pinecone --> Error{Error?}
    Error -->|Yes| Retry{Retry < 3}
    Retry -->|Yes| Worker
    Retry -->|No| RedisFail[Update Redis Status failed]
    RedisFail --> DLQ[Dead Letter Queue]
    DLQ --> Monitor[Monitoring / Alert]
end
```
---

#### Retrieval Flow

> **📹 GIF Placeholder — Retrieval + Delete: Ask question → Redis cache check → Pinecone vector search → LLM answer / Delete flow**
>
> ```
> [ -- This area: show GIF of retrieval (question → answer) and delete (file removal cascade) -- ]
> ```

1. **Rate Limit Check** — Redis-based rate limiting on the endpoint
2. **Metadata Cache** — Check Redis for cached file metadata. If miss → fetch from PostgreSQL → update Redis cache
3. **Query Embedding** — User's question is embedded using Gemini Embedding 001
4. **Vector Search** — Pinecone query scoped to `namespace (user_id)` + `file_id` filter
5. **Retrieve Top 8 chunks**, then **filter by similarity score ≥ 0.70**
6. **Prompt Assembly** — Retrieved context + user question assembled into final prompt
7. **LLM Generation** — Gemini generates the answer
8. **Response returned** to user

![Retrieval Flow]
```mermaid
graph TD

User((User / Client)) -->|POST /retrieve_answer| API[FastAPI Retrieval Endpoint]

API --> Rate[Rate Limit - Redis]

Rate --> Cache{Metadata in Redis Cache?}

Cache -->|Yes| RedisFetch[Fetch Metadata from Redis]
Cache -->|No| PG[(Fetch Metadata from PostgreSQL)]

PG --> UpdateCache[Update Redis Cache]
UpdateCache --> RedisFetch

RedisFetch --> Embed[Generate Query Embedding<br/>- Gemini Embedding 001]

Embed --> Search[Vector Search Pinecone<br/>namespace + file_id]

Search --> TopK[Retrieve Top 8 Chunks]
TopK --> Filter[Filter Chunks Score >= 0.70]
Filter --> Prompt[Build Prompt with Context<br/>+ User Question]

Prompt --> LLM[Generate Answer with LLM]
LLM --> Return[Return Answer to User]

%% ================= STYLING =================

style API fill:#2b9ed8,stroke:#ffffff,color:#ffffff
style Search fill:#8a63d2,stroke:#ffffff,color:#ffffff
style LLM fill:#1fb57a,stroke:#ffffff,color:#ffffff

style User fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Rate fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Cache fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style RedisFetch fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style PG fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style UpdateCache fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Embed fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style TopK fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Filter fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Prompt fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Return fill:#1e1e1e,stroke:#cccccc,color:#ffffff
```

#### Delete Flow

When a user deletes their file, the system performs a **full cascade delete** in order:

| Step | Action |
|------|--------|
| 1 | Fetch file metadata from PostgreSQL |
| 2 | Delete all vectors from Pinecone (`namespace + file_id`) |
| 3 | Delete file from Supabase Storage |
| 4 | Delete metadata record from PostgreSQL |
| 5 | Remove file cache and processing status from Redis |
| 6 | Return success response |

![Delete Flow](
```mermaid
graph TD

User((User / Client)) -->|DELETE /delete/delete_file_data| API[FastAPI Delete Endpoint]

API --> RateLimit[Rate Limit - Redis]

RateLimit --> FetchMeta[(Fetch File Metadata from PostgreSQL)]

FetchMeta --> PineconeDelete[Delete Vectors from Pinecone<br/>namespace + file_id]

PineconeDelete --> SupabaseDelete[Delete File from Supabase Storage]

SupabaseDelete --> DBDelete[(Delete Metadata from PostgreSQL)]

DBDelete --> RedisDelete[Remove File Cache / Status from Redis]

RedisDelete --> Response[Return Success Response]

style API fill:#0ea5e9,color:#fff
style PineconeDelete fill:#8b5cf6,color:#fff
style SupabaseDelete fill:#10b981,color:#fff

```
)

---

#### Pinecone Index Configuration

| Setting | Value |
|---------|-------|
| Type | Dense |
| Metric | Cosine |
| Dimension | 3072 |
| Namespace | `user_id` |
| Filter key | `file_id` |

Namespacing by `user_id` and filtering by `file_id` ensures complete data isolation between users and allows precise scoped retrieval without cross-contamination.

---

## Phase 2 — Content Engine

### Content Generation

Users submit a fully configurable `ContentGenerationConfig` payload:

```python
class ContentGenerationConfig(BaseModel):
    content_type: ContentType        # blog, article, social post, etc.
    domain: Domain                   # tech, marketing, finance, etc.
    tone: Tone = Tone.neutral
    length: Length = Length.medium
    audience: Audience = Audience.general
    creativity_level: Creativity = Creativity.medium
    structure_type: StructureType = StructureType.basic
    writing_style: Optional[WritingStyle] = None
    topic: str

    # Realtime enrichment
    web_search: bool = False
    realtime_search: bool = False

    # Granular controls
    keywords: List[str]
    language: str = "English"
    target_word_count: Optional[int] = None
    include_examples: bool = False
    include_statistics: bool = False
    include_citations: bool = False
    call_to_action: Optional[str] = None
    special_instructions: Optional[str] = None


```

### Content Generation Pipeline

![Content Generation Flow]
```mermaid
graph TD

User((User / Client))

User -->|POST /generate-content| API[FastAPI Entry Point]
User -->|/generate_content/view_content| StatusAPI[Task Status Endpoint]

StatusAPI --> StatusDB[(PostgreSQL Read Job Status)]

%% ================= REQUEST VALIDATION =================
subgraph Request_Validation_and_Security
    API --> Pydantic[Pydantic Schema Validation]
    Pydantic --> Auth[Auth and Rate Limit - Redis]
    Auth --> TaskID[Generate Task ID]
    TaskID --> SaveStatus[(PostgreSQL Save Status queued)]
end

SaveStatus --> ReturnTask[Return task_id to Client]

%% ================= ASYNC WORKER =================
SaveStatus --> Publish[Publish Task]

subgraph Async_Worker_Pipeline
    Publish --> Queue[RabbitMQ Queue]
    Queue --> Worker[Background Worker]
    Worker --> DBSession[Open Async DB Session]

    subgraph AI_Processing_Pipeline
        DBSession --> Processing[Update Status processing]
        Processing --> Safety[Safety and Domain Filtering]
        Safety --> Temp[Temperature Calculation]
        Temp --> Strategy[Strategy Planning]
        Strategy --> Prompt[Prompt Construction]

        Prompt --> Decision{Web Search Enabled}

        Decision -->|True| Web[External Web Search]
        Web --> Summarize[Summarize Search Results]
        Summarize --> FinalLLM[Final Content Generation LLM]

        Decision -->|False| FinalLLM
    end

    FinalLLM --> SaveFinal[(Save Content and Status completed)]
    SaveFinal --> Ack[RabbitMQ ACK]

    SaveFinal --> Error{Error}
    Error -->|Yes| Retry{Retry less than 3}
    Retry -->|Yes| Worker
    Retry -->|No| DLQ[Dead Letter Queue]
    DLQ --> Alert[Monitoring / Alert]
end

%% ================= STYLING =================

%% Blue (Entry)
style API fill:#2b9ed8,stroke:#ffffff,color:#ffffff

%% Orange (Queue)
style Queue fill:#f39c12,stroke:#ffffff,color:#000000

%% Green (Worker)
style Worker fill:#1fb57a,stroke:#ffffff,color:#ffffff

%% Purple (Final LLM)
style FinalLLM fill:#8a63d2,stroke:#ffffff,color:#ffffff

%% Red (DLQ)
style DLQ fill:#e74c3c,stroke:#ffffff,color:#ffffff

%% Dark theme nodes
style User fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style StatusAPI fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style StatusDB fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Pydantic fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Auth fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style TaskID fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style SaveStatus fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style ReturnTask fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Publish fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style DBSession fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Processing fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Safety fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Temp fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Strategy fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Prompt fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Decision fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Web fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Summarize fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style SaveFinal fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Ack fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Error fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Retry fill:#1e1e1e,stroke:#cccccc,color:#ffffff
style Alert fill:#1e1e1e,stroke:#cccccc,color:#ffffff
```

**Step-by-step:**

1. **Request Validation** — Pydantic schema validation, auth check, rate limit via Redis
2. **Task ID generated** → saved to PostgreSQL with status `queued` → returned to client immediately
3. **Published to RabbitMQ**
4. **Background Worker** picks up the task and runs the **AI Processing Pipeline:**
   - Opens async DB session
   - Updates status → `processing`
   - **Safety and Domain Filtering** — checks topic is within allowed domain
   - **Temperature Calculation** — maps `creativity_level` enum to LLM temperature
   - **Strategy Planning** — determines content structure and approach
   - **Prompt Construction** — builds a robust, richly structured prompt
   - **Web Search (conditional)** — if `web_search` or `realtime_search` is `True`, performs external web search and Gemini summarizes results
   - **Final Content Generation** — Gemini LLM receives full prompt: structure strategy + optional web summary + AI knowledge
   - Saves result + status `completed` to PostgreSQL
   - RabbitMQ **ACK**
5. **On failure:** Retry < 3 times → **Dead Letter Queue** → monitoring alert

**Status polling:** Client uses the `task_id` to hit `/generate_content/view_content` which reads job status directly from PostgreSQL.

**Content Management**
Once content is generated, users have full management control:

**View one piece of content** — fetch by content_id, returns only the fields needed (no SELECT *)
**View all content** — cursor-based pagination; client passes a cursor (the last seen content_id) and a limit, and the query fetches the next page efficiently using an **indexed column** — no offset, no full table scans
**Delete one** — remove a specific piece of generated content by ID
**Delete all** — bulk delete all content for the authenticated user in a single query

Every query on the content table is scoped by user_id and hits a targeted index — the database never scans rows it doesn't need.

---

## Bluesky Social Publisher

Users can connect their Bluesky account and publish content directly from Nexus.

- Credentials (handle + app password) are **encrypted** before storage in PostgreSQL
- On publish: credentials are fetched and decrypted, content is posted to Bluesky via their API
- On publish: credentials are fetched and decrypted, content is posted to Bluesky via their AT Protocol API
- All operations — connect, publish, delete account — are handled asynchronously
- Deleting the account removes the encrypted credentials from PostgreSQL entirely

---

## Full Tech Stack

| Technology | Role | Why |
|---|---|---|
| **FastAPI** | HTTP layer, routing, validation | Async-native, Pydantic integration, auto-docs |
| **PostgreSQL (async pool)** | Primary database | Reliable relational store; async pool for non-blocking queries |
| **Redis** | Job status tracking, metadata cache, rate limiting, refresh token store | In-memory speed for ephemeral and hot data |
| **RabbitMQ** | Async task queue | Decouples HTTP from heavy processing; supports retry + DLQ |
| **Pinecone** | Vector database | Managed dense vector search with namespace isolation |
| **Supabase Storage** | File storage | S3-compatible managed storage with async client |
| **Gemini (Google)** | Embeddings + LLM | Embedding 001 (3072-dim) for vectors; Gemini Pro for generation |
| **RecursiveCharacterTextSplitter** | Document chunking | tiktoken-aware splitting preserves semantic boundaries |
| **Docker Compose** | Local orchestration | Single-command spin-up of all 6+ services |

---

## API Routes Reference

### Auth
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns access + refresh token |
| POST | `/auth/refresh` | Exchange refresh token (stored in Redis) for new access token |
| POST | `/auth/logout` | Invalidate refresh token, remove from Redis |

### Document Engine (RAG)
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/rag/upload` | Upload file → Supabase → publish to RabbitMQ → return `file_id` |
| GET | `/rag/status/{file_id}` | Poll processing status from Redis |
| POST | `/rag/retrieve_answer` | Ask a question against your processed document |
| DELETE | `/rag/delete/delete_file_data` | Full cascade delete of file, vectors, metadata, cache |

### Content Engine
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/content/generate-content` | Submit generation config → publish to RabbitMQ → return `task_id` |
| GET | `/content/generate_content/view_content` | Poll task status / retrieve generated content |

### Bluesky Publisher
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/social/connect` | Save encrypted Bluesky credentials |
| POST | `/social/publish` | Publish content to Bluesky |
| GET | `/social/posts` | List all published posts (paginated) |
| GET | `/social/posts/{post_id}` | View single post |
| DELETE | `/social/posts/{post_id}` | Delete post record |
| DELETE | `/social/account` | Remove stored social credentials |

---

## Key Engineering Decisions

### Why RabbitMQ instead of just async background tasks?
FastAPI's `BackgroundTasks` are tied to the request lifecycle and lost on server restart. RabbitMQ persists messages, supports retry logic, and decouples the HTTP server from the worker process entirely. If the worker crashes mid-processing, the message stays in the queue and gets redelivered.

### Why Redis for job status?
Processing status (`queued → processing → completed/failed`) is read-heavy and ephemeral. Redis gives sub-millisecond reads without hitting PostgreSQL on every poll. It doubles as a metadata cache (reducing DB load on the retrieval hot path) and as the rate limiter.

### Why namespace + file_id in Pinecone?
Namespacing by `user_id` provides hard data isolation at the index level. Filtering by `file_id` within a namespace means one user can theoretically have multiple document versions and queries will never bleed across. Deletion is also clean — delete by namespace + file_id filter removes exactly the right vectors with no side effects.

### Why cosine similarity at dimension 3072?
Gemini Embedding 001 produces 3072-dimensional dense vectors. Cosine similarity is chosen over dot product because it normalizes for vector magnitude — two semantically similar chunks with different lengths are treated fairly. The 0.70 score threshold on retrieval filters out weak matches before they reach the LLM context window.

### Why `cl100k_base` tokenizer for chunking?
Character-based splitting is unreliable — a 500-character chunk can be 80 tokens or 200 tokens depending on content. Using `cl100k_base` (the GPT-4 tokenizer) ensures every chunk is split at true token boundaries, so the assembled context passed to Gemini never silently exceeds limits. It's also tokenizer-agnostic — if you swap Gemini for another LLM later, the chunking logic stays correct.

### Why DLQ after 3 retries?
Transient failures (network blip to Supabase, Pinecone timeout) are handled by retries. Permanent failures (corrupt file, invalid format) would retry forever without a DLQ. After 3 attempts, the message is routed to the Dead Letter Queue where it can be inspected, alerted on, and replayed manually — without blocking the main queue.

### Why async DB pool?
A synchronous database driver blocks the event loop on every query, negating FastAPI's async advantage entirely. The async PostgreSQL pool keeps connections open and reuses them efficiently, allowing hundreds of concurrent requests without thread-pool exhaustion.

### Why cursor-based pagination over offset?
`OFFSET N` pagination forces the database to scan and discard N rows on every request — the larger the page number, the slower the query. Cursor-based pagination passes the last seen `content_id` as a cursor and uses a `WHERE id > cursor LIMIT` n query, which hits the index directly and performs the same regardless of how deep into the list the client is. At scale, offset pagination collapses; cursor pagination doesn't.

### Why selective indexing and no SELECT *?
Every table in Nexus only indexes columns that are actually queried — foreign keys, status fields, user IDs, and cursor columns. Indexing every column wastes write performance and storage. Similarly, every query selects only the fields the response actually needs. `SELECT *` pulls unnecessary data across the network, wastes serialization time, and leaks schema details to the response layer. Both decisions are small but compound significantly at volume.

---

## Local Setup

### Prerequisites
- Docker + Docker Compose
- A `.env` file (see below)

### Run

```bash
git clone https://github.com/akash123-dot/Nexus-Async-AI-Document-Content-Engine
cd Nexus-Async-AI-Document-Content-Engine
cp .env.example .env   # fill in your keys
docker compose up --build
```



---

## Environment Variables

```env
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nexus

# Redis
REDIS_URL=redis://localhost:6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET=your-bucket-name

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=your-index-name

# Gemini
GEMINI_API_KEY=your-gemini-api-key

# JWT Auth
SECRET_KEY=your-jwt-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Encryption (for Bluesky credentials)
ENCRYPTION_KEY=your-fernet-encryption-key
```

---

## Future Roadmap

- [ ] Multi-file support per user with per-file namespacing
- [ ] Streaming LLM responses via Server-Sent Events (SSE)
- [ ] Webhook callbacks on job completion (instead of polling)
- [ ] Add support for more social platforms (LinkedIn, Twitter/X)
- [ ] Admin dashboard for DLQ monitoring and message replay
- [ ] Kubernetes deployment manifests
- [ ] Observability: OpenTelemetry tracing across FastAPI + worker

---

## Author

**Akash** — Built solo end to end.

[GitHub](https://github.com/akash123-dot/Nexus-Async-AI-Document-Content-Engine) · Built with FastAPI, Gemini, Pinecone, RabbitMQ, Redis, PostgreSQL, Supabase


![alt text](ScreenRecording2026-03-18210738-ezgif.com-video-to-gif-converter.gif)
