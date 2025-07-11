#!/usr/bin/env python3
"""
AUTOBOT - Testes de Integração
Valida funcionamento de todos os componentes
"""

import unittest
import sys
import os
import json
import tempfile
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAutobotCore(unittest.TestCase):
    """Testes dos componentes principais"""
    
    def test_requirements_validation(self):
        """Testa se os requirements estão corretos"""
        requirements_path = Path("requirements.txt")
        self.assertTrue(requirements_path.exists(), "requirements.txt não encontrado")
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        essential_packages = ['flask', 'requests', 'pandas', 'numpy']
        for package in essential_packages:
            self.assertIn(package, content, f"Pacote {package} não encontrado")
    
    def test_directory_structure(self):
        """Testa se a estrutura de diretórios está correta"""
        expected_dirs = [
            "autobot/api_drivers",
            "autobot/navigation_flows", 
            "autobot/recorded_tasks",
            "backups",
            "IA/treinamento",
            "src",
            "web/src",
            "metrics"
        ]
        
        for directory in expected_dirs:
            dir_path = Path(directory)
            self.assertTrue(dir_path.exists(), f"Diretório {directory} não encontrado")
    
    def test_database_creation(self):
        """Testa criação do banco de métricas"""
        from setup_automatico import create_metrics_database
        
        # Remove banco existente para teste
        db_path = Path("metrics/autobot_metrics.db")
        if db_path.exists():
            db_path.unlink()
        
        # Cria banco
        create_metrics_database()
        self.assertTrue(db_path.exists(), "Banco de métricas não foi criado")
        
        # Verifica tabelas
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['api_metrics', 'system_metrics', 'task_metrics']
        for table in expected_tables:
            self.assertIn(table, tables, f"Tabela {table} não encontrada")
        
        conn.close()

class TestAPIDrivers(unittest.TestCase):
    """Testes dos drivers de API"""
    
    def test_driver_creation(self):
        """Testa criação de drivers"""
        try:
            from autobot.api_drivers import create_driver
            
            # Testa criação de cada driver
            drivers = ['bitrix', 'ollama', 'webscraping']
            for driver_type in drivers:
                driver = create_driver(driver_type)
                self.assertIsNotNone(driver, f"Driver {driver_type} não criado")
                
        except ImportError:
            self.skipTest("Módulo de drivers não disponível")
    
    def test_driver_testing(self):
        """Testa função de teste dos drivers"""
        try:
            from autobot.api_drivers import test_all_drivers
            
            results = test_all_drivers()
            self.assertIsInstance(results, dict, "Resultado deve ser um dicionário")
            
            expected_drivers = ['bitrix', 'ollama', 'webscraping']
            for driver in expected_drivers:
                self.assertIn(driver, results, f"Driver {driver} não testado")
                
        except ImportError:
            self.skipTest("Módulo de drivers não disponível")

class TestNavigationFlows(unittest.TestCase):
    """Testes dos fluxos de navegação"""
    
    def test_flow_creation(self):
        """Testa criação de fluxos básicos"""
        try:
            from autobot.navigation_flows import BaseFlow, create_flow
            
            # Testa fluxo básico
            flow = BaseFlow("test_flow")
            flow.add_step("wait", "1")
            
            self.assertEqual(flow.name, "test_flow")
            self.assertEqual(len(flow.steps), 1)
            
        except ImportError:
            self.skipTest("Módulo de navegação não disponível")
    
    def test_flow_manager(self):
        """Testa gerenciador de fluxos"""
        try:
            from autobot.navigation_flows import FlowManager, BaseFlow
            
            manager = FlowManager()
            flow = BaseFlow("test")
            flow.add_step("wait", "0.1")  # Passo rápido para teste
            
            manager.add_flow(flow)
            self.assertEqual(len(manager.flows), 1)
            
            summary = manager.get_summary()
            self.assertIn("message", summary)
            
        except ImportError:
            self.skipTest("Módulo de navegação não disponível")

class TestAISystem(unittest.TestCase):
    """Testes do sistema de IA"""
    
    def test_ai_initialization(self):
        """Testa inicialização do sistema de IA"""
        try:
            from IA import AutobotAI, get_ai_status
            
            ai = AutobotAI()
            self.assertIsNotNone(ai, "Sistema de IA não inicializado")
            
            status = get_ai_status()
            self.assertIn("capabilities", status, "Status do IA incompleto")
            
        except ImportError:
            self.skipTest("Módulo de IA não disponível")
    
    def test_data_analysis(self):
        """Testa análise de dados"""
        try:
            from IA import AutobotAI
            
            ai = AutobotAI()
            test_data = [
                {"name": "João", "age": 30, "email": "joao@test.com"},
                {"name": "Maria", "age": 25, "email": "maria@test.com"}
            ]
            
            result = ai.analyze_data(test_data)
            self.assertEqual(result["status"], "success")
            self.assertIn("analysis", result)
            
        except ImportError:
            self.skipTest("Módulo de IA não disponível")

class TestWebInterface(unittest.TestCase):
    """Testes da interface web"""
    
    def test_web_files_exist(self):
        """Testa se arquivos da web existem"""
        web_files = [
            "web/package.json",
            "web/vite.config.js", 
            "web/index.html",
            "web/src/main.jsx",
            "web/src/App.jsx",
            "web/src/style.css"
        ]
        
        for file_path in web_files:
            path = Path(file_path)
            self.assertTrue(path.exists(), f"Arquivo {file_path} não encontrado")
    
    def test_css_optimization(self):
        """Testa se CSS foi otimizado"""
        css_path = Path("web/src/style.css")
        if css_path.exists():
            with open(css_path, 'r') as f:
                content = f.read()
            
            # Verifica se contém variáveis CSS otimizadas
            self.assertIn(":root", content, "Variáveis CSS não encontradas")
            self.assertIn("--primary-color", content, "Variáveis de cor não definidas")
            
            # Verifica se não há duplicação excessiva
            lines = content.split('\n')
            unique_lines = set(line.strip() for line in lines if line.strip())
            duplication_ratio = len(lines) / len(unique_lines) if unique_lines else 1
            
            self.assertLess(duplication_ratio, 2.0, "CSS tem muita duplicação")

def run_comprehensive_test():
    """Executa teste abrangente do sistema"""
    print("🧪 AUTOBOT - Testes de Integração")
    print("=" * 40)
    
    # Cria suite de testes
    test_suite = unittest.TestSuite()
    
    # Adiciona todas as classes de teste
    test_classes = [
        TestAutobotCore,
        TestAPIDrivers, 
        TestNavigationFlows,
        TestAISystem,
        TestWebInterface
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Resumo dos resultados
    print("\n" + "=" * 40)
    print(f"📊 Resumo dos Testes:")
    print(f"  ✅ Testes executados: {result.testsRun}")
    print(f"  ❌ Falhas: {len(result.failures)}")
    print(f"  ⚠️ Erros: {len(result.errors)}")
    print(f"  🎯 Taxa de sucesso: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Falhas encontradas:")
        for test, error in result.failures:
            print(f"  - {test}: {error.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print(f"\n⚠️ Erros encontrados:")
        for test, error in result.errors:
            print(f"  - {test}: {error.split('\n')[-2]}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)