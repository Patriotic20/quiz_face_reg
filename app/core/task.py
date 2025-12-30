import subprocess
import os
from pathlib import Path
from core.logging import logging

logger = logging.getLogger(__name__)

def find_alembic_ini():
    """Find alembic.ini file by searching from app root upwards."""
    current_dir = Path.cwd()
    
    # Search in current directory and parent directories
    for directory in [current_dir] + list(current_dir.parents):
        alembic_ini = directory / "alembic.ini"
        if alembic_ini.exists():
            logger.info(f"Found alembic.ini at: {alembic_ini}")
            return str(directory)
    
    logger.warning("alembic.ini not found in any parent directory")
    return None

def run_migrate():
    """Run Alembic upgrade to head revision.
    
    Automatically finds alembic.ini and runs migration from that directory.
    """
    # Find the directory containing alembic.ini
    migration_dir = find_alembic_ini()
    
    if not migration_dir:
        logger.error("Cannot find alembic.ini - migration aborted")
        return False
    
    code = "alembic upgrade head"
    
    try:
        logger.info(f"Running migrations from: {migration_dir}")
        result = subprocess.run(
            code, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=migration_dir
        )
        
        if result.returncode == 0:
            logger.info("Migration successful!")
            if result.stdout:
                logger.info(result.stdout)
            return True
        else:
            logger.error("Migration failed!")
            if result.stderr:
                logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        return False