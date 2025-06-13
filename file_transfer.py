"""
File Transfer Management for SSH Log Collector
Handles file transfer operations with progress tracking and error handling.
"""

import os
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from rich.console import Console
from rich.progress import (
    Progress, TaskID, TextColumn, BarColumn, TimeRemainingColumn,
    FileSizeColumn, TransferSpeedColumn, SpinnerColumn
)
from rich.table import Table
from rich.live import Live

from ssh_manager import SSHConnection, SSHManager
from utils import format_bytes, sanitize_filename

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class TransferTask:
    """Represents a file transfer task"""
    id: str
    server_name: str
    remote_path: str
    local_path: str
    file_size: int
    status: str = "pending"  # pending, downloading, completed, failed
    progress: int = 0
    error: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class FileTransferManager:
    """Manages file transfer operations with progress tracking"""
    
    def __init__(self, ssh_manager: SSHManager, max_concurrent: int = 5):
        self.ssh_manager = ssh_manager
        self.max_concurrent = max_concurrent
        self.transfer_tasks: Dict[str, TransferTask] = {}
        self.active_transfers = 0
        self.total_transferred = 0
        self.total_size = 0
        self._task_counter = 0
        self._lock = threading.Lock()
    
    def add_transfer_task(self, server_name: str, remote_path: str, 
                         local_base_path: str, file_info: Dict[str, Any]) -> str:
        """Add a file transfer task"""
        with self._lock:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}"
            
            # Create local file path
            filename = sanitize_filename(file_info['name'])
            local_path = os.path.join(local_base_path, server_name, filename)
            
            # Ensure unique filename if file exists
            counter = 1
            original_path = local_path
            while os.path.exists(local_path):
                name, ext = os.path.splitext(original_path)
                local_path = f"{name}_{counter}{ext}"
                counter += 1
            
            task = TransferTask(
                id=task_id,
                server_name=server_name,
                remote_path=remote_path,
                local_path=local_path,
                file_size=file_info.get('size', 0)
            )
            
            self.transfer_tasks[task_id] = task
            self.total_size += task.file_size
            
            return task_id
    
    def execute_transfers(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Execute all pending transfer tasks"""
        if not self.transfer_tasks:
            return {"success": True, "completed": 0, "failed": 0, "errors": []}
        
        results = {
            "success": True,
            "completed": 0,
            "failed": 0,
            "errors": [],
            "total_files": len(self.transfer_tasks),
            "total_size": self.total_size
        }
        
        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            FileSizeColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # Overall progress task
            overall_task = progress.add_task(
                "Overall Progress", 
                total=self.total_size,
                visible=True
            )
            
            # File progress tasks
            file_tasks = {}
            for task_id, task in self.transfer_tasks.items():
                file_task = progress.add_task(
                    f"{task.server_name}: {os.path.basename(task.remote_path)}",
                    total=task.file_size,
                    visible=False
                )
                file_tasks[task_id] = file_task
            
            # Execute transfers using thread pool
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                # Submit all tasks
                future_to_task = {}
                for task_id, task in self.transfer_tasks.items():
                    future = executor.submit(
                        self._execute_single_transfer, 
                        task, 
                        lambda task_id, transferred, total: self._update_progress(
                            progress, file_tasks.get(task_id), overall_task, 
                            task_id, transferred, total
                        )
                    )
                    future_to_task[future] = task_id
                
                # Process completed transfers
                for future in as_completed(future_to_task):
                    task_id = future_to_task[future]
                    task = self.transfer_tasks[task_id]
                    
                    try:
                        success = future.result()
                        if success:
                            task.status = "completed"
                            results["completed"] += 1
                            progress.update(file_tasks[task_id], visible=False)
                        else:
                            task.status = "failed"
                            results["failed"] += 1
                            results["errors"].append(f"{task.server_name}: {task.error}")
                            progress.update(file_tasks[task_id], visible=False)
                    
                    except Exception as e:
                        task.status = "failed"
                        task.error = str(e)
                        results["failed"] += 1
                        results["errors"].append(f"{task.server_name}: {str(e)}")
                        progress.update(file_tasks[task_id], visible=False)
            
            # Final progress update
            progress.update(overall_task, completed=self.total_transferred)
        
        if results["failed"] > 0:
            results["success"] = False
        
        return results
    
    def _execute_single_transfer(self, task: TransferTask, progress_callback: Callable) -> bool:
        """Execute a single file transfer"""
        task.start_time = datetime.now()
        task.status = "downloading"
        
        try:
            # Get SSH connection
            connection = self.ssh_manager.get_connection(task.server_name)
            if not connection or not connection.connected:
                task.error = "No active SSH connection"
                return False
            
            # Create progress callback wrapper
            def file_progress_callback(transferred, total):
                task.progress = int((transferred / total) * 100) if total > 0 else 0
                progress_callback(task.id, transferred, total)
            
            # Download file
            success = connection.download_file(
                task.remote_path, 
                task.local_path, 
                file_progress_callback
            )
            
            task.end_time = datetime.now()
            
            if success:
                logger.info(f"Successfully transferred {task.remote_path} to {task.local_path}")
                return True
            else:
                task.error = "Download failed"
                return False
        
        except Exception as e:
            task.error = str(e)
            task.end_time = datetime.now()
            logger.error(f"Transfer failed for {task.remote_path}: {e}")
            return False
    
    def _update_progress(self, progress: Progress, file_task_id: TaskID, 
                        overall_task_id: TaskID, task_id: str, 
                        transferred: int, total: int):
        """Update progress bars"""
        with self._lock:
            # Update file progress
            if file_task_id is not None:
                progress.update(file_task_id, completed=transferred)
            
            # Update overall progress
            # Calculate total transferred across all tasks
            total_transferred = 0
            for t_id, task in self.transfer_tasks.items():
                if task.status == "completed":
                    total_transferred += task.file_size
                elif task.status == "downloading" and t_id == task_id:
                    total_transferred += transferred
            
            progress.update(overall_task_id, completed=total_transferred)
            self.total_transferred = total_transferred
    
    def get_transfer_summary(self) -> Table:
        """Get a summary table of all transfers"""
        table = Table(title="Transfer Summary")
        table.add_column("Server", style="cyan")
        table.add_column("File", style="white")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Status", justify="center")
        table.add_column("Progress", justify="right")
        
        for task in self.transfer_tasks.values():
            status_style = {
                "completed": "green",
                "failed": "red",
                "downloading": "yellow",
                "pending": "dim"
            }.get(task.status, "white")
            
            progress_text = f"{task.progress}%" if task.status == "downloading" else ""
            if task.status == "completed":
                progress_text = "100%"
            elif task.status == "failed":
                progress_text = "Failed"
            
            table.add_row(
                task.server_name,
                os.path.basename(task.remote_path),
                format_bytes(task.file_size),
                f"[{status_style}]{task.status}[/{status_style}]",
                progress_text
            )
        
        return table
    
    def clear_tasks(self):
        """Clear all transfer tasks"""
        self.transfer_tasks.clear()
        self.total_size = 0
        self.total_transferred = 0
        self._task_counter = 0
