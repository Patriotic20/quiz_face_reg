import subprocess
import sys

def run_migrate(migration_dir=None):
    """Run Alembic upgrade to head revision.
    
    Args:
        migration_dir: Optional path to directory containing alembic.ini
                      If None, uses current working directory
    """
    code = "alembic upgrade head"
    
    try:
        result = subprocess.run(code, shell=True, capture_output=True, text=True, cwd=migration_dir)
        
        if result.returncode == 0:
            print("Migration successful!")
            print(result.stdout)
            return True
        else:
            print("Migration failed!")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error running migration: {e}")
        return False


