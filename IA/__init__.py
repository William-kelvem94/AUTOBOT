"""
AUTOBOT IA - Sistema de Inteligência Artificial
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class AutobotAI:
    """Sistema principal de IA do AUTOBOT"""
    
    def __init__(self):
        self.models_path = Path("IA/treinamento")
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.training_data = []
        
    def load_training_data(self, data_path: str) -> Dict[str, Any]:
        """Carrega dados de treinamento"""
        try:
            if data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
                self.training_data = df.to_dict('records')
            elif data_path.endswith('.json'):
                with open(data_path, 'r', encoding='utf-8') as f:
                    self.training_data = json.load(f)
            else:
                return {"status": "error", "message": "Formato não suportado"}
                
            return {
                "status": "success", 
                "message": f"Carregados {len(self.training_data)} registros",
                "records_count": len(self.training_data)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_training_dataset(self, task_type: str, samples: List[Dict]) -> Dict[str, Any]:
        """Cria dataset de treinamento"""
        try:
            dataset_path = self.models_path / f"{task_type}_dataset.json"
            
            training_set = {
                "task_type": task_type,
                "created_at": datetime.now().isoformat(),
                "samples_count": len(samples),
                "samples": samples
            }
            
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(training_set, f, indent=2, ensure_ascii=False)
            
            return {
                "status": "success",
                "message": f"Dataset criado: {dataset_path}",
                "samples_count": len(samples)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def analyze_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Analisa dados usando técnicas básicas"""
        try:
            if not data:
                return {"status": "error", "message": "Dados vazios"}
            
            df = pd.DataFrame(data)
            
            analysis = {
                "rows_count": len(df),
                "columns_count": len(df.columns),
                "columns": list(df.columns),
                "data_types": df.dtypes.to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_summary": {}
            }
            
            # Análise de colunas numéricas
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                analysis["numeric_summary"][col] = {
                    "mean": float(df[col].mean()) if not df[col].empty else 0,
                    "std": float(df[col].std()) if not df[col].empty else 0,
                    "min": float(df[col].min()) if not df[col].empty else 0,
                    "max": float(df[col].max()) if not df[col].empty else 0
                }
            
            return {"status": "success", "analysis": analysis}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def predict_pattern(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predição básica de padrões (placeholder)"""
        try:
            # Implementação básica - pode ser expandida
            patterns = {
                "email": "@" in str(input_data.get("text", "")),
                "url": "http" in str(input_data.get("text", "")),
                "number": str(input_data.get("text", "")).isdigit(),
                "date": any(sep in str(input_data.get("text", "")) for sep in ["/", "-", "."])
            }
            
            detected_patterns = [pattern for pattern, detected in patterns.items() if detected]
            
            return {
                "status": "success",
                "input": input_data,
                "patterns_detected": detected_patterns,
                "confidence": len(detected_patterns) * 0.25  # Confidence simples
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_model_status(self) -> Dict[str, Any]:
        """Status dos modelos disponíveis"""
        try:
            models = []
            
            for model_file in self.models_path.glob("*.json"):
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        model_data = json.load(f)
                    
                    models.append({
                        "name": model_file.stem,
                        "path": str(model_file),
                        "task_type": model_data.get("task_type", "unknown"),
                        "created_at": model_data.get("created_at", "unknown"),
                        "samples_count": model_data.get("samples_count", 0)
                    })
                except:
                    continue
            
            return {
                "status": "success",
                "models_count": len(models),
                "models": models
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

class TaskLearner:
    """Aprende padrões de tarefas executadas"""
    
    def __init__(self):
        self.task_history = []
        self.patterns = {}
    
    def record_task(self, task_name: str, steps: List[Dict], success: bool) -> None:
        """Registra execução de tarefa para aprendizado"""
        task_record = {
            "task_name": task_name,
            "timestamp": datetime.now().isoformat(),
            "steps": steps,
            "success": success,
            "step_count": len(steps)
        }
        
        self.task_history.append(task_record)
        self._update_patterns()
    
    def _update_patterns(self) -> None:
        """Atualiza padrões baseado no histórico"""
        for record in self.task_history[-10:]:  # Últimas 10 execuções
            task_name = record["task_name"]
            
            if task_name not in self.patterns:
                self.patterns[task_name] = {
                    "success_rate": 0,
                    "avg_steps": 0,
                    "common_failures": [],
                    "executions": 0
                }
            
            pattern = self.patterns[task_name]
            pattern["executions"] += 1
            
            # Atualiza taxa de sucesso
            successful_tasks = sum(1 for r in self.task_history if r["task_name"] == task_name and r["success"])
            pattern["success_rate"] = successful_tasks / pattern["executions"]
            
            # Atualiza média de passos
            total_steps = sum(r["step_count"] for r in self.task_history if r["task_name"] == task_name)
            pattern["avg_steps"] = total_steps / pattern["executions"]
    
    def suggest_improvements(self, task_name: str) -> Dict[str, Any]:
        """Sugere melhorias para uma tarefa"""
        if task_name not in self.patterns:
            return {"message": "Tarefa não encontrada no histórico"}
        
        pattern = self.patterns[task_name]
        suggestions = []
        
        if pattern["success_rate"] < 0.8:
            suggestions.append("Taxa de sucesso baixa - revisar passos críticos")
        
        if pattern["avg_steps"] > 10:
            suggestions.append("Muitos passos - considerar otimização")
        
        return {
            "task_name": task_name,
            "current_performance": pattern,
            "suggestions": suggestions
        }

# Instância global
autobot_ai = AutobotAI()
task_learner = TaskLearner()

def get_ai_status() -> Dict[str, Any]:
    """Status geral do sistema de IA"""
    return {
        "autobot_ai": autobot_ai.get_model_status(),
        "task_learner": {
            "recorded_tasks": len(task_learner.task_history),
            "learned_patterns": len(task_learner.patterns)
        },
        "capabilities": [
            "Data Analysis",
            "Pattern Recognition", 
            "Task Learning",
            "Basic Predictions"
        ]
    }