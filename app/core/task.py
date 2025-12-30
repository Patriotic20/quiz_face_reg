import subprocess
import sys
from core.logging import logging

logger = logging.getLogger(__name__)

def run_migrate(migration_dir=None):
    """Run Alembic upgrade to head revision.
    
    Args:
        migration_dir: Optional path to directory containing alembic.ini
                      If None, uses current working directory
    """
    code = "alembic upgrade head"
    
    try:
        result = subprocess.run(
            code, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=migration_dir or "/app"
        )
        
        if result.returncode == 0:
            logger.info("Migration successful!")
            logger.info(result.stdout)
            return True
        else:
            logger.error("Migration failed!")
            logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        return False