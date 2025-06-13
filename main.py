#!/usr/bin/env python3
"""
SSH Log Collector - Main Entry Point
A Windows command-line utility for automated SSH-based log file collection
from multiple Linux/Unix servers.
"""

import sys
import os
import traceback
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import click

from config import ConfigManager
from ui import LogCollectorUI
from utils import setup_logging, log_error

console = Console()

@click.command()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--log-file', default='ssh_log_collector.log', help='Log file path')
def main(config, verbose, log_file):
    """SSH Log Collector - Automated log file collection from remote servers"""
    
    # Setup logging
    setup_logging(log_file, verbose)
    
    try:
        # Display welcome banner
        welcome_text = Text()
        welcome_text.append("SSH Log Collector", style="bold blue")
        welcome_text.append("\nAutomated log file collection from remote servers", style="dim")
        
        console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
        
        # Initialize configuration manager
        config_manager = ConfigManager(config)
        
        if not config_manager.load_config():
            console.print("[red]Failed to load configuration. Please check your config.yaml file.[/red]")
            return 1
        
        # Initialize and run UI
        ui = LogCollectorUI(config_manager)
        ui.run()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return 0
    except Exception as e:
        log_error(f"Unexpected error in main: {str(e)}")
        console.print(f"[red]An unexpected error occurred: {str(e)}[/red]")
        if verbose:
            console.print("[dim]Full traceback:[/dim]")
            console.print(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
