# main.py
from fastapi import FastAPI, Request, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# This is where app will look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Get JWT_SECRET from Supabase project's API settings
JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
if not JWT_SECRET:
   raise ValueError("SUPABASE_JWT_SECRET not found in environment variables")

# Initialize embedding model
model = SentenceTransformer('mixedbread-ai/mxbai-embed-large-v1')

# Initialize FastAPI app and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],  # Configure appropriately for production
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
   """Dependency to verify the JWT and get the user."""
   credentials_exception = HTTPException(
       status_code=401,
       detail="Could not validate credentials",
       headers={"WWW-Authenticate": "Bearer"},
   )

   try:
       # Define the expected audience
       expected_audience = "authenticated"

       # Decode the JWT token
       payload = jwt.decode(
           token,
           JWT_SECRET,
           algorithms=["HS256"],
           audience=expected_audience
       )

       user_id = payload.get("sub")
       if user_id is None:
           raise credentials_exception

       return {"id": user_id}
   except JWTError:
       raise credentials_exception

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
   """Render the main page."""
   return templates.TemplateResponse("index.html", {"request": request})

class LoginRequest(BaseModel):
   email: str
   password: str

@app.post("/login")
async def login(login_data: LoginRequest):
   """Authenticate user and return JWT token."""
   try:
       response = supabase.auth.sign_in_with_password({
           "email": login_data.email,
           "password": login_data.password
       })

       return {
           "access_token": response.session.access_token,
           "token_type": "bearer"
       }
   except Exception as e:
       raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/upload")
async def handle_upload(
   file: UploadFile = File(...),
   current_user: dict = Depends(get_current_user)
):
   """Handles file uploads for the authenticated user."""
   user_id = current_user.get("id")

   try:
       # Validate file type
       if not file.filename.endswith('.pdf'):
           return HTMLResponse(
               content="Only PDF files are supported",
               status_code=400
           )

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

       # Clean up the temp file
       os.remove(temp_file_path)

       # Check if document has content
       if not full_text.strip():
           return HTMLResponse(
               content="PDF appears to be empty or contains no extractable text",
               status_code=400
           )

       # Chunk the text
       text_splitter = RecursiveCharacterTextSplitter(
           chunk_size=1000,
           chunk_overlap=200
       )
       chunks = text_splitter.split_text(full_text)

       # Create embeddings and store in Supabase with the user_id
       for chunk in chunks:
           embedding = model.encode(chunk).tolist()

           supabase.table('documents').insert({
               'content': chunk,
               'embedding': embedding,
               'user_id': user_id,
               'filename': file.filename  # Store filename for reference
           }).execute()

       return HTMLResponse(
           content=f"Successfully uploaded {file.filename} ({len(chunks)} chunks processed)",
           status_code=200
       )

   except Exception as e:
       return HTMLResponse(
           content=f"An error occurred: {str(e)}",
           status_code=500
       )

@app.post("/search")
async def handle_search(
   request: Request,
   current_user: dict = Depends(get_current_user)
):
   """Handles search queries for the authenticated user."""
   user_id = current_user.get("id")

   form_data = await request.form()
   query = form_data.get("query")

   if not query:
       return HTMLResponse(content="Please enter a search query.", status_code=400)

   try:
       # Create embedding for the query
       query_embedding = model.encode(query).tolist()

       # Call the updated RPC function with user_id parameter
       response = supabase.rpc('match_documents', {
           'query_embedding': query_embedding,
           'match_threshold': 0.5,
           'match_count': 5,
           'filter_user_id': user_id  # Pass user_id as parameter
       }).execute()

       # Format results as HTML
       results_html = "<h3>Search Results:</h3>"
       if not response.data:
           results_html += "<p>No relevant documents found.</p>"
       else:
           for doc in response.data:
               # Escape HTML in content to prevent XSS
               content = doc['content'].replace('<', '&lt;').replace('>', '&gt;')
               similarity_score = doc['similarity'] * 100  # Convert to percentage

               results_html += f"""
               <div style="margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 5px;">
                   <h4 style="margin: 0 0 10px 0;">Relevance: {similarity_score:.1f}%</h4>
                   <p style="margin: 0;">{content}</p>
               </div>
               """

       return HTMLResponse(content=results_html)

   except Exception as e:
       return HTMLResponse(
           content=f"Search error: {str(e)}",
           status_code=500
       )

if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)