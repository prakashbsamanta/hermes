import sys
import logging
from hermes_data import DataService, DataSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_registry():
    print("Initializing DataService...")
    # Use localhost DB URL for external script
    settings = DataSettings(
        database_url="postgresql://hermes:hermes_secret@localhost:5432/hermes",
        registry_enabled=True,
        # Point to the data directory (relative to where script is run, or absolute)
        # In this case, we run from project root, so 'hermes-backend/data/minute' is correct
        data_dir="hermes-backend/data/minute"
    )
    
    try:
        service = DataService(settings=settings)
        print("Syncing registry from filesystem...")
        count = service.sync_registry()
        print(f"Successfully synced {count} instruments.")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = sync_registry()
    sys.exit(0 if success else 1)
