#!/usr/bin/env python3
"""
Download pre-built SSH Log Collector executable for Windows
This script helps users get the .exe file without needing to build it themselves.
"""

import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

def download_file(url, filename):
    """Download file with progress indicator"""
    try:
        print(f"Downloading {filename}...")
        
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, (downloaded * 100) // total_size)
                print(f"\rProgress: {percent}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        urllib.request.urlretrieve(url, filename, reporthook=show_progress)
        print(f"\n✓ Successfully downloaded {filename}")
        return True
        
    except urllib.error.URLError as e:
        print(f"\n✗ Failed to download: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def main():
    print("SSH Log Collector - Windows Executable Downloader")
    print("=" * 50)
    
    # Create download directory
    download_dir = Path("ssh-log-collector-windows")
    download_dir.mkdir(exist_ok=True)
    
    print(f"Download directory: {download_dir.absolute()}")
    
    # Note: These URLs would need to be updated with actual release URLs
    # when the project is hosted on GitHub or other platforms
    files_to_download = [
        {
            "name": "ssh-log-collector.exe",
            "url": "https://github.com/your-username/ssh-log-collector/releases/latest/download/ssh-log-collector.exe",
            "description": "Main executable file"
        },
        {
            "name": "config.yaml", 
            "url": "https://github.com/your-username/ssh-log-collector/releases/latest/download/config.yaml",
            "description": "Configuration file template"
        }
    ]
    
    print("\nAvailable download options:")
    print("1. Download from GitHub Releases (recommended)")
    print("2. Build locally using Python")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        print("\nTo download the .exe file, you need to:")
        print("1. Upload this project to GitHub")
        print("2. Enable GitHub Actions")
        print("3. The Actions will automatically build .exe files")
        print("4. Download from the Releases page")
        print("\nAlternatively, you can run this project directly with Python:")
        print("   python3 main.py")
        
    elif choice == "2":
        print("\nTo build locally on Windows:")
        print("1. Install Python 3.7+ on a Windows machine")
        print("2. Run: pip install paramiko rich click pyyaml keyboard pyinstaller")
        print("3. Run: pyinstaller --onefile --console --name ssh-log-collector main.py")
        print("4. Find the .exe in the 'dist' folder")
        
    else:
        print("Exiting...")
        return
    
    print(f"\nProject files are ready in: {download_dir.absolute()}")
    print("\nNext steps:")
    print("1. Edit config.yaml with your server details")
    print("2. Run the application")

if __name__ == "__main__":
    main()