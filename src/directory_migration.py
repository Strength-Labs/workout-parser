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
OLD_SINGLE_BASE_DIR = os.path.expanduser("~/Turnkey")  # Previous single workspace dir
OLD_APP_DIR = os.path.dirname(__file__)  # Current script directory

def get_workspace_base_dir(workspace_name=None):
    """Get the base directory for a specific workspace."""
    if workspace_name:
        return os.path.expanduser(f"~/Turnkey-{workspace_name}")
    
    # Try to get current workspace from settings
    try:
        from src.settings import get_current_workspace, get_workspace_settings
        workspace = get_current_workspace()
        if workspace and workspace.get('company_name'):
            from src.api_client import sanitize_workspace_name
            workspace_name = sanitize_workspace_name(workspace['company_name'])
            return os.path.expanduser(f"~/Turnkey-{workspace_name}")
    except ImportError:
        pass
    
    # Fallback to default
    return os.path.expanduser("~/Turnkey-default")

def get_new_paths(workspace_name=None):
    """Get the new directory structure paths for a workspace."""
    base_dir = get_workspace_base_dir(workspace_name)
    return {
        'base': base_dir,
        'clients': os.path.join(base_dir, 'clients'),
        'shared': os.path.join(base_dir, 'shared'),
        'coaching_context': os.path.join(base_dir, 'shared', 'coaching_context'),
        'cache': os.path.join(base_dir, 'cache')
    }

def needs_migration():
    """Check if migration is needed."""
    # Check for old directory structures
    has_old_clients = os.path.exists(OLD_BASE_DIR)
    has_old_single = os.path.exists(OLD_SINGLE_BASE_DIR)
    
    # If either old structure exists, migration might be needed
    return has_old_clients or has_old_single

def needs_workspace_migration():
    """Check if workspace-specific migration is needed."""
    # Check if old single workspace directory exists
    return os.path.exists(OLD_SINGLE_BASE_DIR)

def migrate_to_workspace_directory(workspace_name=None, force=False):
    """Migrate old single workspace to workspace-specific directory."""
    if not needs_workspace_migration() and not force:
        return True
        
    console.print("[yellow]🔄 Migrating to v1.5.0 workspace structure...[/yellow]")
    
    # Get target workspace directory (default to barbell-logic for existing users)
    if not workspace_name:
        workspace_name = "barbell-logic"
    target_base = get_workspace_base_dir(workspace_name)
    
    try:
        # If target already exists, we need to merge the data
        if os.path.exists(target_base):
            return merge_old_directory_to_workspace(workspace_name)
        else:
            # Simple case - just move the entire directory
            console.print(f"[blue]Moving {OLD_SINGLE_BASE_DIR} to {target_base}[/blue]")
            shutil.move(OLD_SINGLE_BASE_DIR, target_base)
            console.print(f"[green]✅ Successfully migrated to {target_base}[/green]")
            return True
            
    except (OSError, shutil.Error) as e:
        console.print(f"[red]❌ Error during workspace migration: {e}[/red]")
        return False

def merge_old_directory_to_workspace(workspace_name):
    """Merge old ~/Turnkey/ directory into existing workspace directory."""
    target_base = get_workspace_base_dir(workspace_name)
    
    console.print(f"[blue]Merging {OLD_SINGLE_BASE_DIR} into {target_base}[/blue]")
    
    if not os.path.exists(OLD_SINGLE_BASE_DIR):
        console.print("[yellow]No old directory to migrate.[/yellow]")
        return True
    
    try:
        migrated_clients = 0
        
        # Migrate client directories (the important data)
        old_clients_dir = os.path.join(OLD_SINGLE_BASE_DIR, 'clients')
        target_clients_dir = os.path.join(target_base, 'clients')
        
        if os.path.exists(old_clients_dir):
            os.makedirs(target_clients_dir, exist_ok=True)
            
            for client_id in os.listdir(old_clients_dir):
                if client_id.startswith('.'):  # Skip .DS_Store etc
                    continue
                    
                old_client_path = os.path.join(old_clients_dir, client_id)
                target_client_path = os.path.join(target_clients_dir, client_id)
                
                if not os.path.isdir(old_client_path):
                    continue
                    
                # Remove target if it exists (partial downloads, etc)
                if os.path.exists(target_client_path):
                    console.print(f"[dim]Overwriting partial data for client {client_id}[/dim]")
                    shutil.rmtree(target_client_path)
                
                # Move the client directory
                console.print(f"[green]Migrating client {client_id}...[/green]")
                shutil.move(old_client_path, target_client_path)
                migrated_clients += 1
        
        # Migrate shared data (exercise lists, etc) - but don't overwrite existing
        old_shared_dir = os.path.join(OLD_SINGLE_BASE_DIR, 'shared')
        target_shared_dir = os.path.join(target_base, 'shared')
        
        if os.path.exists(old_shared_dir):
            os.makedirs(target_shared_dir, exist_ok=True)
            
            for item in os.listdir(old_shared_dir):
                if item.startswith('.'):  # Skip .DS_Store etc
                    continue
                    
                old_item_path = os.path.join(old_shared_dir, item)
                target_item_path = os.path.join(target_shared_dir, item)
                
                # Only move if target doesn't exist (keep newer shared data)
                if not os.path.exists(target_item_path):
                    console.print(f"[dim]Moving shared/{item}[/dim]")
                    shutil.move(old_item_path, target_item_path)
                else:
                    console.print(f"[dim]Keeping existing shared/{item}[/dim]")
        
        # Clean up old directory
        cleanup_old_directory()
        
        console.print(f"[bold green]✅ Migration complete! Moved {migrated_clients} client directories[/bold green]")
        return True
        
    except (OSError, shutil.Error) as e:
        console.print(f"[red]❌ Error during migration: {e}[/red]")
        return False

