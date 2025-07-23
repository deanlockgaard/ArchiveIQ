# main.py
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import multipart
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Initialize embedding model
model = SentenceTransformer('mixedbread-ai/mxbai-embed-large-v1')

# Initialize FastAPI app and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    """Handles file uploads, processes the document, and stores it."""
    try:
        # Save the uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Extract text from the PDF
        doc = fitz.open(temp_file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        os.remove(temp_file_path) # Clean up the temp file

        # Chunk the text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(full_text)

        # Create embeddings and store in Supabase
        for chunk in chunks:
            embedding = model.encode(chunk).tolist()
            supabase.table('documents').insert({
                'content': chunk,
                'embedding': embedding
            }).execute()

        return HTMLResponse(content=f"Successfully uploaded and processed {file.filename}", status_code=200)

    except Exception as e:
        return HTMLResponse(content=f"An error occurred: {str(e)}", status_code=500)


@app.post("/search")
async def handle_search(request: Request):
    """Handles search queries and returns matching documents."""
    form_data = await request.form()
    query = form_data.get("query")

    if not query:
        return HTMLResponse(content="No results found.", status_code=200)

    # Generate embedding for the query
    query_embedding = model.encode(query).tolist()

    # Find matching documents in Supabase
    response = supabase.rpc('match_documents', {
        'query_embedding': query_embedding,
        'match_threshold': 0.5,
        'match_count': 5
    }).execute()

    # Format results as HTML
    results_html = "<h3>Search Results:</h3>"
    if not response.data:
        results_html += "<p>No relevant documents found.</p>"
    else:
        for doc in response.data:
            results_html += f"<div><h4>Similarity: {doc['similarity']:.2f}</h4><p>{doc['content']}</p></div><hr>"

    return HTMLResponse(content=results_html)