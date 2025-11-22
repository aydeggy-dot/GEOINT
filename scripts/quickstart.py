"""
Quick start script to set up and run the Nigeria Security System
"""
import os
import sys
import subprocess
import time


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_docker():
    """Check if Docker is installed and running"""
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def start_services():
    """Start Docker Compose services"""
    print_header("Starting Docker Services")

    print("Starting PostgreSQL, Redis, and Backend...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("✓ Services started successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start services: {e}")
        return False


def wait_for_services():
    """Wait for services to be healthy"""
    print("\nWaiting for services to be ready...")

    max_attempts = 30
    for i in range(max_attempts):
        try:
            # Check if backend is responding
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✓ Backend is ready")
                return True
        except:
            pass

        print(f"  Attempt {i+1}/{max_attempts}...", end="\r")
        time.sleep(2)

    print("✗ Services did not start in time")
    return False


def seed_database():
    """Run database seeding script"""
    print_header("Seeding Database")

    response = input("Do you want to populate the database with sample data? (y/n): ")

    if response.lower() == 'y':
        print("\nSeeding database with sample incidents...")
        try:
            subprocess.run([
                sys.executable,
                "scripts/seed_database.py"
            ], check=True)
            print("✓ Database seeded successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to seed database: {e}")
            return False
    else:
        print("Skipping database seeding")
        return True


def show_endpoints():
    """Display available endpoints"""
    print_header("Available Endpoints")

    endpoints = [
        ("API Documentation", "http://localhost:8000/docs"),
        ("Health Check", "http://localhost:8000/health"),
        ("List Incidents", "http://localhost:8000/api/v1/incidents/"),
        ("Get Statistics", "http://localhost:8000/api/v1/incidents/stats/summary"),
        ("GeoJSON Export", "http://localhost:8000/api/v1/incidents/geojson/all"),
    ]

    for name, url in endpoints:
        print(f"  {name:20} → {url}")


def show_sample_request():
    """Show sample API request"""
    print_header("Sample API Request")

    sample = '''
curl -X POST "http://localhost:8000/api/v1/incidents/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "incident_type": "armed_attack",
    "severity": "high",
    "location": {
      "type": "Point",
      "coordinates": [7.4905, 9.0765]
    },
    "description": "Armed men attacked village at dawn, multiple casualties reported",
    "timestamp": "2025-11-20T06:30:00Z",
    "casualties": {
      "killed": 5,
      "injured": 12,
      "missing": 0
    },
    "reporter_phone": "+234XXXXXXXXXX"
  }'
'''

    print(sample)


def main():
    """Main quick start function"""
    print_header("Nigeria Security Early Warning System - Quick Start")

    # Check Docker
    if not check_docker():
        print("✗ Docker or Docker Compose is not installed or not running")
        print("\nPlease install Docker Desktop and ensure it's running:")
        print("  https://www.docker.com/products/docker-desktop")
        return

    print("✓ Docker is installed and running")

    # Start services
    if not start_services():
        return

    # Wait for services
    if not wait_for_services():
        print("\nYou can check logs with: docker-compose logs backend")
        return

    # Seed database
    seed_database()

    # Show info
    show_endpoints()
    show_sample_request()

    print_header("System is Ready!")
    print("Press Ctrl+C to stop the services")
    print("\nTo stop services manually, run: docker-compose down")

    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping services...")
        subprocess.run(["docker-compose", "down"])
        print("✓ Services stopped")


if __name__ == "__main__":
    main()
