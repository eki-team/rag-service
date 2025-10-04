"""
Quick Start Script - NASA RAG Service
Checks environment and starts the service.
"""
import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env exists"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("📝 Copy .env.example to .env and fill in your credentials:")
        print("   cp .env.example .env")
        return False
    print("✅ .env file found")
    return True


def check_required_vars():
    """Check if required env vars are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = [
        "OPENAI_API_KEY",
        "COSMOS_URL",
        "COSMOS_KEY",
    ]
    
    missing = []
    for var in required:
        value = os.getenv(var)
        if not value or value.startswith("your-"):
            missing.append(var)
    
    if missing:
        print(f"⚠️ Missing or placeholder values for: {', '.join(missing)}")
        print("   Please update .env with real credentials")
        return False
    
    print("✅ Required environment variables are set")
    return True


def main():
    """Main check and start"""
    print("🚀 NASA RAG Service - Quick Start\n")
    
    # Check .env
    if not check_env_file():
        sys.exit(1)
    
    # Check required vars
    if not check_required_vars():
        print("\n⚠️ Warning: Service may not work without valid credentials")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("\n✅ All checks passed!")
    print("\n📦 Starting service...")
    print("   uvicorn app.main:app --reload --port 8000")
    print("\n📚 Docs will be available at:")
    print("   http://localhost:8000/docs")
    print("   http://localhost:8000/redoc")
    print("\n🛑 Press Ctrl+C to stop\n")
    
    # Start uvicorn
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
