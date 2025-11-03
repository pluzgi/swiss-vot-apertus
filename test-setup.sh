#!/bin/bash
# Test script for Step 1 infrastructure setup

echo "🧪 Testing Swiss Voting Assistant Setup (Step 1)"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your API keys!"
    echo ""
fi

# Check Docker
echo "📦 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi
echo "✅ Docker version: $(docker --version)"
echo ""

# Check Docker Compose
echo "📦 Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found."
    exit 1
fi
echo "✅ Docker Compose version: $(docker-compose --version)"
echo ""

# Validate docker-compose.yml
echo "🔍 Validating docker-compose.yml..."
if docker-compose config --quiet; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    exit 1
fi
echo ""

# Check if containers are running
echo "🐳 Checking container status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Containers are running:"
    docker-compose ps
else
    echo "⚠️  No containers running. Start with: docker-compose up -d"
fi
echo ""

# Test backend health endpoint (if running)
echo "🏥 Testing backend health endpoint..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy:"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "⚠️  Backend not responding (containers may not be started yet)"
fi
echo ""

echo "=================================================="
echo "✅ Step 1 Setup Verification Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Swisscom Apertus API key"
echo "2. Start services: docker-compose up -d"
echo "3. Access OpenWebUI at http://localhost:3000"
echo "4. View API docs at http://localhost:8000/docs"
echo ""
