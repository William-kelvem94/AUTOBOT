"""
Automation Engine - System for recording and executing user automations
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import uuid

import pyautogui
import keyboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AutomationStep:
    """Single step in an automation sequence"""
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    parameters: Dict[str, Any] = None
    delay: float = 1.0
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

@dataclass
class AutomationScript:
    """Complete automation script"""
    id: str
    name: str
    description: str
    steps: List[AutomationStep]
    triggers: List[str]
    conditions: List[Dict]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class ActionRecorder:
    """Records user actions for automation creation"""
    
    def __init__(self):
        self.recording = False
        self.recorded_actions: List[Dict] = []
        self.start_time = None
        
    def start_recording(self, session_id: str):
        """Start recording user actions"""
        self.recording = True
        self.recorded_actions = []
        self.start_time = time.time()
        self.session_id = session_id
        
        # Set up keyboard and mouse listeners
        keyboard.on_press(self._on_key_press)
        keyboard.on_release(self._on_key_release)
        
        logger.info(f"Started recording session: {session_id}")
    
    def stop_recording(self):
        """Stop recording and return actions"""
        self.recording = False
        keyboard.unhook_all()
        
        actions = self.recorded_actions.copy()
        self.recorded_actions = []
        
        logger.info(f"Stopped recording, captured {len(actions)} actions")
        return actions
    
    def _on_key_press(self, event):
        """Handle key press events"""
        if not self.recording:
            return
            
        if hasattr(event, 'name'):
            action = {
                "type": "key_press",
                "key": event.name,
                "timestamp": time.time() - self.start_time,
                "modifiers": []
            }
            
            # Check for modifiers
            if keyboard.is_pressed('ctrl'):
                action["modifiers"].append('ctrl')
            if keyboard.is_pressed('shift'):
                action["modifiers"].append('shift')
            if keyboard.is_pressed('alt'):
                action["modifiers"].append('alt')
            
            self.recorded_actions.append(action)
    
    def _on_key_release(self, event):
        """Handle key release events"""
        if not self.recording:
            return
            
        if hasattr(event, 'name') and event.name in ['enter', 'tab', 'space']:
            action = {
                "type": "key_release",
                "key": event.name,
                "timestamp": time.time() - self.start_time
            }
            self.recorded_actions.append(action)

class AutomationExecutor:
    """Executes automation scripts"""
    
    def __init__(self):
        self.running_automations: Dict[str, bool] = {}
        self.webdrivers: Dict[str, webdriver.Chrome] = {}
        
    async def execute_automation(self, script: AutomationScript, parameters: Dict = None) -> Dict:
        """Execute an automation script"""
        try:
            execution_id = str(uuid.uuid4())
            self.running_automations[execution_id] = True
            
            logger.info(f"Starting execution of automation: {script.name}")
            
            results = []
            for i, step in enumerate(script.steps):
                if not self.running_automations.get(execution_id, False):
                    break
                    
                try:
                    result = await self._execute_step(step, parameters or {})
                    results.append({
                        "step": i,
                        "action": step.action,
                        "result": result,
                        "success": True
                    })
                    
                    # Wait between steps
                    await asyncio.sleep(step.delay)
                    
                except Exception as e:
                    logger.error(f"Error executing step {i}: {e}")
                    results.append({
                        "step": i,
                        "action": step.action,
                        "error": str(e),
                        "success": False
                    })
                    break
            
            # Cleanup
            if execution_id in self.running_automations:
                del self.running_automations[execution_id]
            
            return {
                "execution_id": execution_id,
                "script_name": script.name,
                "success": all(r.get("success", False) for r in results),
                "results": results,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing automation: {e}")
            return {
                "execution_id": execution_id,
                "script_name": script.name,
                "success": False,
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            }
    
    async def _execute_step(self, step: AutomationStep, parameters: Dict) -> Any:
        """Execute a single automation step"""
        action = step.action.lower()
        
        if action == "click":
            return await self._click_action(step, parameters)
        elif action == "type":
            return await self._type_action(step, parameters)
        elif action == "wait":
            return await self._wait_action(step, parameters)
        elif action == "screenshot":
            return await self._screenshot_action(step, parameters)
        elif action == "web_navigate":
            return await self._web_navigate_action(step, parameters)
        elif action == "web_click":
            return await self._web_click_action(step, parameters)
        elif action == "web_type":
            return await self._web_type_action(step, parameters)
        elif action == "hotkey":
            return await self._hotkey_action(step, parameters)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _click_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Execute click action"""
        try:
            if step.target:
                # Try to find target by image or coordinates
                if step.target.startswith("image:"):
                    image_path = step.target[6:]
                    location = pyautogui.locateOnScreen(image_path, confidence=0.8)
                    if location:
                        center = pyautogui.center(location)
                        pyautogui.click(center)
                    else:
                        raise Exception(f"Image not found: {image_path}")
                elif "," in step.target:
                    # Coordinates
                    x, y = map(int, step.target.split(","))
                    pyautogui.click(x, y)
                else:
                    raise Exception(f"Invalid target format: {step.target}")
            else:
                # Click current mouse position
                pyautogui.click()
            
            return {"status": "clicked", "target": step.target}
            
        except Exception as e:
            raise Exception(f"Click action failed: {e}")
    
    async def _type_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Execute type action"""
        try:
            text = step.value or parameters.get("text", "")
            
            # Replace parameter placeholders
            for key, value in parameters.items():
                text = text.replace(f"{{{key}}}", str(value))
            
            pyautogui.typewrite(text, interval=0.05)
            
            return {"status": "typed", "text": text}
            
        except Exception as e:
            raise Exception(f"Type action failed: {e}")
    
    async def _wait_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Execute wait action"""
        try:
            duration = step.parameters.get("duration", 1.0)
            await asyncio.sleep(duration)
            
            return {"status": "waited", "duration": duration}
            
        except Exception as e:
            raise Exception(f"Wait action failed: {e}")
    
    async def _screenshot_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Take a screenshot"""
        try:
            filename = step.parameters.get("filename", f"screenshot_{int(time.time())}.png")
            filepath = f"data/screenshots/{filename}"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            return {"status": "screenshot_taken", "filepath": filepath}
            
        except Exception as e:
            raise Exception(f"Screenshot action failed: {e}")
    
    async def _hotkey_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Execute hotkey combination"""
        try:
            keys = step.target.split("+") if step.target else []
            if keys:
                pyautogui.hotkey(*keys)
                return {"status": "hotkey_pressed", "keys": keys}
            else:
                raise Exception("No hotkey specified")
                
        except Exception as e:
            raise Exception(f"Hotkey action failed: {e}")
    
    async def _web_navigate_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Navigate to URL in web browser"""
        try:
            session_id = parameters.get("session_id", "default")
            url = step.target or step.value
            
            if session_id not in self.webdrivers:
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                self.webdrivers[session_id] = webdriver.Chrome(options=options)
            
            driver = self.webdrivers[session_id]
            driver.get(url)
            
            return {"status": "navigated", "url": url}
            
        except Exception as e:
            raise Exception(f"Web navigate action failed: {e}")
    
    async def _web_click_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Click element in web browser"""
        try:
            session_id = parameters.get("session_id", "default")
            driver = self.webdrivers.get(session_id)
            
            if not driver:
                raise Exception("No active web session")
            
            # Find element by various strategies
            element = None
            if step.target.startswith("id:"):
                element = driver.find_element(By.ID, step.target[3:])
            elif step.target.startswith("class:"):
                element = driver.find_element(By.CLASS_NAME, step.target[6:])
            elif step.target.startswith("css:"):
                element = driver.find_element(By.CSS_SELECTOR, step.target[4:])
            elif step.target.startswith("xpath:"):
                element = driver.find_element(By.XPATH, step.target[6:])
            else:
                element = driver.find_element(By.XPATH, f"//*[text()='{step.target}']")
            
            if element:
                element.click()
                return {"status": "web_clicked", "target": step.target}
            else:
                raise Exception(f"Element not found: {step.target}")
                
        except Exception as e:
            raise Exception(f"Web click action failed: {e}")
    
    async def _web_type_action(self, step: AutomationStep, parameters: Dict) -> Dict:
        """Type text in web element"""
        try:
            session_id = parameters.get("session_id", "default")
            driver = self.webdrivers.get(session_id)
            
            if not driver:
                raise Exception("No active web session")
            
            # Find element
            element = None
            if step.target.startswith("id:"):
                element = driver.find_element(By.ID, step.target[3:])
            elif step.target.startswith("name:"):
                element = driver.find_element(By.NAME, step.target[5:])
            elif step.target.startswith("css:"):
                element = driver.find_element(By.CSS_SELECTOR, step.target[4:])
            
            if element:
                text = step.value or parameters.get("text", "")
                element.clear()
                element.send_keys(text)
                return {"status": "web_typed", "target": step.target, "text": text}
            else:
                raise Exception(f"Element not found: {step.target}")
                
        except Exception as e:
            raise Exception(f"Web type action failed: {e}")

