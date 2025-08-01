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
- **Authentication**: Supabase Auth
- **File Storage**: Supabase Storage
- **Frontend**: HTMX, Jinja2, FastAPI, Uvicorn

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
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documents table
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    filename TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index for faster vector similarity searches
CREATE INDEX IF NOT EXISTS documents_embedding_idx
ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create an index on user_id for faster filtering
CREATE INDEX IF NOT EXISTS idx_documents_user_id
ON documents(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Policy: Users can only see their own documents
CREATE POLICY "Users can view own documents"
ON documents
FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can only insert their own documents
CREATE POLICY "Users can insert own documents"
ON documents
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only delete their own documents
CREATE POLICY "Users can delete own documents"
ON documents
FOR DELETE
USING (auth.uid() = user_id);
```

- Create the RPC function for vector search:

```sql
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1024),
  match_threshold float,
  match_count int,
  filter_user_id uuid
)
RETURNS TABLE (
  id bigint,
  content text,
  similarity float
)
LANGUAGE sql stable
AS $$
  SELECT
    documents.id,
    documents.content,
    1 - (documents.embedding <=> query_embedding) as similarity
  FROM documents
  WHERE documents.user_id = filter_user_id
    AND 1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
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
pip install -r requirements.txt
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

#### Phase 1: Critical Fixes & Core Improvements

- [ ] Fix authentication flow - Resolve HTMX bearer token issues
- [ ] Add comprehensive error handling - Better user feedback for failures
- [ ] Implement document management - View, delete, and organize uploaded documents
- [ ] Add upload progress indicators - Show real-time upload status
- [ ] Display document metadata - Show filename, upload date, chunk count in search results

#### Phase 2: Search Enhancement

- [ ] Implement hybrid search - Combine semantic + keyword search (BM25)
- [ ] Add search filters - Filter by date, filename, document type
- [ ] Implement search result highlighting - Highlight matching terms in context
- [ ] Add pagination - Handle large result sets efficiently
- [ ] Create search history - Track and reuse previous searches

#### Phase 3: Performance & Scalability

- [ ] Implement chunk caching - Cache frequently accessed embeddings
- [ ] Add background job processing - Queue large document uploads
- [ ] Optimize chunk size dynamically - Adjust based on document type
- [ ] Implement batch document upload - Process multiple files at once
- [ ] Add database connection pooling - Improve concurrent user handling

#### Phase 4: LLM Integration

- [ ] Extend with LLM-based answer synthesis - Generate comprehensive answers from retrieved chunks
- [ ] Implement query refinement - Use LLM to improve search queries
- [ ] Add conversational search - Multi-turn Q&A with context
- [ ] Create document summarization - Generate summaries of uploaded documents
- [ ] Implement smart chunk reranking - Use LLM to reorder results by relevance

#### Phase 5: Advanced Features

- [ ] Add OCR support - Extract text from scanned PDFs and images
- [ ] Support multiple file formats - DOCX, TXT, HTML, Markdown
- [ ] Implement semantic document clustering - Group similar documents
- [ ] Add collaborative features - Share documents/searches with team members
- [ ] Create export functionality - Export search results and summaries

#### Phase 6: UI/UX Enhancement

- [ ]  Build proper React/Vue frontend - Replace HTMX for richer interactions
- [ ] Add dark mode - User preference support
- [ ] Implement drag-and-drop upload - Better file upload UX
- [ ] Create dashboard with analytics - Usage stats, popular searches
- [ ] Add mobile-responsive design - Optimize for all devices

#### Phase 7: Enterprise Features

- [ ] Implement folder/project organization - Hierarchical document structure
- [ ] Add advanced access controls - Team roles and permissions
- [ ] Create API endpoints - Allow programmatic access
- [ ] Add audit logging - Track all user actions
- [ ] Implement data retention policies - Automatic document expiration

#### Phase 8: AI Enhancement

- [ ] Add cross-document analysis - Find relationships between documents
- [ ] Implement citation generation - Auto-generate citations from sources
- [ ] Create knowledge graph visualization - Visual document relationships
- [ ] Add multilingual support - Search across languages
- [ ] Implement continuous learning - Improve search based on user feedback


---

## 📄 License

MIT License. See `LICENSE` file for details.

---

## 🧠 Credits

- Created by Dean Lockgaard
- Embedding model: [`mixedbread-ai/mxbai-embed-large-v1`](https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1)
- Vector DB: [Supabase](https://supabase.io) + [pgvector](https://github.com/pgvector/pgvector)
