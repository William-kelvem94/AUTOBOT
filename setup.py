#!/usr/bin/env python3
"""
AUTOBOT Setup Script
Initialize the AUTOBOT system and download required models
"""

import os
import asyncio
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "data/models",
        "data/knowledge", 
        "data/automations",
        "data/logs",
        "data/config",
        "data/qdrant",
        "data/postgres", 
        "data/redis",
        "data/screenshots"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def check_docker():
    """Check if Docker is available"""
    return run_command("docker --version", "Checking Docker")

def check_docker_compose():
    """Check if Docker Compose is available"""
    return run_command("docker-compose --version", "Checking Docker Compose")

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            run_command("cp .env.example .env", "Creating .env file")
            print("📝 Please edit .env file with your configurations")
        else:
            print("❌ .env.example not found")
    else:
        print("✅ .env file already exists")

def pull_docker_images():
    """Pull required Docker images"""
    images = [
        "ollama/ollama:latest",
        "qdrant/qdrant:latest", 
        "postgres:15",
        "redis:alpine",
        "nginx:alpine"
    ]
    
    for image in images:
        run_command(f"docker pull {image}", f"Pulling {image}")

def download_ai_models():
    """Download AI models using Ollama"""
    print("🤖 Starting Ollama and downloading AI models...")
    
    # Start Ollama service
    if run_command("docker-compose up -d ollama", "Starting Ollama service"):
        # Wait a bit for service to start
        print("⏳ Waiting for Ollama to start...")
        import time
        time.sleep(10)
        
        # Download models
        models = ["llama3", "mistral", "codellama"]
        for model in models:
            run_command(
                f"docker exec autobot-ollama ollama pull {model}",
                f"Downloading {model} model"
            )

def setup_database():
    """Initialize the database"""
    print("🗄️ Setting up database...")
    run_command("docker-compose up -d postgres", "Starting PostgreSQL")

def build_and_start():
    """Build and start all services"""
    print("🚀 Building and starting AUTOBOT...")
    return run_command("docker-compose up -d --build", "Building and starting all services")

def main():
    """Main setup function"""
    print("🤖 AUTOBOT Setup Script")
    print("=" * 50)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    if not check_docker():
        print("❌ Docker is required but not found")
        sys.exit(1)
    
    if not check_docker_compose():
        print("❌ Docker Compose is required but not found")
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Create .env file
    print("\n⚙️ Setting up configuration...")
    create_env_file()
    
    # Pull Docker images
    print("\n📦 Pulling Docker images...")
    pull_docker_images()
    
    # Build and start services
    print("\n🚀 Starting services...")
    if build_and_start():
        print("\n✅ AUTOBOT services started successfully!")
        
        # Download AI models
        download_ai_models()
        
        print("\n🎉 Setup completed!")
        print("\n📝 Next steps:")
        print("1. Edit .env file with your configurations")
        print("2. Access the web interface at http://localhost")
        print("3. Check API documentation at http://localhost:8000/docs")
        print("4. Check service status with: docker-compose ps")
        
    else:
        print("\n❌ Setup failed. Check the logs with: docker-compose logs")
        sys.exit(1)

if __name__ == "__main__":
    main()