"""
Directory structure migration utilities for Turnkey Coach tools.

Migrates from:
  ~/TurnkeyClients/{client_id}/
  ~/TurnkeyClients/coaching_context/
  ./exerciselist.json
  ./.tokencache

To:
  ~/Turnkey/clients/{client_id}/
  ~/Turnkey/shared/coaching_context/
  ~/Turnkey/shared/exerciselist.json
  ~/Turnkey/shared/.tokencache
"""

import os
import shutil
import json
from pathlib import Path
from rich.console import Console

console = Console()

# Old and new directory constants
OLD_BASE_DIR = os.path.expanduser("~/TurnkeyClients")
NEW_BASE_DIR = os.path.expanduser("~/Turnkey")
OLD_APP_DIR = os.path.dirname(__file__)  # Current script directory

def get_new_paths():
    """Get the new directory structure paths."""
    return {
        'base': NEW_BASE_DIR,
        'clients': os.path.join(NEW_BASE_DIR, 'clients'),
        'shared': os.path.join(NEW_BASE_DIR, 'shared'),
        'coaching_context': os.path.join(NEW_BASE_DIR, 'shared', 'coaching_context'),
        'cache': os.path.join(NEW_BASE_DIR, 'cache')
    }


def ensure_new_structure_exists():
    """Ensure the NEW_BASE_DIR structure exists even when no migration is needed."""
    paths = get_new_paths()
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

def needs_migration():
    """Check if migration is needed."""
    # If new structure exists, assume migration is done
    if os.path.exists(NEW_BASE_DIR):
        return False
    
    # If old structure exists, migration is needed
    return os.path.exists(OLD_BASE_DIR)

def create_new_directory_structure():
    """Create the new directory structure."""
    paths = get_new_paths()
    
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
        console.print(f"[green]Created directory: {path}[/green]")

def migrate_client_directories():
    """Migrate client directories from old to new structure."""
    if not os.path.exists(OLD_BASE_DIR):
        return
    
    paths = get_new_paths()
    migrated_count = 0
    
    for item in os.listdir(OLD_BASE_DIR):
        old_path = os.path.join(OLD_BASE_DIR, item)
        
        # Skip non-directories and the coaching_context directory (handled separately)
        if not os.path.isdir(old_path) or item == 'coaching_context':
            continue
            
        # Check if it's a client directory (numeric ID)
        try:
            client_id = int(item)
            new_client_dir = os.path.join(paths['clients'], item)
            
            console.print(f"[blue]Migrating client {client_id} from {old_path} to {new_client_dir}[/blue]")
            shutil.move(old_path, new_client_dir)
            migrated_count += 1
            
        except ValueError:
            console.print(f"[yellow]Skipping non-client directory: {item}[/yellow]")
        except (OSError, shutil.Error) as e:
            console.print(f"[red]Error migrating client {item}: {e}[/red]")
    
    console.print(f"[green]Migrated {migrated_count} client directories[/green]")

def migrate_coaching_context():
    """Migrate the coaching_context directory."""
    old_context_dir = os.path.join(OLD_BASE_DIR, 'coaching_context')
    new_context_dir = get_new_paths()['coaching_context']
    
    if os.path.exists(old_context_dir):
        console.print(f"[blue]Migrating coaching context from {old_context_dir} to {new_context_dir}[/blue]")
        
        try:
            # Move all files from old to new coaching_context
            for item in os.listdir(old_context_dir):
                old_file = os.path.join(old_context_dir, item)
                new_file = os.path.join(new_context_dir, item)
                shutil.move(old_file, new_file)
            
            # Remove empty old directory
            os.rmdir(old_context_dir)
            console.print("[green]Coaching context migrated[/green]")
        except (OSError, shutil.Error) as e:
            console.print(f"[yellow]Warning: Could not fully migrate coaching context: {e}[/yellow]")

def migrate_shared_files():
    """Migrate shared files from app directory to shared directory."""
    paths = get_new_paths()
    shared_dir = paths['shared']
    
    # Files to migrate from app directory
    files_to_migrate = [
        ('exerciselist.json', 'exerciselist.json'),
        ('.tokencache', '.tokencache')
    ]
    
    for old_filename, new_filename in files_to_migrate:
        old_path = os.path.join(OLD_APP_DIR, old_filename)
        new_path = os.path.join(shared_dir, new_filename)
        
        if os.path.exists(old_path):
            console.print(f"[blue]Migrating {old_filename} to shared directory[/blue]")
            shutil.move(old_path, new_path)

def cleanup_old_structure():
    """Remove the old directory structure if it's empty."""
    if os.path.exists(OLD_BASE_DIR):
        try:
            # Only remove if directory is empty
            os.rmdir(OLD_BASE_DIR)
            console.print(f"[green]Removed old directory: {OLD_BASE_DIR}[/green]")
        except OSError:
            console.print(f"[yellow]Old directory {OLD_BASE_DIR} not empty, leaving it alone[/yellow]")

def perform_migration():
    """Perform the complete migration process."""
    if not needs_migration():
        console.print("[green]Migration not needed - new structure already exists[/green]")
        return True
    
    try:
        console.print("[bold blue]Starting directory migration...[/bold blue]")
        
        # Create new structure
        create_new_directory_structure()
        
        # Migrate data
        migrate_client_directories()
        migrate_coaching_context()
        migrate_shared_files()
        
        # Cleanup
        cleanup_old_structure()
        
        console.print("[bold green]Migration completed successfully![/bold green]")
        return True
        
    except Exception as e:
        console.print(f"[bold red]Migration failed: {e}[/bold red]")
        return False

def get_client_dir(client_id):
    """Get the client directory path, handling migration if needed."""
    if needs_migration():
        perform_migration()
    else:
        # First run with no existing directories: create them now
        ensure_new_structure_exists()
    
    paths = get_new_paths()
    client_dir = os.path.join(paths['clients'], str(client_id))
    os.makedirs(client_dir, exist_ok=True)
    return client_dir

def get_shared_dir():
    """Get the shared directory path, handling migration if needed."""
    if needs_migration():
        perform_migration()
    else:
        # First run with no existing directories: create them now
        ensure_new_structure_exists()
    
    shared_dir = get_new_paths()['shared']
    os.makedirs(shared_dir, exist_ok=True)
    return shared_dir

def get_coaching_context_dir():
    """Get the coaching context directory path, handling migration if needed."""
    if needs_migration():
        perform_migration()
    else:
        # First run with no existing directories: create them now
        ensure_new_structure_exists()
    
    context_dir = get_new_paths()['coaching_context']
    os.makedirs(context_dir, exist_ok=True)
    return context_dir

if __name__ == "__main__":
    # Run migration if called directly
    perform_migration()