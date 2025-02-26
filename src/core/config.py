"""
Module quản lý cấu hình ứng dụng
"""

import os
import json
import time

class Config:
    """Lớp quản lý cấu hình ứng dụng"""
    
    def __init__(self, config_file=None):
        """
        Khởi tạo đối tượng Config
        
        Args:
            config_file (str, optional): Đường dẫn đến file cấu hình
        """
        if config_file is None:
            # Sử dụng thư mục mặc định cho cấu hình
            app_data_dir = os.path.join(os.path.expanduser('~'), '.lappytube')
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
            self.config_file = os.path.join(app_data_dir, 'config.json')
        else:
            self.config_file = config_file
        
        # Cấu hình mặc định
        self.default_config = {
            'save_directory': os.path.join(os.path.expanduser('~'), 'Downloads'),
            'default_format': 'mp4',
            'default_quality': 'highest',
            'recent_downloads': [],
            'theme': 'light'
        }
        
        # Tải cấu hình
        self.config = self.load_config()
    
    def load_config(self):
        """
        Tải cấu hình từ file
        
        Returns:
            dict: Cấu hình đã tải
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Nếu có lỗi, sử dụng cấu hình mặc định
                return self.default_config.copy()
        else:
            # Nếu file không tồn tại, sử dụng cấu hình mặc định
            return self.default_config.copy()
    
    def save_config(self):
        """Lưu cấu hình hiện tại vào file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except IOError:
            return False
    
    def get(self, key, default=None):
        """
        Lấy giá trị cấu hình
        
        Args:
            key (str): Khóa cấu hình
            default: Giá trị mặc định nếu khóa không tồn tại
            
        Returns:
            Giá trị cấu hình
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Đặt giá trị cấu hình
        
        Args:
            key (str): Khóa cấu hình
            value: Giá trị cấu hình
            
        Returns:
            bool: True nếu lưu thành công, False nếu có lỗi
        """
        self.config[key] = value
        return self.save_config()
    
    def add_recent_download(self, url, title):
        """
        Thêm một URL vào danh sách tải xuống gần đây
        
        Args:
            url (str): URL video
            title (str): Tiêu đề video
            
        Returns:
            bool: True nếu lưu thành công, False nếu có lỗi
        """
        recent = self.config.get('recent_downloads', [])
        # Thêm vào đầu danh sách và giới hạn số lượng
        recent.insert(0, {'url': url, 'title': title, 'date': time.strftime('%Y-%m-%d %H:%M:%S')})
        recent = recent[:10]  # Giữ tối đa 10 mục
        self.config['recent_downloads'] = recent
        return self.save_config() 