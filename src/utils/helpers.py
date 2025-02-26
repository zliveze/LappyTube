"""
Các hàm tiện ích cho ứng dụng
"""

import os
import re
import platform
import subprocess

def sanitize_filename(filename):
    """
    Làm sạch tên file để tránh các ký tự không hợp lệ
    
    Args:
        filename (str): Tên file cần làm sạch
        
    Returns:
        str: Tên file đã được làm sạch
    """
    # Thay thế các ký tự không hợp lệ bằng dấu gạch ngang
    invalid_chars = r'[\\/*?:"<>|]'
    return re.sub(invalid_chars, '-', filename)

def format_filesize(size_bytes):
    """
    Định dạng kích thước file thành dạng dễ đọc
    
    Args:
        size_bytes (int): Kích thước file tính bằng byte
        
    Returns:
        str: Chuỗi biểu diễn kích thước file
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def format_duration(seconds):
    """
    Định dạng thời lượng thành dạng dễ đọc
    
    Args:
        seconds (int): Thời lượng tính bằng giây
        
    Returns:
        str: Chuỗi biểu diễn thời lượng
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def open_file_location(file_path):
    """
    Mở thư mục chứa file trong trình quản lý file
    
    Args:
        file_path (str): Đường dẫn đến file
        
    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """
    try:
        if platform.system() == "Windows":
            # Mở thư mục và chọn file trong Windows Explorer
            subprocess.Popen(f'explorer /select,"{file_path}"')
        elif platform.system() == "Darwin":  # macOS
            # Mở thư mục trong Finder
            subprocess.Popen(["open", "-R", file_path])
        else:  # Linux và các hệ điều hành khác
            # Mở thư mục trong trình quản lý file mặc định
            subprocess.Popen(["xdg-open", os.path.dirname(file_path)])
        return True
    except Exception:
        return False 