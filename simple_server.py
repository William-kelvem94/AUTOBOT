#!/usr/bin/env python3
"""
AUTOBOT - Servidor de Desenvolvimento Simplificado
Usando apenas bibliotecas built-in do Python para demonstração
"""

import http.server
import socketserver
import json
import sqlite3
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

class AutobotHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handler personalizado para o AUTOBOT"""
    
    def do_GET(self):
        """Handles GET requests"""
        path = self.path.split('?')[0]
        
        if path == '/':
            self.send_response_json({"message": "🤖 AUTOBOT - Sistema de IA Corporativa", "status": "running", "version": "1.0.0"})
        elif path == '/api/health':
            self.send_response_json({"status": "healthy", "timestamp": datetime.now().isoformat()})
        elif path == '/api/health/detailed':
            self.send_response_json(self.get_detailed_health())
        elif path == '/api/metrics':
            self.send_response_json(self.get_metrics())
        elif path == '/api/system/info':
            self.send_response_json(self.get_system_info())
        else:
            self.send_error(404, "Endpoint not found")
    
    def send_response_json(self, data):
        """Sends JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
    
    def get_detailed_health(self):
        """Health check detalhado"""
        checks = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "components": {}
        }
        
        # Verifica Python
        checks["components"]["python"] = {
            "status": "healthy",
            "version": sys.version.split()[0]
        }
        
        # Verifica banco de dados
        db_path = Path("metrics/autobot_metrics.db")
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM api_metrics")
                count = cursor.fetchone()[0]
                conn.close()
                checks["components"]["database"] = {
                    "status": "healthy",
                    "metrics_count": count
                }
            except Exception as e:
                checks["components"]["database"] = {"status": "error", "error": str(e)}
        else:
            checks["components"]["database"] = {"status": "warning", "message": "Database not found"}
        
        # Verifica estrutura de diretórios
        required_dirs = ["autobot", "IA", "web", "metrics"]
        missing_dirs = [d for d in required_dirs if not Path(d).exists()]
        
        checks["components"]["structure"] = {
            "status": "healthy" if not missing_dirs else "warning",
            "required_dirs": required_dirs,
            "missing_dirs": missing_dirs
        }
        
        return checks
    
    def get_metrics(self):
        """Métricas básicas do sistema"""
        try:
            # Uso básico de CPU/memoria sem psutil
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "basic_metrics": {
                    "python_version": sys.version.split()[0],
                    "platform": sys.platform
                }
            }
            
            # Tenta obter métricas do banco
            db_path = Path("metrics/autobot_metrics.db")
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Conta métricas de API
                cursor.execute("SELECT COUNT(*) FROM api_metrics")
                api_count = cursor.fetchone()[0]
                
                # Conta métricas de sistema
                cursor.execute("SELECT COUNT(*) FROM system_metrics")
                system_count = cursor.fetchone()[0]
                
                conn.close()
                
                metrics["database_metrics"] = {
                    "api_metrics_count": api_count,
                    "system_metrics_count": system_count
                }
            
            return metrics
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_system_info(self):
        """Informações básicas do sistema"""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "autobot_version": "1.0.0",
            "server_type": "Simple HTTP Server (Development)",
            "timestamp": datetime.now().isoformat()
        }
    
    def log_message(self, format, *args):
        """Custom logging to reduce noise"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def start_simple_server(port=5000):
    """Inicia servidor simples"""
    handler = AutobotHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🤖 AUTOBOT Servidor Simples")
            print(f"🌐 Rodando em: http://localhost:{port}")
            print(f"📊 Health Check: http://localhost:{port}/api/health/detailed")
            print(f"📈 Métricas: http://localhost:{port}/api/metrics")
            print(f"ℹ️  Sistema: http://localhost:{port}/api/system/info")
            print(f"🛑 Para parar: Ctrl+C")
            print("=" * 50)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    start_simple_server(port)