def cleanup_old_directory():
    """Remove old ~/Turnkey directory if it's empty or nearly empty."""
    if not os.path.exists(OLD_SINGLE_BASE_DIR):
        return
    
    try:
        # Remove .DS_Store files
        for root, dirs, files in os.walk(OLD_SINGLE_BASE_DIR, topdown=False):
            for file in files:
                if file == '.DS_Store':
                    os.remove(os.path.join(root, file))
        
        # Try to remove empty subdirectories
        for subdir in ['clients', 'shared', 'cache']:
            subdir_path = os.path.join(OLD_SINGLE_BASE_DIR, subdir)
            if os.path.exists(subdir_path):
                try:
                    os.rmdir(subdir_path)
                except OSError:
                    pass  # Directory not empty, that's fine
        
        # Try to remove main directory
        try:
            os.rmdir(OLD_SINGLE_BASE_DIR)
            console.print(f"[dim]🗑️  Cleaned up old ~/Turnkey directory[/dim]")
        except OSError:
            # Directory not empty, check what's left
            remaining = [f for f in os.listdir(OLD_SINGLE_BASE_DIR) if not f.startswith('.')]
            if remaining:
                console.print(f"[yellow]Keeping ~/Turnkey (contains: {', '.join(remaining)})[/yellow]")
    except Exception as e:
        console.print(f"[dim]Note: Could not clean up old directory: {e}[/dim]")

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

def workspace_directories_exist(workspace_name=None):
    """Check if workspace directories already exist."""
    paths = get_new_paths(workspace_name)
    # Check if the basic structure exists
    return (os.path.exists(paths['base']) and 
            os.path.exists(paths['clients']) and 
            os.path.exists(paths['shared']))

def ensure_workspace_directories(workspace_name=None):
    """Ensure workspace directories exist, creating them quietly if needed."""
    paths = get_new_paths(workspace_name)
    
    # Check if this is a first-time setup for this workspace
    needs_setup = not workspace_directories_exist(workspace_name)
    
    if needs_setup:
        # Only show migration message for truly new workspaces
        if needs_migration():
            perform_migration()
        else:
            # Just create directories quietly for new workspaces
            console.print("Starting directory migration...")
            for path in paths.values():
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                    console.print(f"Created directory: {path}")
            console.print("Migration completed successfully!")
    else:
        # Workspace already exists, just ensure directories are there (silent)
        for path in paths.values():
            os.makedirs(path, exist_ok=True)

def get_client_dir(client_id, workspace_name=None):
    """Get the client directory path for current workspace, handling migration if needed."""
    ensure_workspace_directories(workspace_name)
    paths = get_new_paths(workspace_name)
    return os.path.join(paths['clients'], str(client_id))

def get_shared_dir(workspace_name=None):
    """Get the shared directory path for current workspace, handling migration if needed."""
    ensure_workspace_directories(workspace_name)
    return get_new_paths(workspace_name)['shared']

def get_coaching_context_dir(workspace_name=None):
    """Get the coaching context directory path for current workspace, handling migration if needed."""
    ensure_workspace_directories(workspace_name)
    return get_new_paths(workspace_name)['coaching_context']

if __name__ == "__main__":
    # Run migration if called directly
    perform_migration()