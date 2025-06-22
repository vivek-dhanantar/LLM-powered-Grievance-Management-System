from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ComplaintCreate(BaseModel):
    name: str = Field(..., description="Full name of the complainant")
    mobile_number: str = Field(..., description="Mobile number of the complainant")
    complaint_text: str = Field(..., description="Description of the complaint")

class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    complaint_id: str
    name: str
    mobile_number: str
    complaint_text: str
    category: str = "general"
    priority: str = "medium"
    status: str = "pending"
    created_at: datetime
    updated_at: datetime

class ComplaintQuery(BaseModel):
    message: str = Field(..., description="User's message/query for complaint collection or retrieval")

class ComplaintDetails(BaseModel):
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="LLM-generated response")
    complaints_found: int = Field(..., description="Number of complaints found")
    complaints: List[ComplaintResponse] = Field(..., description="List of found complaints")

class StatusQuery(BaseModel):
    mobile_number: str = Field(..., description="Mobile number to search for complaints")

class ChatMessage(BaseModel):
    message: str = Field(..., description="User's message to the chatbot")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")

class ChatResponse(BaseModel):
    session_id: str
    intent: str
    response: str
    extracted_data: Optional[dict] = None
    is_complete: bool = False 