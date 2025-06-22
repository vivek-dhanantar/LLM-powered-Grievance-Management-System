# LLM-powered-Grievance-Management-System
Grievance chatbot using Streamlit, SQLite, FastAPI, and locally hosted Qwen 3 via Ollama. Handles complaint registration and status checks with LLM-driven intent detection and response generation. Stores user data in SQLite and provides a natural chat interface.

# Features

- **LLM-Powered Complaint Collection**: Automatically extract complaint details from natural language
- **Intelligent Complaint Retrieval**: Search complaints using natural language queries
- **FastAPI Backend**: RESTful API with automatic documentation
- **Streamlit Web Interface**: User-friendly web application
- **SQLite Database**: Persistent storage with proper schema
- **Ollama Integration**: Local LLM processing for data privacy

# System Architecture


┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI API   │    │   SQLite DB     │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │   (Processing)  │
                       └─────────────────┘

# Pre-Requirements

1. Python Environment
Python 3.9+
Ensure Python is installed and available in your system PATH.

2. SQLite (built-in with Python)
No separate installation needed. Python’s sqlite3 module handles it.
Used to store complaint records locally.

3. Ollama (for Qwen 3 Model)
      Install Ollama from: https://ollama.com

Pull the Qwen 3 model:
      ollama run qwen:3b
      or 
      chose any huggingface model
4. Text Editor or IDE
VS Code, PyCharm, or any code editor for writing and running Python code.

5. Optional Tools
Postman: For testing FastAPI endpoints.
SQLite Browser: GUI to view/edit database contents.
