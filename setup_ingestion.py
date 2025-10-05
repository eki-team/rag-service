"""
Setup script for Scientific Document Ingestion System
Installs dependencies and configures MongoDB
"""

import subprocess
import sys
import os


def check_python_version():
    """Check Python version is >= 3.9"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")


def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)


def install_spacy_model(skip_spacy=False):
    """Install spaCy English model (optional)"""
    if skip_spacy:
        print("\n⚠️  Skipping spaCy model (will use SimpleSynthesizer)")
        return
    
    print("\n🔤 Installing spaCy English model...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("✅ spaCy model installed")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install spaCy model (will use SimpleSynthesizer)")


def check_mongodb():
    """Check MongoDB connection"""
    print("\n🗄️  Checking MongoDB connection...")
    
    try:
        from pymongo import MongoClient
        
        # Get MONGO_URI from env or default
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise exception if cannot connect
        
        print(f"✅ MongoDB connected: {mongo_uri}")
        client.close()
        
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("   Make sure MongoDB is running or set MONGO_URI in .env")


def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists(".env"):
        print("\n✅ .env file already exists")
        return
    
    print("\n📝 Creating .env file...")
    
    env_template = """# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/

# Database name
DATABASE_NAME=rag_service

# OpenAI API Key (if using embeddings)
OPENAI_API_KEY=your-api-key-here

# PostgreSQL (if used elsewhere)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag_service
DB_HOST=localhost
DB_PORT=5432

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
    
    with open(".env", "w") as f:
        f.write(env_template)
    
    print("✅ .env file created (please update with your credentials)")


def create_indexes():
    """Create MongoDB indexes"""
    print("\n🔍 Creating MongoDB indexes...")
    
    try:
        from app.services.ingestion import get_mongo_config
        
        config = get_mongo_config()
        config.connect()  # This creates indexes automatically
        
        print("✅ MongoDB indexes created")
        
    except Exception as e:
        print(f"⚠️  Failed to create indexes: {e}")


def run_example():
    """Ask if user wants to run example"""
    print("\n" + "=" * 60)
    response = input("Run example ingestion? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n🚀 Running example...")
        try:
            subprocess.check_call([sys.executable, "example_ingestion.py"])
        except subprocess.CalledProcessError:
            print("❌ Example failed")
    else:
        print("   To run manually: python example_ingestion.py")


def main():
    """Main setup routine"""
    print("=" * 60)
    print("Scientific Document Ingestion System - Setup")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Ask about spaCy
    print("\n" + "=" * 60)
    spacy_response = input("Install spaCy model for advanced synthesis? (y/n): ").strip().lower()
    install_spacy_model(skip_spacy=(spacy_response != 'y'))
    
    # Create .env file
    create_env_file()
    
    # Check MongoDB
    check_mongodb()
    
    # Create indexes
    create_indexes()
    
    # Run example
    run_example()
    
    # Done
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update .env with your credentials")
    print("2. Ensure MongoDB is running")
    print("3. Use IngestionPipeline to ingest documents")
    print("\nDocumentation: INGESTION_SYSTEM.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
