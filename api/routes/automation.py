"""
Automation API routes
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from core.automation_engine import AutomationEngine, AutomationScript

router = APIRouter()

class AutomationCreateRequest(BaseModel):
    description: str
    user_id: str = "anonymous"
    name: Optional[str] = None

class AutomationExecuteRequest(BaseModel):
    script_id: str
    parameters: Optional[Dict[str, Any]] = None

class AutomationResponse(BaseModel):
    id: str
    name: str
    description: str
    steps: List[Dict]
    created_at: str
    is_active: bool

class RecordingSession(BaseModel):
    session_id: str
    name: str
    description: str

@router.get("/health")
async def health():
    """Health check for automation service"""
    return {"status": "healthy", "service": "automation"}

# Global dependency functions (set by main.py)
get_automation_engine = None

@router.post("/create", response_model=AutomationResponse)
async def create_automation(
    request: AutomationCreateRequest
):
    """Create an automation from natural language description"""
    try:
        automation_engine = get_automation_engine()
        script = await automation_engine.create_automation_from_text(
            request.description, 
            request.user_id
        )
        
        return AutomationResponse(
            id=script.id,
            name=script.name,
            description=script.description,
            steps=[{
                "action": step.action,
                "target": step.target,
                "value": step.value,
                "parameters": step.parameters,
                "delay": step.delay
            } for step in script.steps],
            created_at=script.created_at.isoformat(),
            is_active=script.is_active
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating automation: {str(e)}")

@router.post("/execute")
async def execute_automation(
    request: AutomationExecuteRequest
):
    """Execute an automation script"""
    try:
        automation_engine = get_automation_engine()
        result = await automation_engine.execute_automation(
            request.script_id,
            request.parameters or {}
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing automation: {str(e)}")

@router.get("/list", response_model=List[AutomationResponse])
async def list_automations():
    """List all available automations"""
    try:
        automation_engine = get_automation_engine()
        scripts = automation_engine.list_automations()
        
        return [
            AutomationResponse(
                id=script.id,
                name=script.name,
                description=script.description,
                steps=[{
                    "action": step.action,
                    "target": step.target,
                    "value": step.value,
                    "parameters": step.parameters,
                    "delay": step.delay
                } for step in script.steps],
                created_at=script.created_at.isoformat(),
                is_active=script.is_active
            )
            for script in scripts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing automations: {str(e)}")

@router.get("/{script_id}", response_model=AutomationResponse)
async def get_automation(
    script_id: str,
    automation_engine: AutomationEngine = Depends()
):
    """Get details of a specific automation"""
    try:
        script = automation_engine.get_automation(script_id)
        
        if not script:
            raise HTTPException(status_code=404, detail="Automation not found")
        
        return AutomationResponse(
            id=script.id,
            name=script.name,
            description=script.description,
            steps=[{
                "action": step.action,
                "target": step.target,
                "value": step.value,
                "parameters": step.parameters,
                "delay": step.delay
            } for step in script.steps],
            created_at=script.created_at.isoformat(),
            is_active=script.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automation: {str(e)}")

@router.delete("/{script_id}")
async def delete_automation(
    script_id: str,
    automation_engine: AutomationEngine = Depends()
):
    """Delete an automation script"""
    try:
        success = automation_engine.delete_automation(script_id)
        
        if success:
            return {"status": "success", "message": "Automation deleted"}
        else:
            raise HTTPException(status_code=404, detail="Automation not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting automation: {str(e)}")

@router.post("/record/start")
async def start_recording(
    automation_engine: AutomationEngine = Depends()
):
    """Start recording user actions"""
    try:
        session_id = f"recording_{int(datetime.now().timestamp())}"
        await automation_engine.record_user_actions(session_id)
        
        return {
            "status": "recording_started",
            "session_id": session_id,
            "message": "Action recording started. Perform actions and then stop recording."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting recording: {str(e)}")

@router.post("/record/stop")
async def stop_recording(
    session: RecordingSession,
    automation_engine: AutomationEngine = Depends()
):
    """Stop recording and create automation script"""
    try:
        script = await automation_engine.stop_recording_and_create_script(
            session.session_id,
            session.name,
            session.description
        )
        
        return AutomationResponse(
            id=script.id,
            name=script.name,
            description=script.description,
            steps=[{
                "action": step.action,
                "target": step.target,
                "value": step.value,
                "parameters": step.parameters,
                "delay": step.delay
            } for step in script.steps],
            created_at=script.created_at.isoformat(),
            is_active=script.is_active
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping recording: {str(e)}")