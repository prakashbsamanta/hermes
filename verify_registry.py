import sys
from sqlalchemy import create_engine, inspect, text
from hermes_data.config import DataSettings
from hermes_data.registry.models import Base

def verify_registry():
    print("Verifying registry connection...")
    
    # Use localhost because we are running outside container
    db_url = "postgresql://hermes:hermes_secret@localhost:5432/hermes"
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("Successfully connected to database")
            
            # Check if tables exist
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"Tables found: {tables}")
            
            required_tables = {"instruments", "data_availability", "data_load_logs"}
            missing = required_tables - set(tables)
            
            if missing:
                print(f"ERROR: Missing tables: {missing}")
                # Try creating tables if missing (backend should have done this)
                print("Attempting to create missing tables...")
                Base.metadata.create_all(engine)
                print("Tables created.")
            else:
                print("All required registry tables exist.")
                
            # Check instrument count
            count = conn.execute(text("SELECT count(*) FROM instruments")).scalar()
            print(f"Instrument count in registry: {count}")
            
            # Check logs
            logs = conn.execute(text("SELECT * FROM data_load_logs ORDER BY created_at DESC LIMIT 5")).fetchall()
            print(f"Recent data load logs: {len(logs)}")
            for log in logs:
                print(f" - {log.symbol} ({log.timeframe}): {log.status} - {log.rows_loaded} rows ({log.load_time_ms}ms)")
            
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = verify_registry()
    sys.exit(0 if success else 1)
