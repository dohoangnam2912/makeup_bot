# 💄 makeup_bot

A chatbot developed by **Nam** to assist with makeup-related queries.

## 🚀 How to Run This App

Follow these steps to get the chatbot running locally:

1. **Install dependencies**  
   Go to the `frontend` folder and run:
        npm install
2. **Install backend dependencies**
    Go to the backend folder and run:
        pip install -r requirements.txt

3. **Download Dify**
    Follow the official instructions from Dify's GitHub or documentation to get Dify set up.
    Run Dify with Docker
    Ensure Docker is installed, then run Dify:
        docker compose up -d
4. **Install Kokoro model and Whisper model from Huggingface**       
5. **Start the FastAPI backend**
    Inside the backend folder, run:
        uvicorn main:app --reload
6. **Start the frontend dev server**
    Go to the frontend folder and run:
        npm run dev