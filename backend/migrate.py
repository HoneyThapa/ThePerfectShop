#!/usr/bin/env python3
"""
Database migration management script for ExpiryShield backend.

This script provides convenient commands for managing database migrations
using Alembic. It handles common migration tasks and provides helpful
error messages.

Usage:
    python migrate.py upgrade    # Apply all pending migrations
    python migrate.py downgrade  # Downgrade one migration
    python migrate.py current    # Show current migration
    python migrate.py history    # Show migration history
    python migrate.py create "description"  # Create new migration
"""

import sys
import subprocess
import os
from pathlib import Path

def run_alembic_command(command_args):
    """Run an Alembic command and handle errors."""
    try:
        result = subprocess.run(
            ["alembic"] + command_args,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running alembic {' '.join(command_args)}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("Error: Alembic not found. Please install it with: pip install alembic")
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "upgrade":
        print("Applying all pending migrations...")
        success = run_alembic_command(["upgrade", "head"])
        if success:
            print("✅ Database upgraded successfully!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)
    
    elif command == "downgrade":
        print("Downgrading one migration...")
        success = run_alembic_command(["downgrade", "-1"])
        if success:
            print("✅ Database downgraded successfully!")
        else:
            print("❌ Downgrade failed!")
            sys.exit(1)
    
    elif command == "current":
        print("Current migration:")
        run_alembic_command(["current"])
    
    elif command == "history":
        print("Migration history:")
        run_alembic_command(["history"])
    
    elif command == "create":
        if len(sys.argv) < 3:
            print("Usage: python migrate.py create 'migration description'")
            sys.exit(1)
        
        description = sys.argv[2]
        print(f"Creating new migration: {description}")
        success = run_alembic_command(["revision", "--autogenerate", "-m", description])
        if success:
            print("✅ Migration created successfully!")
        else:
            print("❌ Migration creation failed!")
            sys.exit(1)
    
    elif command == "create-empty":
        if len(sys.argv) < 3:
            print("Usage: python migrate.py create-empty 'migration description'")
            sys.exit(1)
        
        description = sys.argv[2]
        print(f"Creating empty migration: {description}")
        success = run_alembic_command(["revision", "-m", description])
        if success:
            print("✅ Empty migration created successfully!")
        else:
            print("❌ Migration creation failed!")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()