# main.py
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

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