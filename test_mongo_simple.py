"""
Test Simple de Conexión MongoDB (Estilo ETL-Service)
Prueba rápida sin dependencias de FastAPI/settings
"""
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import sys

# ============================================
# CONFIGURACIÓN DIRECTA (edita aquí si necesitas)
# ============================================

# Opción 1: SRV (recomendada, más simple)
MONGO_URI = "mongodb+srv://admin:admin@nasakb.yvrx6cs.mongodb.net/nasakb?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"

# Opción 2: Direct (si la opción 1 falla por DNS)
# MONGO_URI = "mongodb://admin:admin@nasakb.yvrx6cs-shard-00-00.mongodb.net:27017,nasakb.yvrx6cs-shard-00-01.mongodb.net:27017,nasakb.yvrx6cs-shard-00-02.mongodb.net:27017/nasakb?retryWrites=true&w=majority&authSource=admin&tls=true&tlsAllowInvalidCertificates=true"

DB_NAME = "nasakb"
COLLECTION_NAME = "chunks"

# ============================================
# PRUEBA DE CONEXIÓN (Estilo ETL)
# ============================================

def test_connection():
    """Prueba de conexión simple y directa"""
    print("=" * 60)
    print("🧪 TEST DE CONEXIÓN MONGODB (Estilo ETL-Service)")
    print("=" * 60)
    
    print(f"\n📋 Configuración:")
    print(f"   URI: {MONGO_URI[:50]}...")
    print(f"   DB: {DB_NAME}")
    print(f"   Collection: {COLLECTION_NAME}")
    
    client = None
    
    try:
        print("\n🔌 Conectando a MongoDB...")
        
        # Configuración optimizada (como ETL-service)
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=10000,  # 10 segundos
            connectTimeoutMS=10000,
            socketTimeoutMS=45000,
            maxPoolSize=50,
            minPoolSize=10,
            retryWrites=True,
            retryReads=True,
        )
        
        # Test 1: Ping
        print("   ⏳ Haciendo ping al servidor...")
        client.admin.command('ping')
        print("   ✅ Ping exitoso!")
        
        # Test 2: Server Info
        print("\n📊 Información del servidor:")
        server_info = client.server_info()
        print(f"   Versión: {server_info.get('version', 'N/A')}")
        print(f"   Host conectado: {client.address[0]}:{client.address[1]}")
        
        # Test 3: Database
        db = client[DB_NAME]
        print(f"\n📚 Base de datos '{DB_NAME}':")
        collections = db.list_collection_names()
        print(f"   Colecciones encontradas: {len(collections)}")
        print(f"   Colecciones: {', '.join(collections[:5])}")
        
        # Test 4: Collection
        if COLLECTION_NAME in collections:
            collection = db[COLLECTION_NAME]
            count = collection.count_documents({})
            print(f"\n📦 Colección '{COLLECTION_NAME}':")
            print(f"   Documentos: {count}")
            
            # Obtener índices
            indexes = list(collection.list_indexes())
            print(f"   Índices: {len(indexes)}")
            for idx in indexes:
                print(f"      - {idx.get('name', 'N/A')}")
        else:
            print(f"\n⚠️  Colección '{COLLECTION_NAME}' no existe")
        
        print("\n" + "=" * 60)
        print("✅ PRUEBA EXITOSA - MongoDB está funcionando correctamente")
        print("=" * 60)
        return True
        
    except ServerSelectionTimeoutError as e:
        print("\n" + "=" * 60)
        print("❌ ERROR: Timeout al conectar al servidor")
        print("=" * 60)
        print(f"\nDetalles: {e}")
        print("\n💡 Posibles causas:")
        print("   1. Firewall bloqueando la conexión")
        print("   2. Problema de DNS (si usas mongodb+srv://)")
        print("   3. IP no whitelistada en MongoDB Atlas")
        print("   4. Credenciales incorrectas")
        print("\n💡 Soluciones:")
        print("   1. Si usas mongodb+srv://, prueba con mongodb:// directo")
        print("   2. Desactiva temporalmente el firewall")
        print("   3. Verifica que tu IP esté en 0.0.0.0/0 en Atlas")
        print("   4. Usa una VPN o hotspot móvil")
        return False
        
    except ConnectionFailure as e:
        print("\n" + "=" * 60)
        print("❌ ERROR: Fallo en la conexión")
        print("=" * 60)
        print(f"\nDetalles: {e}")
        print("\n💡 Verifica:")
        print("   1. Usuario y contraseña correctos")
        print("   2. Formato del URI correcto")
        print("   3. Base de datos existe en MongoDB")
        return False
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR INESPERADO")
        print("=" * 60)
        print(f"\nTipo: {type(e).__name__}")
        print(f"Detalles: {e}")
        return False
        
    finally:
        if client:
            client.close()
            print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
