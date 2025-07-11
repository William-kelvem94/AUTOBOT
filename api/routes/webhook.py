"""
Webhook API routes
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import json
import logging

from core.ai_engine import AIEngine
from integrations.bitrix24 import Bitrix24Integration

router = APIRouter()
logger = logging.getLogger(__name__)

class WebhookResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

@router.get("/health")
async def health():
    """Health check for webhook service"""
    return {"status": "healthy", "service": "webhook"}

# Global dependency functions (set by main.py)  
get_ai_engine = None

@router.post("/bitrix24", response_model=WebhookResponse)
async def bitrix24_webhook(
    request: Request
):
    """Handle Bitrix24 webhook events"""
    try:
        ai_engine = get_ai_engine()
        
        # Get request body
        body = await request.body()
        data = json.loads(body) if body else {}
        
        # Initialize Bitrix24 integration
        bitrix_integration = Bitrix24Integration()
        bitrix_integration.set_ai_engine(ai_engine)
        
        # Process webhook
        result = await bitrix_integration.handle_webhook(data)
        
        return WebhookResponse(
            status="success",
            message="Webhook processed successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error processing Bitrix24 webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

@router.post("/generic", response_model=WebhookResponse)
async def generic_webhook(
    request: Request,
    source: str = "unknown"
):
    """Handle generic webhook events"""
    try:
        ai_engine = get_ai_engine()
        
        # Get request body and headers
        body = await request.body()
        headers = dict(request.headers)
        data = json.loads(body) if body else {}
        
        # Process with AI
        webhook_context = {
            "source": source,
            "headers": headers,
            "data": data,
            "timestamp": str(request.headers.get("timestamp", ""))
        }
        
        # Use AI to understand and respond to webhook
        response = await ai_engine.process_message(
            f"Webhook recebido de {source}: {json.dumps(data, ensure_ascii=False)}",
            "webhook_system",
            f"webhook_{source}",
            webhook_context
        )
        
        return WebhookResponse(
            status="success",
            message="Generic webhook processed",
            data={
                "ai_response": response.content,
                "processed_data": data
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing generic webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

@router.get("/list")
async def list_webhooks():
    """List available webhook endpoints"""
    return {
        "webhooks": [
            {
                "name": "Bitrix24",
                "endpoint": "/api/webhook/bitrix24",
                "method": "POST",
                "description": "Handle Bitrix24 CRM events"
            },
            {
                "name": "Generic",
                "endpoint": "/api/webhook/generic",
                "method": "POST",
                "description": "Handle any webhook with AI processing"
            }
        ]
    }