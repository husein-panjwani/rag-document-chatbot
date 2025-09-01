📚 RAG-Based Document Q&A Chatbot

A Flask-based Retrieval-Augmented Generation (RAG) chatbot that allows users to upload documents (PDF/DOCX), extracts their content, creates vector embeddings with Gemini, stores them in ChromaDB, and answers user queries based on the uploaded documents.

🚀 Features

📂 Upload and process PDF/DOCX files

🧹 Automatic text preprocessing & smart chunking

🔑 Generates vector embeddings using Google Gemini

🗄️ Stores embeddings in ChromaDB for semantic search

❓ Ask questions → Retrieves most relevant chunks → Gemini generates final answer

🧽 Clear documents & embeddings for fresh uploads

🛠️ Tech Stack

Backend: Flask

Vector Database: ChromaDB

LLM + Embeddings: Google Gemini

Document Processing:

PyMuPDF (fitz)
 → PDF extraction

python-docx
 → DOCX extraction

Language: Python 3.10+


⚙️ Setup & Installation

1️⃣ Clone the Repository
git clone https://github.com/your-username/rag-chatbot.git
cd rag-chatbot

2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Configure Environment Variables

Create a .env file or export directly:

export GOOGLE_API_KEY="your_gemini_api_key"

5️⃣ Run the App
python app.py


The app will be available at: http://127.0.0.1:5000

🔍 Usage
Upload a Document

POST /upload with a PDF or DOCX file.

Extracted text → Preprocessed → Chunked → Embedded → Stored in ChromaDB.

Ask a Question

POST /query with JSON:

{
  "query": "What is the conclusion of the report?"
}


Returns an answer based on retrieved document context.

Clear Documents

POST /clear → Removes uploaded files and embeddings.

🖼️ Example Flow

Upload report.pdf

Ask: "What are the key findings?"

Response: Gemini generates answer using most relevant document chunks

🔮 Future Improvements

Add support for more file types (.txt, .csv)

Multi-document search

Frontend improvements (React or Next.js)

Authentication for secure use

📜 License

MIT License – feel free to use and modify for your own projects.
