
# Adicione este código ao seu autobot/api.py existente:

try:
    from IA.treinamento.integration_api import ai_local_bp
    app.register_blueprint(ai_local_bp)
    print("✅ Sistema de IA local integrado à API")
except ImportError as e:
    print(f"⚠️ Falha ao carregar IA local: {e}")
