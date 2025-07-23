# ArchiveIQ

**ArchiveIQ** is an AI-powered semantic document search system that allows users to upload documents and ask natural language questions about their contents. It uses a Retrieval-Augmented Generation (RAG) pipeline built on a lightweight, modern stack designed for low-cost, low-maintenance deployment.

---

## 🚀 Features

- **Document Ingestion**: Upload and process plain text documents or extract from PDF/DOCX (extension-ready).
- **Semantic Chunking**: Break documents into overlapping chunks for contextual recall.
- **Embedding Generation**: Vectorize chunks using `mixedbread-ai/mxbai-embed-large-v1` from sentence-transformers.
- **Vector Storage**: Store embeddings in Supabase Postgres using the `pgvector` extension.
- **Semantic Search**: Query documents using natural language and retrieve the most relevant content chunks.
- **RAG Pipeline**: Retrieve document chunks and synthesize answers via LLM integration (future extension).

---

## 🧱 Tech Stack

- **Backend**: Python + Jupyter Notebook for orchestration
- **Embedding Model**: `mixedbread-ai/mxbai-embed-large-v1` via `sentence-transformers`
- **Database**: Supabase Postgres with `pgvector`
- **Authentication (optional)**: Supabase Auth (future integration)
- **File Storage (optional)**: Supabase Storage (future integration)

---

## 📦 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/deanlockgaard/archiveiq.git
cd archiveiq
```

### 2. Create a Supabase Project

- Go to [Supabase.io](https://supabase.io) and create a new project.
- In the **SQL Editor**, run the following SQL:

```sql
create extension vector;

create table documents (
  id bigserial primary key,
  content text,
  embedding vector(1024)
);
```

- Create the RPC function for vector search:

```sql
create or replace function match_documents (
  query_embedding vector(1024),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  content text,
  similarity float
)
language sql stable
as $$
  select
    documents.id,
    documents.content,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
```

- Go to **Project Settings > API**, and copy your Supabase URL and `service_role` API key.

### 3. Create a `.env` File

Create a `.env` file in the project root:

```env
SUPABASE_URL="YOUR_SUPABASE_URL"
SUPABASE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"
```

### 4. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install jupyter supabase sentence-transformers python-dotenv langchain
```

---

## 🧪 Running the System

Launch the notebook:

```bash
jupyter notebook rag_pipeline.ipynb
```

Follow the cell-by-cell instructions to:
- Load your sample or uploaded text
- Chunk it
- Generate embeddings
- Store it in Supabase
- Query it using semantic similarity

---

## 🔍 Sample Use Case

- Upload a research article
- Ask: “What is the main conclusion?”
- The system will retrieve and display the most relevant paragraphs from the stored content.

---

## 📌 Roadmap

- [ ] Add file upload UI (PDF/DOCX support)
- [ ] Integrate Supabase Auth for multi-user access
- [ ] Convert pipeline into a FastAPI or Flask backend
- [ ] Add frontend UI with HTMX or Streamlit
- [ ] Extend with LLM-based answer synthesis

---

## 📄 License

MIT License. See `LICENSE` file for details.

---

## 🧠 Credits

Developed by Dean Lockgaard.
Embedding model: [`mixedbread-ai/mxbai-embed-large-v1`](https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1)
Vector DB: [Supabase](https://supabase.io) + [pgvector](https://github.com/pgvector/pgvector)
