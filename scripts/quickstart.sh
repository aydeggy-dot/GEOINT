#!/bin/bash

# Quick start script for Nigeria Security System (Unix/Linux/macOS)

set -e

echo "======================================================================="
echo "  Nigeria Security Early Warning System - Quick Start"
echo "======================================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed"
    echo "Please install Docker: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose is not installed"
    exit 1
fi

echo "✓ Docker is installed"

# Navigate to project root
cd "$(dirname "$0")/.."

echo ""
echo "======================================================================="
echo "  Starting Docker Services"
echo "======================================================================="
echo ""

# Start services
docker-compose up -d

echo "✓ Services started"
echo ""
echo "Waiting for backend to be ready..."

# Wait for backend
max_attempts=30
for i in $(seq 1 $max_attempts); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Backend is ready"
        break
    fi
    echo -ne "  Attempt $i/$max_attempts...\r"
    sleep 2
done

echo ""
echo ""
echo "======================================================================="
echo "  Seeding Database"
echo "======================================================================="
echo ""

read -p "Do you want to populate the database with sample data? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 scripts/seed_database.py
    echo "✓ Database seeded"
else
    echo "Skipping database seeding"
fi

echo ""
echo "======================================================================="
echo "  Available Endpoints"
echo "======================================================================="
echo ""
echo "  API Documentation     → http://localhost:8000/docs"
echo "  Health Check          → http://localhost:8000/health"
echo "  List Incidents        → http://localhost:8000/api/v1/incidents/"
echo "  Get Statistics        → http://localhost:8000/api/v1/incidents/stats/summary"
echo "  GeoJSON Export        → http://localhost:8000/api/v1/incidents/geojson/all"

echo ""
echo "======================================================================="
echo "  System is Ready!"
echo "======================================================================="
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f backend"
echo ""
