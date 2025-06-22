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
