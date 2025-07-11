"""
Chat API routes
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.ai_engine import AIEngine
from core.nlp_processor import NLPProcessor

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    confidence: float
    metadata: Dict[str, Any]
    timestamp: str
    session_id: str

@router.get("/health")
async def health():
    """Health check for chat service"""
    return {"status": "healthy", "service": "chat"}

# Global dependency functions (set by main.py)
get_ai_engine = None
get_nlp_processor = None

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_data: ChatMessage
):
    """Send a message to the AI and get a response"""
    try:
        ai_engine = get_ai_engine()
        
        # Generate session ID if not provided
        session_id = message_data.session_id or f"session_{int(datetime.now().timestamp())}"
        
        # Process message with AI engine
        response = await ai_engine.process_message(
            message_data.message,
            message_data.user_id,
            session_id,
            message_data.context
        )
        
        # Learn from interaction
        await ai_engine.learn_from_interaction({
            "user_id": message_data.user_id,
            "session_id": session_id,
            "message": message_data.message,
            "response": response.content,
            "timestamp": response.timestamp.isoformat()
        })
        
        return ChatResponse(
            response=response.content,
            confidence=response.confidence,
            metadata=response.metadata,
            timestamp=response.timestamp.isoformat(),
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.post("/analyze")
async def analyze_text(
    text: str,
    context: Optional[Dict] = None
):
    """Analyze text for intent, entities, and sentiment"""
    try:
        nlp_processor = get_nlp_processor()
        analysis = await nlp_processor.analyze_text(text, context)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing text: {str(e)}")

@router.post("/knowledge")
async def add_knowledge(
    content: str,
    source: str = "manual",
    metadata: Optional[Dict] = None
):
    """Add knowledge to the AI system"""
    try:
        ai_engine = get_ai_engine()
        success = await ai_engine.add_knowledge(content, source, metadata)
        if success:
            return {"status": "success", "message": "Knowledge added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding knowledge: {str(e)}")