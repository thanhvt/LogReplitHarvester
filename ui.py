"""
User Interface for SSH Log Collector
Provides interactive command-line interface with rich formatting.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
import keyboard

from config import ConfigManager
from ssh_manager import SSHManager, SSHConnection
from file_transfer import FileTransferManager
from utils import format_bytes, get_time_filter_options, get_custom_time_range

console = Console()
logger = logging.getLogger(__name__)

class LogCollectorUI:
    """Interactive user interface for SSH Log Collector"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.ssh_manager = SSHManager()
        self.selected_servers = set()
        self.selected_directories = {}  # server_name -> [directory_configs]
        self.time_filter = None
        self.time_filter_end = None  # For custom date range
        self.download_path = ""
        
    def run(self):
        """Main UI loop"""
        try:
            while True:
                self._show_main_menu()
                choice = self._get_menu_choice([
                    "1", "2", "3", "4", "5", "6", "q"
                ])
                
                if choice == "1":
                    self._select_servers()
                elif choice == "2":
                    self._select_directories()
                elif choice == "3":
                    self._select_time_filter()
                elif choice == "4":
                    self._select_download_path()
                elif choice == "5":
                    self._start_collection()
                elif choice == "6":
                    self._show_current_settings()
                elif choice == "q":
                    break
                
                if choice != "q":
                    console.print("\n[dim]Press any key to continue...[/dim]")
                    console.input("")
        
        finally:
            self.ssh_manager.disconnect_all()
    
    def _show_main_menu(self):
        """Display the main menu"""
        console.clear()
        
        # Title
        title = Text("SSH Log Collector", style="bold blue")
        subtitle = Text("Select your options and start log collection", style="dim")
        
        # Menu options
        menu_text = Text()
        menu_text.append("1. Select Servers", style="white")
        menu_text.append(f" ({len(self.selected_servers)} selected)\n", style="dim")
        
        total_dirs = sum(len(dirs) for dirs in self.selected_directories.values())
        menu_text.append("2. Select Log Directories", style="white")
        menu_text.append(f" ({total_dirs} selected)\n", style="dim")
        
        if self.time_filter and self.time_filter_end:
            time_desc = f"Custom: {self.time_filter.strftime('%Y-%m-%d %H:%M')} to {self.time_filter_end.strftime('%Y-%m-%d %H:%M')}"
        elif self.time_filter:
            time_desc = f"After: {self.time_filter.strftime('%Y-%m-%d %H:%M')}"
        else:
            time_desc = "Not set"
        menu_text.append("3. Select Time Filter", style="white")
        menu_text.append(f" ({time_desc})\n", style="dim")
        
        path_desc = self.download_path or "Not set"
        menu_text.append("4. Select Download Path", style="white")
        menu_text.append(f" ({path_desc})\n", style="dim")
        
        menu_text.append("5. Start Log Collection", style="bold green")
        menu_text.append(" (requires all settings)\n", style="dim")
        
        menu_text.append("6. Show Current Settings\n", style="white")
        menu_text.append("Q. Quit", style="red")
        
        # Display
        layout = Layout()
        layout.split_column(
            Layout(Panel(Columns([title, subtitle]), border_style="blue"), size=3),
            Layout(Panel(menu_text, title="Main Menu", border_style="white"))
        )
        
        console.print(layout)
    
    def _select_servers(self):
        """Server selection interface"""
        console.clear()
        servers = self.config_manager.get_servers()
        
        if not servers:
            console.print("[red]No servers configured![/red]")
            return
        
        # Display server table
        table = Table(title="Available Servers")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Name", style="white")
        table.add_column("Host", style="green")
        table.add_column("Port", justify="right")
        table.add_column("Username", style="yellow")
        table.add_column("Selected", justify="center")
        
        server_list = list(servers.items())
        for i, (name, config) in enumerate(server_list, 1):
            selected = "✓" if name in self.selected_servers else ""
            table.add_row(
                str(i),
                name,
                config['host'],
                str(config.get('port', 22)),
                config['username'],
                f"[green]{selected}[/green]" if selected else ""
            )
        
        console.print(table)
        console.print("\n[bold]Selection Options:[/bold]")
        console.print("- Enter server numbers (e.g., 1,3,5)")
        console.print("- Enter 'all' to select all servers")
        console.print("- Enter 'none' to clear selection")
        console.print("- Press Enter to keep current selection")
        
        selection = Prompt.ask("Select servers").strip()
        
        if selection.lower() == "all":
            self.selected_servers = set(servers.keys())
        elif selection.lower() == "none":
            self.selected_servers.clear()
            self.selected_directories.clear()
        elif selection:
            try:
                indices = [int(x.strip()) for x in selection.split(',')]
                new_selection = set()
                for idx in indices:
                    if 1 <= idx <= len(server_list):
                        server_name = server_list[idx-1][0]
                        new_selection.add(server_name)
                
                # Remove directories for unselected servers
                for server_name in list(self.selected_directories.keys()):
                    if server_name not in new_selection:
                        del self.selected_directories[server_name]
                
                self.selected_servers = new_selection
                
            except ValueError:
                console.print("[red]Invalid selection![/red]")
    
    def _select_directories(self):
        """Directory selection interface"""
        if not self.selected_servers:
            console.print("[red]Please select servers first![/red]")
            return
        
        console.clear()
        
        for server_name in self.selected_servers:
            directories = self.config_manager.get_directories_for_server(server_name)
            
            if not directories:
                console.print(f"[yellow]No directories configured for {server_name}[/yellow]")
                continue
            
            # Display directories for this server
            table = Table(title=f"Log Directories for {server_name}")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Name", style="white")
            table.add_column("Path", style="green")
            table.add_column("Pattern", style="yellow")
            table.add_column("Recursive", justify="center")
            table.add_column("Selected", justify="center")
            
            selected_dirs = self.selected_directories.get(server_name, [])
            
            for i, dir_config in enumerate(directories, 1):
                selected = "✓" if dir_config in selected_dirs else ""
                recursive = "Yes" if dir_config.get('recursive', False) else "No"
                
                table.add_row(
                    str(i),
                    dir_config['name'],
                    dir_config['path'],
                    dir_config.get('file_pattern', '*'),
                    recursive,
                    f"[green]{selected}[/green]" if selected else ""
                )
            
            console.print(table)
            console.print(f"\n[bold]Select directories for {server_name}:[/bold]")
            console.print("- Enter directory numbers (e.g., 1,2)")
            console.print("- Enter 'all' to select all directories")
            console.print("- Enter 'none' to clear selection")
            console.print("- Press Enter to keep current selection")
            
            selection = Prompt.ask(f"Select directories for {server_name}").strip()
            
            if selection.lower() == "all":
                self.selected_directories[server_name] = directories.copy()
            elif selection.lower() == "none":
                self.selected_directories[server_name] = []
            elif selection:
                try:
                    indices = [int(x.strip()) for x in selection.split(',')]
                    selected_dirs = []
                    for idx in indices:
                        if 1 <= idx <= len(directories):
                            selected_dirs.append(directories[idx-1])
                    
                    self.selected_directories[server_name] = selected_dirs
                    
                except ValueError:
                    console.print("[red]Invalid selection![/red]")
                    console.input("Press Enter to continue...")
    
    def _select_time_filter(self):
        """Time filter selection interface"""
        console.clear()
        
        options = get_time_filter_options()
        
        table = Table(title="Time Filter Options")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Description", style="white")
        table.add_column("Filter", style="green")
        
        for i, (desc, filter_func) in enumerate(options, 1):
            current = " (current)" if str(filter_func) == str(self.time_filter) else ""
            table.add_row(str(i), desc + current, str(filter_func) if filter_func else "No filter")
        
        console.print(table)
        
        try:
            choice = Prompt.ask("Select time filter", default="1")
            idx = int(choice) - 1
            
            if 0 <= idx < len(options):
                desc, filter_value = options[idx]
                
                if filter_value == "custom":
                    # Handle custom date range
                    start_date, end_date = get_custom_time_range()
                    if start_date and end_date:
                        self.time_filter = start_date
                        self.time_filter_end = end_date
                        console.print(f"[green]Custom time filter set: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}[/green]")
                    else:
                        console.print("[yellow]Custom date range not set[/yellow]")
                else:
                    # Handle predefined filters
                    self.time_filter = filter_value
                    self.time_filter_end = None
                    console.print(f"[green]Time filter set to: {desc}[/green]")
            else:
                console.print("[red]Invalid selection![/red]")
                
        except ValueError:
            console.print("[red]Invalid selection![/red]")
    
    def _select_download_path(self):
        """Download path selection interface"""
        console.clear()
        
        default_path = self.config_manager.get_default_download_path()
        current_path = self.download_path or default_path
        
        console.print(f"[bold]Current download path:[/bold] {current_path}")
        console.print("\nEnter new download path or press Enter to keep current:")
        
        new_path = Prompt.ask("Download path", default=current_path)
        
        # Expand user path and make absolute
        new_path = os.path.abspath(os.path.expanduser(new_path))
        
        # Check if path exists, create if needed
        if not os.path.exists(new_path):
            if Confirm.ask(f"Directory {new_path} does not exist. Create it?"):
                try:
                    os.makedirs(new_path, exist_ok=True)
                    self.download_path = new_path
                    console.print(f"[green]Download path set to: {new_path}[/green]")
                except Exception as e:
                    console.print(f"[red]Error creating directory: {e}[/red]")
            else:
                console.print("[yellow]Download path not changed[/yellow]")
        else:
            self.download_path = new_path
            console.print(f"[green]Download path set to: {new_path}[/green]")
    
    def _start_collection(self):
        """Start the log collection process"""
        # Validate settings
        if not self.selected_servers:
            console.print("[red]Please select at least one server![/red]")
            return
        
        if not any(self.selected_directories.values()):
            console.print("[red]Please select at least one directory![/red]")
            return
        
        if not self.download_path:
            console.print("[red]Please set a download path![/red]")
            return
        
        console.clear()
        console.print("[bold blue]Starting Log Collection...[/bold blue]")
        
        # Connect to servers
        console.print("\n[bold]Connecting to servers...[/bold]")
        connections = {}
        
        for server_name in self.selected_servers:
            if server_name not in self.selected_directories or not self.selected_directories[server_name]:
                continue
                
            server_config = self.config_manager.get_server(server_name)
            connection = self.ssh_manager.create_connection(server_name, server_config)
            
            console.print(f"Connecting to {server_name}...")
            if connection.connect():
                connections[server_name] = connection
                console.print(f"[green]✓ Connected to {server_name}[/green]")
            else:
                console.print(f"[red]✗ Failed to connect to {server_name}[/red]")
        
        if not connections:
            console.print("[red]No successful connections! Aborting.[/red]")
            return
        
        # Collect file lists
        console.print("\n[bold]Scanning for log files...[/bold]")
        transfer_manager = FileTransferManager(
            self.ssh_manager, 
            self.config_manager.get_max_concurrent_transfers()
        )
        
        total_files = 0
        total_size = 0
        
        for server_name, connection in connections.items():
            for dir_config in self.selected_directories[server_name]:
                console.print(f"Scanning {server_name}:{dir_config['path']}...")
                
                try:
                    files = connection.list_files(
                        dir_config['path'],
                        dir_config.get('file_pattern', '*'),
                        dir_config.get('recursive', False),
                        self.time_filter,
                        self.time_filter_end
                    )
                    
                    for file_info in files:
                        task_id = transfer_manager.add_transfer_task(
                            server_name, 
                            file_info['path'], 
                            self.download_path, 
                            file_info
                        )
                        total_files += 1
                        total_size += file_info.get('size', 0)
                    
                    console.print(f"[green]Found {len(files)} files in {dir_config['name']}[/green]")
                    
                except Exception as e:
                    console.print(f"[red]Error scanning {dir_config['name']}: {e}[/red]")
        
        if total_files == 0:
            console.print("[yellow]No files found matching the criteria![/yellow]")
            return
        
        # Show summary and confirm
        console.print(f"\n[bold]Found {total_files} files ({format_bytes(total_size)})[/bold]")
        
        if not Confirm.ask("Start downloading?"):
            console.print("[yellow]Download cancelled[/yellow]")
            return
        
        # Start transfer
        console.print("\n[bold]Starting file transfers...[/bold]")
        
        try:
            results = transfer_manager.execute_transfers()
            
            # Show results
            console.print("\n" + "="*60)
            console.print("[bold]Transfer Results:[/bold]")
            console.print(f"Total files: {results['total_files']}")
            console.print(f"[green]Completed: {results['completed']}[/green]")
            console.print(f"[red]Failed: {results['failed']}[/red]")
            console.print(f"Total size: {format_bytes(results['total_size'])}")
            
            if results['errors']:
                console.print("\n[bold red]Errors:[/bold red]")
                for error in results['errors']:
                    console.print(f"[red]• {error}[/red]")
            
            # Show transfer summary table
            console.print("\n")
            console.print(transfer_manager.get_transfer_summary())
            
            if results['success']:
                console.print(f"\n[bold green]All files downloaded successfully to: {self.download_path}[/bold green]")
            else:
                console.print(f"\n[bold yellow]Download completed with some failures. Files saved to: {self.download_path}[/bold yellow]")
        
        except Exception as e:
            console.print(f"[red]Transfer failed: {e}[/red]")
            logger.error(f"Transfer error: {e}")
    
    def _show_current_settings(self):
        """Display current settings summary"""
        console.clear()
        
        # Servers
        server_table = Table(title="Selected Servers")
        server_table.add_column("Server", style="cyan")
        server_table.add_column("Host", style="white")
        server_table.add_column("Username", style="yellow")
        
        for server_name in self.selected_servers:
            server_config = self.config_manager.get_server(server_name)
            server_table.add_row(
                server_name,
                server_config['host'],
                server_config['username']
            )
        
        # Directories
        dir_table = Table(title="Selected Directories")
        dir_table.add_column("Server", style="cyan")
        dir_table.add_column("Directory", style="white")
        dir_table.add_column("Path", style="green")
        dir_table.add_column("Pattern", style="yellow")
        
        for server_name, directories in self.selected_directories.items():
            for dir_config in directories:
                dir_table.add_row(
                    server_name,
                    dir_config['name'],
                    dir_config['path'],
                    dir_config.get('file_pattern', '*')
                )
        
        # Settings summary
        settings_text = Text()
        settings_text.append("Time Filter: ", style="bold")
        settings_text.append(str(self.time_filter) if self.time_filter else "Not set", style="white")
        settings_text.append("\nDownload Path: ", style="bold")
        settings_text.append(self.download_path or "Not set", style="white")
        
        # Display all
        console.print(server_table)
        console.print("\n")
        console.print(dir_table)
        console.print("\n")
        console.print(Panel(settings_text, title="Other Settings", border_style="blue"))
    
    def _get_menu_choice(self, valid_choices: List[str]) -> str:
        """Get valid menu choice from user"""
        while True:
            choice = Prompt.ask("Choose an option").strip().lower()
            if choice in [c.lower() for c in valid_choices]:
                return choice
            console.print(f"[red]Invalid choice. Please select from: {', '.join(valid_choices)}[/red]")
