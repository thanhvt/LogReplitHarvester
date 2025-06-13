"""
Utility functions for SSH Log Collector
Common helper functions used across the application.
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Callable
import unicodedata

def setup_logging(log_file: str = "ssh_log_collector.log", verbose: bool = False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler (only for warnings and errors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress paramiko debug logs unless verbose
    if not verbose:
        logging.getLogger('paramiko').setLevel(logging.WARNING)

def log_error(message: str):
    """Log an error message"""
    logging.getLogger(__name__).error(message)

def format_bytes(size: int) -> str:
    """Format byte size in human readable format"""
    if size == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size_float = float(size)
    
    while size_float >= 1024 and unit_index < len(units) - 1:
        size_float /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size_float)} {units[unit_index]}"
    else:
        return f"{size_float:.1f} {units[unit_index]}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for Windows compatibility"""
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove control characters
    sanitized = ''.join(char for char in sanitized if unicodedata.category(char)[0] != 'C')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "file"
    
    # Limit length to 200 characters (keeping some room for path)
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized

def get_time_filter_options() -> List[Tuple[str, Optional[datetime]]]:
    """Get available time filter options"""
    now = datetime.now()
    
    options = [
        ("No time filter", None),
        ("Last 1 hour", now - timedelta(hours=1)),
        ("Last 6 hours", now - timedelta(hours=6)),
        ("Last 12 hours", now - timedelta(hours=12)),
        ("Last 24 hours", now - timedelta(days=1)),
        ("Last 3 days", now - timedelta(days=3)),
        ("Last week", now - timedelta(weeks=1)),
        ("Last month", now - timedelta(days=30)),
        ("Custom date range", "custom"),
    ]
    
    return options

def validate_path(path: str) -> bool:
    """Validate if a path is valid for the current OS"""
    try:
        # Expand user path
        expanded_path = os.path.expanduser(path)
        
        # Check if parent directory exists or can be created
        parent_dir = os.path.dirname(expanded_path)
        if parent_dir and not os.path.exists(parent_dir):
            return False
        
        # Check for invalid characters (Windows-specific)
        if os.name == 'nt':
            invalid_chars = r'[<>:"|?*]'
            if re.search(invalid_chars, os.path.basename(expanded_path)):
                return False
        
        return True
        
    except Exception:
        return False

def ensure_directory_exists(path: str) -> bool:
    """Ensure directory exists, create if necessary"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        log_error(f"Failed to create directory {path}: {e}")
        return False

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()

def is_log_file(filename: str) -> bool:
    """Check if filename appears to be a log file"""
    log_extensions = {'.log', '.txt', '.out', '.err', '.trace'}
    log_patterns = ['log', 'debug', 'error', 'trace', 'audit']
    
    # Check extension
    if get_file_extension(filename) in log_extensions:
        return True
    
    # Check filename patterns
    filename_lower = filename.lower()
    return any(pattern in filename_lower for pattern in log_patterns)

def create_progress_callback(task_description: str) -> Callable:
    """Create a progress callback function for file transfers"""
    def progress_callback(transferred: int, total: int):
        if total > 0:
            percentage = (transferred / total) * 100
            transferred_str = format_bytes(transferred)
            total_str = format_bytes(total)
            print(f"\r{task_description}: {percentage:.1f}% ({transferred_str}/{total_str})", end='', flush=True)
        else:
            print(f"\r{task_description}: {format_bytes(transferred)}", end='', flush=True)
    
    return progress_callback

def get_unique_filename(base_path: str, filename: str) -> str:
    """Get a unique filename by appending a number if file exists"""
    full_path = os.path.join(base_path, filename)
    
    if not os.path.exists(full_path):
        return full_path
    
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = os.path.join(base_path, new_filename)
        
        if not os.path.exists(new_path):
            return new_path
        
        counter += 1

def parse_time_string(time_str: str) -> Optional[datetime]:
    """Parse various time string formats into datetime object"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%Y%m%d",
        "%d-%m-%Y",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    return None

def get_custom_time_range():
    """Get custom time range from user input"""
    from rich.console import Console
    from rich.prompt import Prompt
    
    console = Console()
    
    console.print("\n[bold]Custom Date Range Setup[/bold]")
    console.print("Supported formats:")
    console.print("- YYYY-MM-DD (e.g., 2024-01-15)")
    console.print("- DD/MM/YYYY (e.g., 15/01/2024)")
    console.print("- DD-MM-YYYY (e.g., 15-01-2024)")
    console.print("- YYYY-MM-DD HH:MM (e.g., 2024-01-15 14:30)")
    console.print("- DD/MM/YYYY HH:MM (e.g., 15/01/2024 14:30)")
    
    try:
        # Get start date
        start_str = Prompt.ask("\nEnter start date/time")
        start_date = parse_time_string(start_str)
        
        if not start_date:
            console.print("[red]Invalid start date format![/red]")
            return None, None
        
        # Get end date
        end_str = Prompt.ask("Enter end date/time")
        end_date = parse_time_string(end_str)
        
        if not end_date:
            console.print("[red]Invalid end date format![/red]")
            return None, None
        
        # Validate date range
        if start_date >= end_date:
            console.print("[red]Start date must be before end date![/red]")
            return None, None
        
        console.print(f"[green]Custom range set: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}[/green]")
        return start_date, end_date
        
    except Exception as e:
        console.print(f"[red]Error setting custom date range: {e}[/red]")
        return None, None

def get_system_info() -> dict:
    """Get basic system information"""
    import platform
    
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.architecture()[0],
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }
