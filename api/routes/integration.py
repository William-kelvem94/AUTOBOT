"""
Integration API routes
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from integrations.bitrix24 import Bitrix24Integration
from core.ai_engine import AIEngine

router = APIRouter()

class IntegrationConfig(BaseModel):
    platform: str
    config: Dict[str, Any]

class IntegrationAction(BaseModel):
    platform: str
    action: str
    parameters: Dict[str, Any]

class IntegrationResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

@router.get("/health")
async def health():
    """Health check for integration service"""
    return {"status": "healthy", "service": "integration"}

@router.get("/platforms")
async def list_platforms():
    """List available integration platforms"""
    return {
        "platforms": [
            {
                "name": "Bitrix24",
                "id": "bitrix24",
                "description": "CRM and business management platform",
                "features": ["webhooks", "api", "automation"],
                "status": "available"
            },
            {
                "name": "Locaweb",
                "id": "locaweb",
                "description": "Web hosting and cloud services",
                "features": ["api", "automation"],
                "status": "planned"
            },
            {
                "name": "IXCSOFT",
                "id": "ixcsoft",
                "description": "ISP management software",
                "features": ["api", "automation"],
                "status": "planned"
            },
            {
                "name": "Fluctus",
                "id": "fluctus",
                "description": "Network management platform",
                "features": ["api", "monitoring"],
                "status": "planned"
            }
        ]
    }

# Global dependency functions (set by main.py)
get_ai_engine = None

@router.post("/bitrix24/test", response_model=IntegrationResponse)
async def test_bitrix24_integration(
    webhook_url: str
):
    """Test Bitrix24 integration"""
    try:
        ai_engine = get_ai_engine()
        integration = Bitrix24Integration(webhook_url)
        integration.set_ai_engine(ai_engine)
        
        # Test connection
        test_result = await integration.test_connection()
        
        return IntegrationResponse(
            status="success" if test_result else "error",
            message="Connection successful" if test_result else "Connection failed",
            data={"webhook_url": webhook_url}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing integration: {str(e)}")

@router.post("/bitrix24/action", response_model=IntegrationResponse)
async def execute_bitrix24_action(
    action: IntegrationAction,
    webhook_url: str,
    ai_engine: AIEngine = Depends()
):
    """Execute an action in Bitrix24"""
    try:
        integration = Bitrix24Integration(webhook_url)
        integration.set_ai_engine(ai_engine)
        
        result = None
        
        if action.action == "create_task":
            result = await integration.create_task(
                title=action.parameters.get("title", ""),
                description=action.parameters.get("description", ""),
                responsible_id=action.parameters.get("responsible_id", 1)
            )
        elif action.action == "update_deal":
            result = await integration.update_deal(
                deal_id=action.parameters.get("deal_id"),
                fields=action.parameters.get("fields", {})
            )
        elif action.action == "get_leads":
            result = await integration.get_leads(
                limit=action.parameters.get("limit", 10)
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")
        
        return IntegrationResponse(
            status="success",
            message=f"Action {action.action} executed successfully",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing action: {str(e)}")

@router.post("/configure")
async def configure_integration(
    config: IntegrationConfig,
    ai_engine: AIEngine = Depends()
):
    """Configure an integration"""
    try:
        # Store configuration (in a real implementation, this would be persisted)
        # For now, just validate the configuration
        
        if config.platform == "bitrix24":
            required_fields = ["webhook_url"]
            missing_fields = [field for field in required_fields if field not in config.config]
            
            if missing_fields:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required fields: {missing_fields}"
                )
            
            # Test the configuration
            integration = Bitrix24Integration(config.config["webhook_url"])
            integration.set_ai_engine(ai_engine)
            test_result = await integration.test_connection()
            
            if not test_result:
                raise HTTPException(status_code=400, detail="Invalid configuration")
            
            return IntegrationResponse(
                status="success",
                message="Integration configured successfully",
                data={"platform": config.platform}
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Platform {config.platform} not supported yet")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configuring integration: {str(e)}")

@router.get("/status")
async def get_integration_status():
    """Get status of all integrations"""
    return {
        "integrations": {
            "bitrix24": {
                "status": "available",
                "configured": False,  # Would check actual configuration
                "last_sync": None
            },
            "locaweb": {
                "status": "not_implemented",
                "configured": False,
                "last_sync": None
            },
            "ixcsoft": {
                "status": "not_implemented", 
                "configured": False,
                "last_sync": None
            },
            "fluctus": {
                "status": "not_implemented",
                "configured": False,
                "last_sync": None
            }
        }
    }