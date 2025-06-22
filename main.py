from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import json
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

from database import get_db, Complaint
from models import ComplaintCreate, ComplaintResponse, ComplaintQuery, ComplaintDetails

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM-Powered Grievance Management System",
    description="A grievance system with LLM-powered APIs for complaint collection and retrieval",
    version="2.0.0"
)

# Initialize Ollama LLM
try:
    llm = OllamaLLM(
        model="hf.co/MaziyarPanahi/gemma-3-1b-it-GGUF:Q8_0",
        temperature=0.7
    )
    logger.info("Ollama LLM initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Ollama LLM: {e}")
    llm = None

def extract_data_fallback(message: str) -> dict:
    """Fallback extraction using regex patterns when LLM fails"""
    import re
    
    extracted_data = {
        "name": None,
        "mobile_number": None,
        "complaint_text": None,
        "category": "general",
        "priority": "medium"
    }
    
    # Extract mobile number
    mobile_match = re.search(r'\b\d{10}\b', message)
    if mobile_match:
        extracted_data["mobile_number"] = mobile_match.group()
    
    # Extract name using various patterns
    name_patterns = [
        r'my name is\s+([A-Za-z\s]+?)(?:\s|,|\.|$)',
        r'i am\s+([A-Za-z\s]+?)(?:\s|,|\.|$)',
        r'name:\s*([A-Za-z\s]+?)(?:\s|,|\.|$)',
        r'call me\s+([A-Za-z\s]+?)(?:\s|,|\.|$)',
        r'([A-Za-z\s]+?)\s+here(?:\s|,|\.|$)',
        r'([A-Za-z\s]+?)\s+is my name(?:\s|,|\.|$)'
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, message, re.IGNORECASE)
        if name_match:
            extracted_data["name"] = name_match.group(1).strip()
            break
    
    # Extract complaint text (everything after name/mobile, excluding the extraction patterns)
    # Remove name and mobile patterns from the message to get complaint text
    complaint_text = message
    
    # Remove name patterns
    for pattern in name_patterns:
        complaint_text = re.sub(pattern, '', complaint_text, flags=re.IGNORECASE)
    
    # Remove mobile pattern
    complaint_text = re.sub(r'\b\d{10}\b', '', complaint_text)
    
    # Clean up the complaint text
    complaint_text = re.sub(r'\s+', ' ', complaint_text).strip()
    complaint_text = re.sub(r'^[,\s]+', '', complaint_text)
    complaint_text = re.sub(r'[,\s]+$', '', complaint_text)
    
    if complaint_text:
        extracted_data["complaint_text"] = complaint_text
    
    # Determine category based on keywords
    if any(word in message.lower() for word in ['billing', 'bill', 'charge', 'payment', 'cost']):
        extracted_data["category"] = "billing"
    elif any(word in message.lower() for word in ['technical', 'app', 'software', 'crash', 'bug']):
        extracted_data["category"] = "technical"
    elif any(word in message.lower() for word in ['service', 'support', 'customer service']):
        extracted_data["category"] = "service"
    
    # Determine priority based on keywords
    if any(word in message.lower() for word in ['urgent', 'emergency', 'critical']):
        extracted_data["priority"] = "urgent"
    elif any(word in message.lower() for word in ['high', 'important', 'serious']):
        extracted_data["priority"] = "high"
    elif any(word in message.lower() for word in ['low', 'minor', 'small']):
        extracted_data["priority"] = "low"
    
    return extracted_data

# LLM Prompts
COMPLAINT_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["user_message"],
    template="""
    You are a complaint data extractor. Extract complaint details from the user message and return ONLY a valid JSON object.
    
    CRITICAL RULES:
    1. Extract names from ANY of these patterns:
       - "my name is [NAME]"
       - "I am [NAME]"
       - "Name: [NAME]"
       - "call me [NAME]"
       - "[NAME] here"
       - "[NAME] is my name"
    2. Extract mobile numbers in 10-digit format (e.g., 1234567890)
    3. Extract complaint text (the actual problem description)
    4. Set category as: technical, billing, service, general
    5. Set priority as: low, medium, high, urgent
    6. Return ONLY the JSON object, no additional text, code, or explanations
    7. If a field cannot be extracted, use null (not "null" as string)
    
    User message: {user_message}
    
    Return ONLY this JSON structure (no markdown, no code blocks):
    {{
        "name": "extracted_name_or_null",
        "mobile_number": "extracted_mobile_number_or_null", 
        "complaint_text": "extracted_complaint_description_or_null",
        "category": "extracted_category_or_general",
        "priority": "extracted_priority_or_medium"
    }}"""
)

COMPLAINT_RETRIEVAL_PROMPT = PromptTemplate(
    input_variables=["user_query", "complaints_data"],
    template="""
    Based on the user query and available complaint data, provide a helpful response.
    
    User Query: {user_query}
    
    Available Complaints Data:
    {complaints_data}
    
    Provide a natural, helpful response that:
    1. Addresses the user's specific query
    2. Mentions relevant complaint details if found
    3. Is friendly and professional
    4. Suggests next steps if appropriate
    
    Response:"""
)

@app.get("/")
async def root():
    return {"message": "LLM-Powered Grievance Management System API"}

