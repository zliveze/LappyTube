"""
Điểm khởi chạy chính của ứng dụng LappyTube
"""

import sys
import os

# Thêm thư mục gốc vào đường dẫn để có thể import các module
base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if base_path not in sys.path:
    sys.path.insert(0, base_path)

# Import các module cần thiết
from PyQt5.QtWidgets import QApplication
try:
    from src.ui.main_window import MainWindow
except ModuleNotFoundError:
    # Thử import trực tiếp nếu không tìm thấy module
    try:
        from ui.main_window import MainWindow
    except ModuleNotFoundError:
        # Nếu vẫn không tìm thấy, thử import với đường dẫn tuyệt đối
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "MainWindow", 
            os.path.join(base_path, "src", "ui", "main_window.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        MainWindow = module.MainWindow

def main():
    """Hàm chính để khởi chạy ứng dụng"""
    app = QApplication(sys.argv)
    app.setApplicationName("LappyTube")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 