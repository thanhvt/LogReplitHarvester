# SSH Log Collector

A Windows command-line utility for automated SSH-based log file collection from multiple Linux/Unix servers.

## Features

- **Interactive Command-Line Interface**: Easy-to-use menu-driven interface with rich formatting
- **Multiple Server Support**: Connect to and manage multiple servers simultaneously
- **Flexible Directory Selection**: Choose specific log directories or patterns per server
- **Time-Based Filtering**: Filter files by modification time (last hour, day, week, etc.)
- **Progress Tracking**: Real-time progress bars and transfer statistics
- **Concurrent Downloads**: Multi-threaded file transfers for better performance
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **SSH Key Support**: Support for both password and SSH key authentication

## Installation

### Option 1: Pre-built Executable (Recommended)

1. Download the latest release from the releases page
2. Extract the files to a directory
3. Edit `config.yaml` with your server details
4. Run `ssh-log-collector.exe`

### Option 2: Build from Source

1. **Prerequisites**:
   - Python 3.7 or later
   - pip package manager

2. **Clone or download** this repository

3. **Install dependencies**:
   ```cmd
   pip install paramiko rich click pyyaml keyboard pyinstaller
   ```

4. **Build executable** (optional):
   ```cmd
   build.bat
   ```
   Or run directly with Python:
   ```cmd
   python main.py
   ```

## Configuration

Edit the `config.yaml` file to configure your servers and log directories:

### Server Configuration

```yaml
servers:
  - name: "Production Server"
    host: "192.168.1.100"
    port: 22
    username: "your_username"
    password: "your_password"  # Optional
    key_file: "~/.ssh/id_rsa"  # Optional, recommended
    passphrase: null           # If key file has passphrase
    timeout: 30
