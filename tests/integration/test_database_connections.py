#!/usr/bin/env python3
"""
Test PostgreSQL and Redis connections
Verifies database connectivity and basic operations
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
import psycopg2
import redis
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_postgresql_connection():
    """Test PostgreSQL connection and basic operations"""
    print("\n🐘 Testing PostgreSQL Connection...")
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Expected format: postgresql://user:password@host:port/database")
        return False
    
    # Parse and display connection info (hide password)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        print(f"📍 Connecting to PostgreSQL:")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        print(f"   User: {parsed.username}")
    except:
        pass
    
    try:
        # Test with psycopg2
        print("\n1️⃣ Testing with psycopg2...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL!")
        print(f"   Version: {version}")
        
        # Check current database
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"   Current database: {db_name}")
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📋 Found {len(tables)} tables:")
            for table in tables[:10]:  # Show first 10
                print(f"   - {table[0]}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more")
        else:
            print("\n⚠️ No tables found in public schema")
            print("   Database may need initialization")
        
        cursor.close()
        conn.close()
        
        # Test with SQLAlchemy
        print("\n2️⃣ Testing with SQLAlchemy...")
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ SQLAlchemy connection successful!")
            
            # Check if alembic_version exists (migrations)
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                );
            """))
            has_migrations = result.scalar()
            
            if has_migrations:
                print("✅ Database migrations table found")
                # Get current migration version
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                if version:
                    print(f"   Current migration: {version}")
            else:
                print("⚠️ No migrations table found")
                print("   Run 'alembic upgrade head' to initialize database")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if PostgreSQL is running: docker-compose ps")
        print("   2. Verify DATABASE_URL is correct")
        print("   3. Check if database exists")
        print("   4. Verify network connectivity")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redis_connection():
    """Test Redis connection and basic operations"""
    print("\n🔴 Testing Redis Connection...")
    
    # Get Redis URL from environment
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Parse and display connection info
    try:
        from urllib.parse import urlparse
        parsed = urlparse(redis_url)
        print(f"📍 Connecting to Redis:")
        print(f"   Host: {parsed.hostname or 'localhost'}")
        print(f"   Port: {parsed.port or 6379}")
        print(f"   Database: {parsed.path.lstrip('/') or '0'}")
    except:
        pass
    
    try:
        # Connect to Redis
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        print("\n1️⃣ Testing basic operations...")
        
        # PING
        pong = r.ping()
        if pong:
            print("✅ Redis connection successful! (PING -> PONG)")
        
        # Server info
        info = r.info()
        print(f"   Redis version: {info.get('redis_version', 'unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 'unknown')}")
        
        # Test SET/GET
        print("\n2️⃣ Testing SET/GET operations...")
        test_key = "evergreen:test:connection"
        test_value = "Hello from integration test!"
        
        r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved = r.get(test_key)
        
        if retrieved == test_value:
            print("✅ SET/GET operations working correctly")
        else:
            print("❌ SET/GET operations failed")
        
        # Test Celery queues
        print("\n3️⃣ Checking Celery queues...")
        
        # List all keys matching celery pattern
        celery_keys = r.keys("celery*")
        if celery_keys:
            print(f"   Found {len(celery_keys)} Celery-related keys")
            
            # Check specific queues
            queues = ['celery', 'video_generation', 'high_priority']
            for queue in queues:
                queue_key = f"celery:queue:{queue}"
                length = r.llen(queue_key)
                print(f"   Queue '{queue}': {length} tasks")
        else:
            print("   No Celery queues found (this is normal if workers haven't started)")
        
        # Test pub/sub
        print("\n4️⃣ Testing Pub/Sub...")
        pubsub = r.pubsub()
        test_channel = "evergreen:test:channel"
        
        pubsub.subscribe(test_channel)
        r.publish(test_channel, "Test message")
        
        # Get one message (subscription confirmation)
        msg = pubsub.get_message(timeout=1)
        if msg and msg['type'] == 'subscribe':
            print("✅ Pub/Sub working correctly")
        
        pubsub.unsubscribe(test_channel)
        pubsub.close()
        
        # Cleanup
        r.delete(test_key)
        
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if Redis is running: docker-compose ps")
        print("   2. Verify REDIS_URL is correct")
        print("   3. Check if Redis port (6379) is accessible")
        print("   4. Try: docker-compose restart redis")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """Test database integration scenarios"""
    print("\n🔗 Testing Database Integration...")
    
    database_url = os.getenv('DATABASE_URL')
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    if not database_url:
        print("⚠️ Skipping integration tests - DATABASE_URL not set")
        return
    
    try:
        # Test scenario: Cache database query results in Redis
        print("\n1️⃣ Testing PostgreSQL + Redis integration...")
        
        # Connect to both
        engine = create_engine(database_url)
        r = redis.from_url(redis_url, decode_responses=True)
        
        with engine.connect() as conn:
            # Check if we have any data to test with
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                LIMIT 1;
            """))
            
            table = result.scalar()
            if table:
                # Cache the result in Redis
                cache_key = f"evergreen:test:tables:{table}"
                r.setex(cache_key, 60, table)
                
                # Retrieve from cache
                cached = r.get(cache_key)
                if cached == table:
                    print("✅ Successfully cached PostgreSQL data in Redis")
                    print(f"   Cached table name: {table}")
                
                # Cleanup
                r.delete(cache_key)
            else:
                print("⚠️ No tables found to test caching")
        
        print("\n2️⃣ Testing connection pooling...")
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        
        # Test multiple concurrent connections
        success_count = 0
        for i in range(5):
            try:
                session = Session()
                result = session.execute(text("SELECT 1"))
                session.close()
                success_count += 1
            except:
                pass
        
        print(f"✅ Connection pooling test: {success_count}/5 connections successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_docker_services():
    """Check if services are running in Docker"""
    print("\n🐳 Checking Docker Services...")
    
    try:
        import subprocess
        
        # Run docker-compose ps
        result = subprocess.run(
            ['docker-compose', 'ps'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        
        if result.returncode == 0:
            print("📋 Docker services status:")
            print(result.stdout)
            
            # Check for specific services
            output = result.stdout.lower()
            services = {
                'postgres': 'PostgreSQL database',
                'redis': 'Redis cache',
                'api': 'FastAPI application',
                'worker': 'Celery worker',
                'flower': 'Celery monitoring'
            }
            
            running_count = 0
            for service, description in services.items():
                if service in output and 'up' in output:
                    print(f"✅ {description} is running")
                    running_count += 1
                else:
                    print(f"❌ {description} is not running")
            
            if running_count == len(services):
                print("\n✅ All services are running!")
            else:
                print(f"\n⚠️ Only {running_count}/{len(services)} services are running")
                print("   Run: docker-compose up -d")
        else:
            print("❌ Could not check Docker services")
            print("   Make sure Docker is running and you're in the project directory")
            
    except FileNotFoundError:
        print("❌ docker-compose command not found")
        print("   Please install Docker Compose")
    except Exception as e:
        print(f"❌ Error checking Docker services: {e}")

def main():
    """Run all database connection tests"""
    print("🚀 Database Connection Test Suite")
    print("=" * 50)
    
    # Test 1: Check Docker services
    test_docker_services()
    
    # Test 2: PostgreSQL connection
    pg_ok = test_postgresql_connection()
    
    # Test 3: Redis connection
    redis_ok = test_redis_connection()
    
    # Test 4: Integration tests (only if both are working)
    if pg_ok and redis_ok:
        test_database_integration()
    else:
        print("\n⚠️ Skipping integration tests due to connection failures")
    
    # Summary
    print("\n📊 Summary:")
    print(f"   PostgreSQL: {'✅ Connected' if pg_ok else '❌ Failed'}")
    print(f"   Redis: {'✅ Connected' if redis_ok else '❌ Failed'}")
    
    if not (pg_ok and redis_ok):
        print("\n💡 Next steps:")
        if not pg_ok:
            print("   1. Start PostgreSQL: docker-compose up -d postgres")
            print("   2. Check logs: docker-compose logs postgres")
        if not redis_ok:
            print("   1. Start Redis: docker-compose up -d redis")
            print("   2. Check logs: docker-compose logs redis")
    
    print("\n✅ Database Connection Tests Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()