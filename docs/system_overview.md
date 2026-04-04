# Architecture & System Design: Project brain-dump

## 1. System Overview
Project brain-dump is a "Second Brain" ingestion and indexing engine designed to unify fragmented communication (Emails, Slack, Teams). It transforms unstructured messages into a structured Entity-Relationship-Task map using a hybrid approach combining a Knowledge Graph (Hard Logic) and Retrieval-Augmented Generation or RAG (Nuance & Context).

## 2. Core Tech Stack
* **Language:** Python 3.10+
* **LLM Engine:** Qwen2.5-Coder:30b (via local Ollama)
* **LLM Orchestration:** `instructor` + `pydantic` (for guaranteed structured JSON extraction)
* **Graph Database:** Neo4j (local via Docker)
* **Vector Database:** ChromaDB (local via Docker)
* **Testing:** `pytest` + `pytest-asyncio` + `unittest.mock` (TDD Approach)

## 3. High-Level Architecture
The system operates on a dual-write ingestion pipeline and a hybrid-query retrieval system.



### The Ingestion Flow
1. **Source:** A raw communication (Email/Message) is ingested.
2. **NLP Extraction:** The raw text is passed to Qwen2.5-Coder. The model extracts structured entities (People, Projects, Tasks, Deadlines, Dependencies).
3. **Dual-Storage Routing:**
   * **Vector Store (ChromaDB):** Stores the raw text alongside basic metadata (source_id) for semantic RAG search.
   * **Graph Store (Neo4j):** Upserts nodes and maps relationships based on the extracted JSON.

## 4. The Ontology (Knowledge Graph Schema)
We are blending concepts from **PROV-O** (Provenance tracking) and **PPO** (Project Planning Ontology).

### Nodes
* `Person`: {id, name, email, role}
* `Project`: {id, name, status, priority}
* `Task`: {description, status, due_date, priority}
* `Source`: {id, platform, sender, timestamp} *(The PROV-O record)*

### Relationships
* `(Person)-[:ASSIGNED_TO]->(Task)`
* `(Task)-[:PART_OF]->(Project)`
* `(Task)-[:DEPENDS_ON]->(Task)`
* `(Task)-[:WAITING_ON]->(Person)`
* `(Source)-[:GENERATED]->(Task)` *(Tracks exact origin of a task)*

## 5. Query Strategy (The Hybrid Approach)
When a user asks a question like *"Who is waiting for what, and why is it hanging?"*:
1. **The Graph Query (Hard Logic):** A Cypher query searches Neo4j for `(:Task {status: 'pending'})-[:WAITING_ON]->(:Person)` and returns the exact bottlenecks.
2. **The RAG Query (Context):** The system takes the `Source ID` of the blocked task, pulls the raw email text from ChromaDB, and uses the LLM to summarize *why* it is blocked based on the conversation history.