@app.post("/collect-complaint", response_model=ComplaintResponse)
async def collect_and_store_complaint(query: ComplaintQuery, db: Session = Depends(get_db)):
    """
    LLM-powered API to extract complaint details from user message and store in database
    """
    try:
        logger.info(f"Processing complaint collection request: {query.message}")
        
        if not llm:
            raise HTTPException(status_code=500, detail="LLM service not available")
        
        # Use LLM to extract complaint details
        prompt = COMPLAINT_EXTRACTION_PROMPT.format(user_message=query.message)
        llm_response = llm.invoke(prompt)
        
        logger.info(f"LLM response: {llm_response}")
        
        # Parse LLM response
        try:
            # Clean the response and extract JSON
            response_text = llm_response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Try to find JSON object in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group()
            
            extracted_data = json.loads(response_text.strip())
            logger.info(f"Extracted data: {extracted_data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Raw response: {llm_response}")
            # Fallback to regex extraction
            logger.info("Using fallback regex extraction")
            extracted_data = extract_data_fallback(query.message)
        
        # Validate extracted data
        name = extracted_data.get("name")
        mobile_number = extracted_data.get("mobile_number")
        complaint_text = extracted_data.get("complaint_text")
        category = extracted_data.get("category", "general")
        priority = extracted_data.get("priority", "medium")
        
        # Check if we have minimum required data
        if not name or not mobile_number or not complaint_text:
            missing_fields = []
            if not name:
                missing_fields.append("name")
            if not mobile_number:
                missing_fields.append("mobile number")
            if not complaint_text:
                missing_fields.append("complaint description")
            
            raise HTTPException(
                status_code=400, 
                detail=f"Incomplete complaint data. Missing: {', '.join(missing_fields)}"
            )
        
        # Create and store complaint
        db_complaint = Complaint(
            name=name,
            mobile_number=mobile_number,
            complaint_text=complaint_text,
            category=category,
            priority=priority
        )
        
        db.add(db_complaint)
        db.commit()
        db.refresh(db_complaint)
        
        logger.info(f"Complaint stored successfully: {db_complaint.complaint_id}")
        
        return ComplaintResponse.model_validate(db_complaint)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error collecting complaint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error collecting complaint: {str(e)}")

@app.post("/retrieve-complaints", response_model=ComplaintDetails)
async def retrieve_complaint_info(query: ComplaintQuery, db: Session = Depends(get_db)):
    """
    LLM-powered API to retrieve and present complaint information based on user query
    """
    try:
        logger.info(f"Processing complaint retrieval request: {query.message}")
        
        if not llm:
            raise HTTPException(status_code=500, detail="LLM service not available")
        
        # Extract search criteria from user query
        search_criteria = {}
        
        # Look for mobile number in query
        import re
        mobile_match = re.search(r'\b\d{10}\b', query.message)
        if mobile_match:
            search_criteria['mobile_number'] = mobile_match.group()
        
        # Look for name in query
        name_patterns = [
            r'name[:\s]+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:complaint|issue)',
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, query.message, re.IGNORECASE)
            if name_match:
                search_criteria['name'] = name_match.group(1).strip()
                break
        
        # Query database based on criteria
        db_query = db.query(Complaint)
        
        if 'mobile_number' in search_criteria:
            db_query = db_query.filter(Complaint.mobile_number == search_criteria['mobile_number'])
        
        if 'name' in search_criteria:
            db_query = db_query.filter(Complaint.name.ilike(f"%{search_criteria['name']}%"))
        
        # If no specific criteria, get recent complaints
        if not search_criteria:
            db_query = db_query.order_by(Complaint.created_at.desc()).limit(5)
        
        complaints = db_query.all()
        
        logger.info(f"Found {len(complaints)} complaints for query")
        
        # Format complaints data for LLM
        if complaints:
            formatted_complaints = []
            for complaint in complaints:
                formatted_complaints.append({
                    "complaint_id": complaint.complaint_id,
                    "name": complaint.name,
                    "mobile_number": complaint.mobile_number,
                    "complaint_text": complaint.complaint_text,
                    "category": complaint.category,
                    "priority": complaint.priority,
                    "status": complaint.status,
                    "created_at": complaint.created_at.strftime("%Y-%m-%d %H:%M"),
                    "updated_at": complaint.updated_at.strftime("%Y-%m-%d %H:%M")
                })
            
            complaints_data = json.dumps(formatted_complaints, indent=2)
        else:
            complaints_data = "No complaints found matching the criteria."
        
        # Use LLM to generate response
        prompt = COMPLAINT_RETRIEVAL_PROMPT.format(
            user_query=query.message,
            complaints_data=complaints_data
        )
        
        llm_response = llm.invoke(prompt)
        response_text = llm_response.strip()
        
        logger.info(f"LLM retrieval response: {response_text}")
        
        return ComplaintDetails(
            query=query.message,
            response=response_text,
            complaints_found=len(complaints),
            complaints=[ComplaintResponse.model_validate(c) for c in complaints]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving complaints: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving complaints: {str(e)}")

@app.get("/complaints", response_model=List[ComplaintResponse])
async def get_all_complaints(db: Session = Depends(get_db)):
    """Get all complaints (for admin purposes)"""
    try:
        complaints = db.query(Complaint).order_by(Complaint.created_at.desc()).all()
        logger.info(f"Retrieved {len(complaints)} total complaints")
        return [ComplaintResponse.model_validate(c) for c in complaints]
    except Exception as e:
        logger.error(f"Error fetching all complaints: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching all complaints: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 