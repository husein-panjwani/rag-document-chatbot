from flask import Flask, render_template, request, jsonify
import os
import fitz
from docx import Document
import re
import chromadb
import google.generativeai as genai

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Create directories if they don't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configure Gemini API with the key from your environment variable
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Initialize ChromaDB client and collection
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="document_chunks")

# --- Helper Functions for File Processing and Embedding ---

def extract_text_from_pdf(filepath):
    """Extracts text from a PDF file."""
    text = ""
    try:
        doc = fitz.open(filepath)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    return text

def extract_text_from_docx(filepath):
    """Extracts text from a DOCX file."""
    text = ""
    try:
        doc = Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None
    return text

def preprocess_text(text):
    """Cleans up the text by removing extra whitespace and newlines."""
    text = re.sub(r'\n+', ' ', text)
    text = text.strip()
    return text

def chunk_text_smarter(text, chunk_size, overlap):
    """
    Splits text into chunks based on sentences with dynamic size and overlap.
    """
    chunks = []
    current_chunk = ""
    sentences = re.split('(?<=[.!?])\s+', text)

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    if len(chunks) > 1 and overlap > 0:
        overlapping_chunks = []
        for i in range(len(chunks)):
            start_index = max(0, i - 1)
            combined_text = ' '.join(chunks[start_index:i+1])
            overlapping_chunks.append(combined_text)
        return overlapping_chunks
    return chunks

def get_embeddings(texts):
    """Converts a list of texts into a list of Gemini embeddings using batching."""
    try:
        # Gemini allows multiple contents in a single call
        response = genai.embed_content(
            model="models/embedding-001",
            content=texts,
            task_type="retrieval_document"
        )
        embeddings = response['embedding']
        return embeddings
    except Exception as e:
        print(f"Error getting embeddings from Gemini API: {e}")
        return None


def store_embeddings(chunks, filename):
    """Converts text chunks into embeddings and stores them in ChromaDB."""
    try:
        embeddings = get_embeddings(chunks)
        if embeddings is None:
            return False

        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename} for _ in range(len(chunks))]

        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully stored {len(chunks)} embeddings in ChromaDB.")
        return True
    except Exception as e:
        print(f"Error storing embeddings in ChromaDB: {e}")
        return False

#  Helper Functions for Querying and LLM Response 

def get_most_relevant_chunks(query, k=5):

    try:
        query_embedding = genai.embed_content(
            model="models/embedding-001",
            content=query,
            task_type="retrieval_query"
        )
        query_vector = query_embedding['embedding']
        
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=k
        )
        
        return results['documents'][0]
    except Exception as e:
        print(f"Error during semantic search: {e}")
        return []

def generate_llm_response(query, context):
  
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            f"You are a helpful assistant. Answer the user's question based on the provided context only. "
            f"If the answer is not in the context, say 'I cannot find the answer in the provided document.'\n\n"
            f"Context: {context}\n\n"
            f"Question: {query}"
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return "Sorry, I am unable to generate a response at this time."

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    extracted_text = None
    
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(file_path)
        else:
            return jsonify({'error': 'Unsupported file type. Please upload a .pdf or .docx'}), 400

    if extracted_text:
        preprocessed_text = preprocess_text(extracted_text)
        text_length = len(preprocessed_text)
        
        if text_length < 2000:
            dynamic_chunk_size = 1000
        elif text_length < 10000:
            dynamic_chunk_size = 700
        else:
            dynamic_chunk_size = 400

        dynamic_overlap = int(dynamic_chunk_size * 0.15)
        
        chunks = chunk_text_smarter(preprocessed_text, chunk_size=dynamic_chunk_size, overlap=dynamic_overlap)
        
        success = store_embeddings(chunks, filename)
        if not success:
            return jsonify({'error': 'Failed to create and store vector embeddings.'}), 500

        print(f"Total text length: {text_length} characters")
        print(f"Dynamic chunk size: {dynamic_chunk_size}")
        print(f"Number of chunks created: {len(chunks)}")
        
        if len(chunks) > 0:
            print("--- First Chunk ---")
            print(chunks[0])
            print("-------------------")
        
        if len(chunks) > 1:
            print("--- Last Chunk ---")
            print(chunks[-1])
            print("------------------")
            
        return jsonify({'message': f'File "{filename}" uploaded, text processed, and embeddings stored successfully!'}), 200
    else:
        return jsonify({'error': 'Failed to extract text from the document.'}), 500

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    user_query = data.get('query')

    if not user_query:
        return jsonify({'error': 'No query provided'}), 400

    relevant_chunks = get_most_relevant_chunks(user_query, k=3)
    
    if not relevant_chunks:
        return jsonify({'response': 'I cannot find any relevant information for that question in the documents.'})

    context = " ".join(relevant_chunks)
    llm_response = generate_llm_response(user_query, context)
    
    return jsonify({'response': llm_response})

@app.route('/clear', methods=['POST'])
def clear_document():
    try:
       
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        
      
        for file in files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            os.remove(file_path)
            
       
        collection.delete(ids=collection.get()['ids'])
        
        return jsonify({'message': 'Document and embeddings cleared successfully! You can now upload a new document.'}), 200
    except Exception as e:
        print(f"Error clearing document: {e}")
        return jsonify({'error': 'Failed to clear the document.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
