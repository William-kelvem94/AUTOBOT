"""
Main FastAPI application for AUTOBOT
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from core.ai_engine import AIEngine
from core.automation_engine import AutomationEngine
from core.nlp_processor import NLPProcessor
from api.routes import chat, automation, webhook, integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
ai_engine: AIEngine = None
automation_engine: AutomationEngine = None
nlp_processor: NLPProcessor = None

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Remove disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting AUTOBOT application...")
    
    global ai_engine, automation_engine, nlp_processor
    
    try:
        # Initialize core components
        ai_engine = AIEngine(
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            default_model=os.getenv("DEFAULT_MODEL", "llama3")
        )
        
        automation_engine = AutomationEngine()
        nlp_processor = NLPProcessor()
        
        # Initialize AI engine
        await ai_engine.initialize()
        
        # Connect automation engine with AI
        automation_engine.set_ai_interpreter(ai_engine)
        
        logger.info("AUTOBOT initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize AUTOBOT: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AUTOBOT...")
    # Cleanup code here if needed

# Create FastAPI application
app = FastAPI(
    title="AUTOBOT API",
    description="Local AI Assistant and Automation System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(automation.router, prefix="/api/automation", tags=["automation"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["webhook"])
app.include_router(integration.router, prefix="/api/integration", tags=["integration"])

# Serve static files
if os.path.exists("ui/web/static"):
    app.mount("/static", StaticFiles(directory="ui/web/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    try:
        with open("ui/web/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>AUTOBOT</title></head>
            <body>
                <h1>AUTOBOT API</h1>
                <p>API is running. Web interface not found.</p>
                <p>Available endpoints:</p>
                <ul>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/api/chat/health">Health Check</a></li>
                </ul>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "ai_engine": ai_engine is not None,
            "automation_engine": automation_engine is not None,
            "nlp_processor": nlp_processor is not None
        }
    }

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type", "chat")
            
            if message_type == "chat":
                # Process chat message
                user_message = data.get("message", "")
                user_id = data.get("user_id", "anonymous")
                session_id = data.get("session_id", client_id)
                
                if user_message:
                    try:
                        # Process with AI engine
                        response = await ai_engine.process_message(
                            user_message, user_id, session_id
                        )
                        
                        # Send response back
                        await manager.send_personal_message({
                            "type": "chat_response",
                            "message": response.content,
                            "metadata": response.metadata,
                            "timestamp": response.timestamp.isoformat()
                        }, client_id)
                        
                    except Exception as e:
                        logger.error(f"Error processing chat message: {e}")
                        await manager.send_personal_message({
                            "type": "error",
                            "message": "Erro ao processar mensagem"
                        }, client_id)
            
            elif message_type == "automation":
                # Handle automation commands
                action = data.get("action", "")
                
                if action == "create":
                    description = data.get("description", "")
                    try:
                        script = await automation_engine.create_automation_from_text(
                            description, client_id
                        )
                        await manager.send_personal_message({
                            "type": "automation_created",
                            "script_id": script.id,
                            "name": script.name,
                            "description": script.description
                        }, client_id)
                    except Exception as e:
                        await manager.send_personal_message({
                            "type": "error",
                            "message": f"Erro ao criar automação: {e}"
                        }, client_id)
                
                elif action == "execute":
                    script_id = data.get("script_id", "")
                    parameters = data.get("parameters", {})
                    try:
                        result = await automation_engine.execute_automation(
                            script_id, parameters
                        )
                        await manager.send_personal_message({
                            "type": "automation_result",
                            "result": result
                        }, client_id)
                    except Exception as e:
                        await manager.send_personal_message({
                            "type": "error",
                            "message": f"Erro ao executar automação: {e}"
                        }, client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

# Dependency injection for routes
def get_ai_engine() -> AIEngine:
    if ai_engine is None:
        raise HTTPException(status_code=503, detail="AI Engine not initialized")
    return ai_engine

def get_automation_engine() -> AutomationEngine:
    if automation_engine is None:
        raise HTTPException(status_code=503, detail="Automation Engine not initialized")
    return automation_engine

def get_nlp_processor() -> NLPProcessor:
    if nlp_processor is None:
        raise HTTPException(status_code=503, detail="NLP Processor not initialized")
    return nlp_processor

def get_connection_manager() -> ConnectionManager:
    return manager

# Update routes to use dependency injection
chat.get_ai_engine = get_ai_engine
chat.get_nlp_processor = get_nlp_processor
automation.get_automation_engine = get_automation_engine
webhook.get_ai_engine = get_ai_engine
integration.get_ai_engine = get_ai_engine

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True if os.getenv("DEBUG", "false").lower() == "true" else False
    )