class AutomationEngine:
    """Main automation engine coordinating recording and execution"""
    
    def __init__(self):
        self.recorder = ActionRecorder()
        self.executor = AutomationExecutor()
        self.scripts: Dict[str, AutomationScript] = {}
        self.ai_interpreter = None  # Will be set by AI engine
        
    def set_ai_interpreter(self, ai_engine):
        """Set AI engine for interpreting automation descriptions"""
        self.ai_interpreter = ai_engine
    
    async def create_automation_from_text(self, description: str, user_id: str) -> AutomationScript:
        """Create automation from natural language description using AI"""
        try:
            if not self.ai_interpreter:
                raise Exception("AI interpreter not available")
            
            # Use AI to generate automation
            automation_data = await self.ai_interpreter.generate_automation(description, user_id)
            
            if "error" in automation_data:
                raise Exception(automation_data["error"])
            
            # Convert to AutomationScript
            steps = [
                AutomationStep(
                    action=step.get("action", ""),
                    target=step.get("target"),
                    value=step.get("text"),
                    parameters=step.get("parameters", {}),
                    delay=step.get("delay", 1.0)
                )
                for step in automation_data.get("steps", [])
            ]
            
            script = AutomationScript(
                id=str(uuid.uuid4()),
                name=automation_data.get("name", "Untitled Automation"),
                description=automation_data.get("description", description),
                steps=steps,
                triggers=automation_data.get("triggers", []),
                conditions=automation_data.get("conditions", []),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store script
            self.scripts[script.id] = script
            
            return script
            
        except Exception as e:
            logger.error(f"Error creating automation from text: {e}")
            raise
    
    async def record_user_actions(self, session_id: str) -> str:
        """Start recording user actions"""
        self.recorder.start_recording(session_id)
        return session_id
    
    async def stop_recording_and_create_script(self, session_id: str, name: str, description: str) -> AutomationScript:
        """Stop recording and create automation script"""
        try:
            actions = self.recorder.stop_recording()
            
            # Convert recorded actions to automation steps
            steps = []
            for action in actions:
                if action["type"] == "key_press":
                    steps.append(AutomationStep(
                        action="hotkey" if action.get("modifiers") else "type",
                        target="+".join(action.get("modifiers", []) + [action["key"]]) if action.get("modifiers") else None,
                        value=action["key"] if not action.get("modifiers") else None,
                        delay=0.5
                    ))
            
            script = AutomationScript(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                steps=steps,
                triggers=[],
                conditions=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.scripts[script.id] = script
            return script
            
        except Exception as e:
            logger.error(f"Error creating script from recording: {e}")
            raise
    
    async def execute_automation(self, script_id: str, parameters: Dict = None) -> Dict:
        """Execute automation by ID"""
        if script_id not in self.scripts:
            raise Exception(f"Automation script not found: {script_id}")
        
        script = self.scripts[script_id]
        return await self.executor.execute_automation(script, parameters)
    
    def get_automation(self, script_id: str) -> Optional[AutomationScript]:
        """Get automation script by ID"""
        return self.scripts.get(script_id)
    
    def list_automations(self) -> List[AutomationScript]:
        """List all automation scripts"""
        return list(self.scripts.values())
    
    def delete_automation(self, script_id: str) -> bool:
        """Delete automation script"""
        if script_id in self.scripts:
            del self.scripts[script_id]
            return True
        return False