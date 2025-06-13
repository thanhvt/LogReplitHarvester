"""
Configuration Management for SSH Log Collector
Handles loading and validation of server and directory configurations.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
import logging

console = Console()
logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = Path(config_file)
        self.config = {}
        self.servers = {}
        self.directories = {}
        
    def load_config(self) -> bool:
        """Load configuration from YAML file"""
        try:
            if not self.config_file.exists():
                self._create_default_config()
                console.print(f"[yellow]Created default configuration file: {self.config_file}[/yellow]")
                console.print("[yellow]Please edit the configuration file and restart the application.[/yellow]")
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            if not self._validate_config():
                return False
                
            self._process_config()
            logger.info(f"Configuration loaded successfully from {self.config_file}")
            return True
            
        except yaml.YAMLError as e:
            console.print(f"[red]Error parsing YAML configuration: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            return False
    
    def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            'servers': [
                {
                    'name': 'Production Server 1',
                    'host': '192.168.1.100',
                    'port': 22,
                    'username': 'your_username',
                    'password': 'your_password',  # Optional, use key_file instead
                    'key_file': None,  # Path to SSH private key file
                    'passphrase': None,  # Passphrase for key file if needed
                    'timeout': 30
                },
                {
                    'name': 'Development Server',
                    'host': '192.168.1.101', 
                    'port': 22,
                    'username': 'dev_user',
                    'key_file': '~/.ssh/id_rsa',
                    'timeout': 30
                }
            ],
            'directories': [
                {
                    'name': 'Application Logs',
                    'path': '/var/log/myapp',
                    'server': 'Production Server 1',
                    'file_pattern': '*.log',
                    'recursive': True
                },
                {
                    'name': 'System Logs',
                    'path': '/var/log',
                    'server': 'Production Server 1', 
                    'file_pattern': '*.log',
                    'recursive': False
                },
                {
                    'name': 'Dev Application Logs',
                    'path': '/home/dev/logs',
                    'server': 'Development Server',
                    'file_pattern': '*.log',
                    'recursive': True
                }
            ],
            'settings': {
                'default_download_path': './downloads',
                'max_concurrent_transfers': 5,
                'retry_attempts': 3,
                'connection_timeout': 30
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    def _validate_config(self) -> bool:
        """Validate configuration structure"""
        required_sections = ['servers', 'directories']
        
        for section in required_sections:
            if section not in self.config:
                console.print(f"[red]Missing required section '{section}' in configuration[/red]")
                return False
        
        # Validate servers
        for i, server in enumerate(self.config.get('servers', [])):
            required_server_fields = ['name', 'host', 'username']
            for field in required_server_fields:
                if field not in server:
                    console.print(f"[red]Server {i+1}: Missing required field '{field}'[/red]")
                    return False
        
        # Validate directories
        for i, directory in enumerate(self.config.get('directories', [])):
            required_dir_fields = ['name', 'path', 'server']
            for field in required_dir_fields:
                if field not in directory:
                    console.print(f"[red]Directory {i+1}: Missing required field '{field}'[/red]")
                    return False
        
        return True
    
    def _process_config(self):
        """Process and organize configuration data"""
        # Process servers
        for server in self.config['servers']:
            # Set defaults
            server.setdefault('port', 22)
            server.setdefault('timeout', 30)
            server.setdefault('key_file', None)
            server.setdefault('password', None)
            server.setdefault('passphrase', None)
            
            # Expand key file path
            if server['key_file']:
                server['key_file'] = os.path.expanduser(server['key_file'])
            
            self.servers[server['name']] = server
        
        # Process directories
        for directory in self.config['directories']:
            # Set defaults
            directory.setdefault('file_pattern', '*')
            directory.setdefault('recursive', False)
            
            server_name = directory['server']
            if server_name not in self.servers:
                console.print(f"[yellow]Warning: Directory '{directory['name']}' references unknown server '{server_name}'[/yellow]")
                continue
            
            if server_name not in self.directories:
                self.directories[server_name] = []
            
            self.directories[server_name].append(directory)
    
    def get_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured servers"""
        return self.servers
    
    def get_directories_for_server(self, server_name: str) -> List[Dict[str, Any]]:
        """Get directories configured for a specific server"""
        return self.directories.get(server_name, [])
    
    def get_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific server"""
        return self.servers.get(server_name)
    
    def get_setting(self, key: str, default=None):
        """Get a setting value with optional default"""
        return self.config.get('settings', {}).get(key, default)
    
    def get_default_download_path(self) -> str:
        """Get the default download path"""
        return self.get_setting('default_download_path', './downloads')
    
    def get_max_concurrent_transfers(self) -> int:
        """Get maximum concurrent transfers setting"""
        return self.get_setting('max_concurrent_transfers', 5)
    
    def get_retry_attempts(self) -> int:
        """Get retry attempts setting"""
        return self.get_setting('retry_attempts', 3)
    
    def get_connection_timeout(self) -> int:
        """Get connection timeout setting"""
        return self.get_setting('connection_timeout', 30)
