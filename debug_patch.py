"""
Patch code để debug vấn đề với custom date range

Hướng dẫn: Copy đoạn code này vào đúng vị trí trong file ui.py, trong hàm _start_collection
đặt vào trước dòng:
files = connection.list_files(
    dir_config['path'],
    dir_config.get('file_pattern', '*'),
    dir_config.get('recursive', False),
    self.time_filter,
    self.time_filter_end
)
"""

# -- Code bắt đầu từ đây --

# Log thông tin bộ lọc thời gian được sử dụng
logger = logging.getLogger(__name__)

if self.time_filter and self.time_filter_end:
    logger.info(f"Using date range filter: from {self.time_filter} to {self.time_filter_end}")
    console.print(f"[dim]Using date range: {self.time_filter.strftime('%d/%m/%Y %H:%M')} to {self.time_filter_end.strftime('%d/%m/%Y %H:%M')}[/dim]")
elif self.time_filter:
    logger.info(f"Using time filter: after {self.time_filter}")
    console.print(f"[dim]Using time filter: after {self.time_filter.strftime('%d/%m/%Y %H:%M')}[/dim]")
else:
    logger.info("No time filter applied")
    console.print("[dim]No time filter applied[/dim]")

# Tạm thời bật logging chi tiết trong ssh_manager
previous_level = logging.getLogger('ssh_manager').level
logging.getLogger('ssh_manager').setLevel(logging.DEBUG)

# --- Đoạn gọi list_files đi ở đây ---

# Khôi phục log level sau khi gọi xong
logging.getLogger('ssh_manager').setLevel(previous_level)
