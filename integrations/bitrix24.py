"""
Bitrix24 Integration Module
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx

from core.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class Bitrix24Integration:
    """
    Integration with Bitrix24 CRM platform
    """
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.ai_engine: Optional[AIEngine] = None
        
    def set_ai_engine(self, ai_engine: AIEngine):
        """Set AI engine for intelligent processing"""
        self.ai_engine = ai_engine
    
    async def test_connection(self) -> bool:
        """Test connection to Bitrix24"""
        if not self.webhook_url:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                # Try to get user info to test connection
                response = await client.get(
                    f"{self.webhook_url}/user.current",
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Bitrix24 connection test failed: {e}")
            return False
    
    async def handle_webhook(self, data: Dict) -> Dict:
        """
        Handle incoming webhook from Bitrix24
        """
        try:
            event_type = data.get("event", "unknown")
            event_data = data.get("data", {})
            
            logger.info(f"Processing Bitrix24 webhook: {event_type}")
            
            # Process different event types
            if event_type.startswith("ONCRMLEADADD"):
                return await self._handle_lead_added(event_data)
            elif event_type.startswith("ONCRMDEALUPDATE"):
                return await self._handle_deal_updated(event_data)
            elif event_type.startswith("ONCRMCONTACTADD"):
                return await self._handle_contact_added(event_data)
            elif event_type.startswith("ONTASKADD"):
                return await self._handle_task_added(event_data)
            else:
                return await self._handle_generic_event(event_type, event_data)
                
        except Exception as e:
            logger.error(f"Error handling Bitrix24 webhook: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _handle_lead_added(self, data: Dict) -> Dict:
        """Handle new lead creation"""
        try:
            lead_id = data.get("FIELDS", {}).get("ID")
            
            if not lead_id:
                return {"error": "No lead ID provided"}
            
            # Get full lead details
            lead_details = await self.get_lead(lead_id)
            
            if self.ai_engine:
                # Use AI to analyze the lead and suggest actions
                lead_text = f"""
                Novo lead criado no Bitrix24:
                ID: {lead_id}
                Nome: {lead_details.get('NAME', 'N/A')}
                Telefone: {lead_details.get('PHONE', 'N/A')}
                Email: {lead_details.get('EMAIL', 'N/A')}
                Fonte: {lead_details.get('SOURCE_DESCRIPTION', 'N/A')}
                """
                
                ai_response = await self.ai_engine.process_message(
                    lead_text,
                    "bitrix24_system",
                    f"lead_{lead_id}",
                    {"event": "lead_added", "lead_data": lead_details}
                )
                
                return {
                    "status": "processed",
                    "lead_id": lead_id,
                    "ai_analysis": ai_response.content,
                    "suggested_actions": self._extract_suggested_actions(ai_response.content)
                }
            
            return {"status": "processed", "lead_id": lead_id}
            
        except Exception as e:
            logger.error(f"Error handling lead added: {e}")
            return {"error": str(e)}
    
    async def _handle_deal_updated(self, data: Dict) -> Dict:
        """Handle deal update"""
        try:
            deal_id = data.get("FIELDS", {}).get("ID")
            
            if not deal_id:
                return {"error": "No deal ID provided"}
            
            # Get full deal details
            deal_details = await self.get_deal(deal_id)
            
            if self.ai_engine:
                deal_text = f"""
                Negócio atualizado no Bitrix24:
                ID: {deal_id}
                Título: {deal_details.get('TITLE', 'N/A')}
                Valor: {deal_details.get('OPPORTUNITY', 'N/A')}
                Estágio: {deal_details.get('STAGE_ID', 'N/A')}
                """
                
                ai_response = await self.ai_engine.process_message(
                    deal_text,
                    "bitrix24_system",
                    f"deal_{deal_id}",
                    {"event": "deal_updated", "deal_data": deal_details}
                )
                
                return {
                    "status": "processed",
                    "deal_id": deal_id,
                    "ai_analysis": ai_response.content
                }
            
            return {"status": "processed", "deal_id": deal_id}
            
        except Exception as e:
            logger.error(f"Error handling deal updated: {e}")
            return {"error": str(e)}
    
    async def _handle_contact_added(self, data: Dict) -> Dict:
        """Handle new contact creation"""
        try:
            contact_id = data.get("FIELDS", {}).get("ID")
            
            return {"status": "processed", "contact_id": contact_id}
            
        except Exception as e:
            logger.error(f"Error handling contact added: {e}")
            return {"error": str(e)}
    
    async def _handle_task_added(self, data: Dict) -> Dict:
        """Handle new task creation"""
        try:
            task_id = data.get("FIELDS", {}).get("ID")
            
            return {"status": "processed", "task_id": task_id}
            
        except Exception as e:
            logger.error(f"Error handling task added: {e}")
            return {"error": str(e)}
    
    async def _handle_generic_event(self, event_type: str, data: Dict) -> Dict:
        """Handle generic events"""
        try:
            if self.ai_engine:
                event_text = f"Evento Bitrix24 {event_type}: {json.dumps(data, ensure_ascii=False)}"
                
                ai_response = await self.ai_engine.process_message(
                    event_text,
                    "bitrix24_system",
                    f"event_{event_type}",
                    {"event": event_type, "data": data}
                )
                
                return {
                    "status": "processed",
                    "event_type": event_type,
                    "ai_analysis": ai_response.content
                }
            
            return {"status": "processed", "event_type": event_type}
            
        except Exception as e:
            logger.error(f"Error handling generic event: {e}")
            return {"error": str(e)}
    
    async def get_lead(self, lead_id: str) -> Dict:
        """Get lead details by ID"""
        try:
            if not self.webhook_url:
                raise Exception("No webhook URL configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.webhook_url}/crm.lead.get",
                    params={"ID": lead_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error getting lead {lead_id}: {e}")
            return {}
    
    async def get_deal(self, deal_id: str) -> Dict:
        """Get deal details by ID"""
        try:
            if not self.webhook_url:
                raise Exception("No webhook URL configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.webhook_url}/crm.deal.get",
                    params={"ID": deal_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error getting deal {deal_id}: {e}")
            return {}
    
    async def get_leads(self, limit: int = 10) -> List[Dict]:
        """Get list of leads"""
        try:
            if not self.webhook_url:
                raise Exception("No webhook URL configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.webhook_url}/crm.lead.list",
                    params={"ORDER": '{"DATE_CREATE": "DESC"}', "FILTER": '{"STATUS_ID": "NEW"}'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", [])[:limit]
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error getting leads: {e}")
            return []
    
    async def create_task(self, title: str, description: str, responsible_id: int) -> Dict:
        """Create a new task in Bitrix24"""
        try:
            if not self.webhook_url:
                raise Exception("No webhook URL configured")
            
            task_data = {
                "TITLE": title,
                "DESCRIPTION": description,
                "RESPONSIBLE_ID": responsible_id,
                "CREATED_BY": responsible_id,
                "DEADLINE": None  # Could be set based on AI suggestion
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.webhook_url}/tasks.task.add",
                    json={"fields": task_data}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {"error": str(e)}
    
    async def update_deal(self, deal_id: int, fields: Dict) -> Dict:
        """Update a deal in Bitrix24"""
        try:
            if not self.webhook_url:
                raise Exception("No webhook URL configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.webhook_url}/crm.deal.update",
                    json={"ID": deal_id, "fields": fields}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error updating deal: {e}")
            return {"error": str(e)}
    
    def _extract_suggested_actions(self, ai_text: str) -> List[str]:
        """Extract suggested actions from AI response"""
        actions = []
        
        # Simple pattern matching for action suggestions
        if "criar tarefa" in ai_text.lower() or "create task" in ai_text.lower():
            actions.append("create_task")
        
        if "ligar" in ai_text.lower() or "call" in ai_text.lower():
            actions.append("make_call")
        
        if "enviar email" in ai_text.lower() or "send email" in ai_text.lower():
            actions.append("send_email")
        
        if "agendar" in ai_text.lower() or "schedule" in ai_text.lower():
            actions.append("schedule_meeting")
        
        return actions