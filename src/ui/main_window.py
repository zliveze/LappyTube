"""
Cửa sổ chính của ứng dụng LappyTube
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QProgressBar, QFileDialog, QMessageBox, QGroupBox, QApplication,
                            QTabWidget, QCheckBox, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import os
import time
import sys
import subprocess

from src.core.downloader import YouTubeDownloader

class DownloadThread(QThread):
    """Thread xử lý tải xuống để không chặn giao diện người dùng"""
    progress_signal = pyqtSignal(int, int, int, int)  # percent, downloaded, total, speed
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, downloader, url, save_path, download_type, quality, speed_limit=0,
                 concurrent_downloads=8, buffer_size=16*1024*1024, retry_count=10, ffmpeg_path=None):
        super().__init__()
        self.downloader = downloader
        self.url = url
        self.save_path = save_path
        self.download_type = download_type
        self.quality = quality
        self.speed_limit = speed_limit
        self.concurrent_downloads = concurrent_downloads
        self.buffer_size = buffer_size
        self.retry_count = retry_count
        self.ffmpeg_path = ffmpeg_path
        self.is_cancelled = False
        
    def run(self):
        try:
            # Thêm hàm callback riêng để đảm bảo tín hiệu được gửi đúng cách
            def progress_callback(percent, downloaded, total, speed):
                # Kiểm tra nếu đã hủy thì dừng tải xuống
                if self.is_cancelled:
                    return False  # Trả về False để báo hiệu dừng tải xuống
                
                # In ra console để debug
                print(f"Progress: {percent}%, Downloaded: {downloaded}, Total: {total}, Speed: {speed}")
                self.progress_signal.emit(percent, downloaded, total, speed)
                return True  # Tiếp tục tải xuống
            
            self.downloader.download(
                self.url, 
                self.save_path, 
                self.download_type,
                self.quality,
                progress_callback,
                self.speed_limit,
                self.concurrent_downloads,
                self.buffer_size,
                self.retry_count,
                self.ffmpeg_path
            )
            
            if not self.is_cancelled:
                self.finished_signal.emit("Tải xuống hoàn tất!")
            else:
                self.error_signal.emit("Đã hủy tải xuống")
        except Exception as e:
            if not self.is_cancelled:
                self.error_signal.emit(f"Lỗi: {str(e)}")
            
    def cancel_download(self):
        """Hủy quá trình tải xuống"""
        self.is_cancelled = True

class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""
    
    def __init__(self):
        super().__init__()
        self.downloader = YouTubeDownloader()
        self.last_downloaded = 0
        self.last_time = 0
        # Cải thiện biến lưu trữ lịch sử tốc độ tải xuống
        self.speed_history = []
        self.speed_history_max_size = 10  # Tăng lên 10 giá trị để làm mượt hơn
        self.last_displayed_speed = 0  # Lưu tốc độ hiển thị cuối cùng
        self.speed_update_threshold = 0.15  # Ngưỡng thay đổi 15% để cập nhật hiển thị
        self.last_speed_update_time = 0  # Thời điểm cập nhật tốc độ cuối cùng
        self.speed_update_interval = 1.0  # Chỉ cập nhật tốc độ mỗi 1 giây
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle("LappyTube - Tải Video YouTube")
        self.setMinimumSize(600, 450)  # Tăng kích thước cửa sổ
        
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Thêm khoảng cách lề
        
        # Tạo tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Tab tải xuống
        download_tab = QWidget()
        self.tab_widget.addTab(download_tab, "Tải xuống")
        
        # Tab cài đặt
        settings_tab = QWidget()
        self.tab_widget.addTab(settings_tab, "Cài đặt")
        
        # Thiết lập tab tải xuống
        self.setup_download_tab(download_tab)
        
        # Thiết lập tab cài đặt
        self.setup_settings_tab(settings_tab)
    
    def setup_download_tab(self, tab):
        """Thiết lập giao diện cho tab tải xuống"""
        # Layout chính cho tab
        tab_layout = QVBoxLayout(tab)
        
        # Phần nhập URL và phân tích
        url_layout = QHBoxLayout()
        url_label = QLabel("URL Video:")
        url_label.setMinimumWidth(80)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Nhập URL video YouTube")
        self.analyze_btn = QPushButton("Phân tích")
        self.analyze_btn.setMinimumWidth(100)
        self.analyze_btn.clicked.connect(self.analyze_video)
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.analyze_btn)
        
        # Thông tin video
        info_group = QGroupBox("Thông tin Video")
        info_layout = QVBoxLayout(info_group)
        
        # Tiêu đề
        title_layout = QHBoxLayout()
        title_label = QLabel("Tiêu đề:")
        title_label.setMinimumWidth(80)
        self.title_value = QLabel("Chưa có thông tin")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_value)
        
        # Kênh
        channel_layout = QHBoxLayout()
        channel_label = QLabel("Kênh:")
        channel_label.setMinimumWidth(80)
        self.channel_value = QLabel("Chưa có thông tin")
        channel_layout.addWidget(channel_label)
        channel_layout.addWidget(self.channel_value)
        
        # Thời lượng
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Thời lượng:")
        duration_label.setMinimumWidth(80)
        self.duration_value = QLabel("Chưa có thông tin")
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_value)
        
        info_layout.addLayout(title_layout)
        info_layout.addLayout(channel_layout)
        info_layout.addLayout(duration_layout)
        
        # Tùy chọn tải xuống
        download_group = QGroupBox("Tùy chọn tải xuống")
        download_layout = QVBoxLayout(download_group)
        
        # Loại tải xuống (video hoặc audio)
        download_type_layout = QHBoxLayout()
        download_type_label = QLabel("Loại tải xuống:")
        download_type_label.setMinimumWidth(80)
        self.download_type_combo = QComboBox()
        self.download_type_combo.addItem("Video", "video")
        self.download_type_combo.addItem("Chỉ Audio", "audio")
        self.download_type_combo.currentIndexChanged.connect(self.on_download_type_changed)
        download_type_layout.addWidget(download_type_label)
        download_type_layout.addWidget(self.download_type_combo)
        
        # Tốc độ tải xuống
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Tốc độ tải:")
        speed_label.setMinimumWidth(80)
        self.speed_combo = QComboBox()
        self.speed_combo.addItem("Không giới hạn")
        self.speed_combo.addItem("1 MB/s")
        self.speed_combo.addItem("2 MB/s")
        self.speed_combo.addItem("5 MB/s")
        self.speed_combo.addItem("10 MB/s")
        self.speed_combo.addItem("20 MB/s")
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_combo)
        
        # Chất lượng
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Chất lượng:")
        quality_label.setMinimumWidth(80)
        self.quality_combo = QComboBox()
        self.quality_combo.setEnabled(False)  # Vô hiệu hóa cho đến khi phân tích
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        
        # Thư mục lưu
        save_layout = QHBoxLayout()
        save_label = QLabel("Lưu vào:")
        save_label.setMinimumWidth(80)
        self.save_path_input = QLineEdit()
        self.save_path_input.setText(os.path.join(os.path.expanduser('~'), 'Downloads'))
        self.browse_btn = QPushButton("Duyệt...")
        self.browse_btn.clicked.connect(self.browse_save_location)
        save_layout.addWidget(save_label)
        save_layout.addWidget(self.save_path_input)
        save_layout.addWidget(self.browse_btn)
        
        download_layout.addLayout(download_type_layout)
        download_layout.addLayout(speed_layout)
        download_layout.addLayout(quality_layout)
        download_layout.addLayout(save_layout)
        
        # Tiến trình tải xuống
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Thêm label hiển thị thông tin chi tiết về tiến trình
        self.download_info_label = QLabel("")
        self.download_info_label.setVisible(False)
        
        self.status_label = QLabel("Sẵn sàng")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.download_info_label)
        progress_layout.addWidget(self.status_label)
        
        # Nút tải xuống và hủy
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Thêm nút hủy tải xuống
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setEnabled(False)  # Vô hiệu hóa ban đầu
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.download_btn = QPushButton("Tải xuống")
        self.download_btn.setEnabled(False)  # Vô hiệu hóa cho đến khi phân tích
        self.download_btn.setMinimumWidth(120)
        self.download_btn.setMinimumHeight(40)  # Làm nút to hơn
        self.download_btn.clicked.connect(self.download_video)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.download_btn)
        
        # Thêm tất cả vào layout chính
        tab_layout.addLayout(url_layout)
        tab_layout.addWidget(info_group)
        tab_layout.addWidget(download_group)
        tab_layout.addLayout(progress_layout)
        tab_layout.addLayout(button_layout)
    
    def browse_save_location(self):
        """Mở hộp thoại chọn thư mục lưu"""
        directory = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục lưu", self.save_path_input.text()
        )
        if directory:
            self.save_path_input.setText(directory)
    
    def analyze_video(self):
        """Phân tích video từ URL"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập URL video YouTube")
            return
        
        # Đặt lại giao diện tiến trình
        self.reset_progress_ui()
        
        # Vô hiệu hóa nút phân tích trong khi đang xử lý
        self.analyze_btn.setEnabled(False)
        self.status_label.setText("Đang phân tích video...")
        
        # Sử dụng QThread để phân tích video
        self.analyze_thread = AnalyzeThread(self.downloader, url)
        self.analyze_thread.finished_signal.connect(self.on_analyze_finished)
        self.analyze_thread.error_signal.connect(self.on_analyze_error)
        self.analyze_thread.start()
    
    def on_analyze_finished(self, video_info):
        """Xử lý khi phân tích video hoàn tất"""
        # Lưu thông tin video
        self.video_info = video_info
        
        # Cập nhật thông tin video
        self.title_value.setText(video_info['title'])
        self.channel_value.setText(video_info['author'])
        
        # Định dạng thời lượng
        duration = video_info['length']
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            duration_str = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
        else:
            duration_str = f"{int(minutes)}:{int(seconds):02d}"
        
        self.duration_value.setText(duration_str)
        
        # Cập nhật các tùy chọn chất lượng
        self.update_quality_options(video_info)
        
        # Kích hoạt nút tải xuống
        self.download_btn.setEnabled(True)
        
        # Đặt lại thanh tiến trình
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.download_info_label.setVisible(False)
        
        self.status_label.setText("Sẵn sàng tải xuống")
    
    def on_analyze_error(self, error_message):
        """Xử lý khi có lỗi phân tích"""
        QMessageBox.critical(self, "Lỗi", error_message)
        self.analyze_btn.setEnabled(True)
        self.status_label.setText("Có lỗi xảy ra")
    
    def download_video(self):
        """Tải xuống video"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập URL video YouTube")
            return
        
        save_path = self.save_path_input.text()
        if not save_path or not os.path.exists(save_path):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn thư mục lưu hợp lệ")
            return
        
        # Lấy loại tải xuống (video hoặc audio)
        download_type = self.download_type_combo.currentData()
        
        # Lấy chất lượng đã chọn
        quality_index = self.quality_combo.currentIndex()
        if quality_index >= 0:
            quality = self.quality_combo.itemData(quality_index) or self.quality_combo.itemText(quality_index)
        else:
            quality = "best" if download_type == "video" else "bestaudio"
        
        # Xử lý trường hợp đặc biệt cho "Chất lượng cao nhất (MP3)"
        if quality == "Chất lượng cao nhất (MP3)":
            quality = "bestaudio"
        
        # Hiển thị thanh tiến trình
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.download_info_label.setText("")
        self.download_info_label.setVisible(True)
        
        # Vô hiệu hóa nút tải xuống và phân tích trong khi đang tải
        self.download_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)  # Kích hoạt nút hủy
        
        # Xác định tốc độ tải xuống
        speed_limit = self.speed_combo.currentText()
        if speed_limit != "Không giới hạn":
            # Chuyển đổi từ MB/s sang B/s
            speed_mb = int(speed_limit.split(" ")[0])
            speed_bytes = speed_mb * 1024 * 1024
        else:
            speed_bytes = 0  # Không giới hạn
        
        # Lấy cài đặt từ tab cài đặt
        concurrent_downloads = self.concurrent_spinbox.value()
        buffer_size = self.buffer_spinbox.value() * 1024 * 1024  # Chuyển từ MB sang bytes
        retry_count = self.retry_spinbox.value()
        
        # Đường dẫn ffmpeg
        if self.auto_detect_ffmpeg_checkbox.isChecked():
            ffmpeg_path = None  # Tự động phát hiện
        else:
            ffmpeg_path = self.ffmpeg_path_input.text()
        
        # Sử dụng QThread để tải xuống
        self.download_thread = DownloadThread(
            self.downloader, url, save_path, download_type, quality, speed_bytes,
            concurrent_downloads, buffer_size, retry_count, ffmpeg_path
        )
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.error_signal.connect(self.on_download_error)
        self.download_thread.start()
        
        self.status_label.setText("Đang tải xuống...")
    
    def update_progress(self, percent, downloaded, total, speed):
        """Cập nhật thanh tiến trình và thông tin tải xuống"""
        current_time = time.time()
        
        # Tính lại phần trăm dựa trên dung lượng đã tải và tổng dung lượng
        # để đảm bảo tính nhất quán
        if total > 0 and downloaded > 0:
            calculated_percent = min(int(downloaded * 100 / total), 100)
            # Nếu phần trăm tính toán khác với phần trăm nhận được, ưu tiên phần trăm tính toán
            if abs(calculated_percent - percent) > 5:  # Nếu chênh lệch > 5%
                print(f"Điều chỉnh phần trăm: {percent}% -> {calculated_percent}% (Đã tải: {downloaded}/{total})")
                percent = calculated_percent
        
        # Cập nhật thanh tiến trình với giá trị phần trăm chính xác
        self.progress_bar.setValue(percent)
        
        # Tính tốc độ tải xuống nếu không được cung cấp hoặc không hợp lệ
        calculated_speed = 0
        if self.last_time > 0 and current_time > self.last_time:
            time_diff = current_time - self.last_time
            if time_diff > 0:
                bytes_diff = downloaded - self.last_downloaded
                if bytes_diff > 0:
                    calculated_speed = bytes_diff / time_diff
        
        # Sử dụng tốc độ tính toán nếu tốc độ từ yt-dlp không hợp lệ
        if speed <= 0 or speed > 100 * 1024 * 1024:  # Nếu tốc độ <= 0 hoặc > 100MB/s
            speed = calculated_speed
        
        # Thêm tốc độ hiện tại vào lịch sử nếu hợp lệ
        if speed > 0:
            # Loại bỏ các giá trị bất thường (quá cao hoặc quá thấp)
            if len(self.speed_history) > 0:
                avg = sum(self.speed_history) / len(self.speed_history)
                # Chỉ thêm vào nếu tốc độ không chênh lệch quá 300% so với trung bình
                if speed < avg * 3 and speed > avg * 0.3:
                    self.speed_history.append(speed)
            else:
                self.speed_history.append(speed)
            
            # Giới hạn kích thước lịch sử
            if len(self.speed_history) > self.speed_history_max_size:
                self.speed_history.pop(0)
        
        # Chuyển đổi các giá trị sang định dạng dễ đọc
        def format_size(size_bytes):
            if size_bytes <= 0:
                return "0 B"
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024
                i += 1
            return f"{size_bytes:.2f} {size_names[i]}"
        
        downloaded_str = format_size(downloaded)
        
        if total > 0:
            total_str = format_size(total)
            info_text = f"Đã tải: {downloaded_str} / {total_str}"
        else:
            info_text = f"Đã tải: {downloaded_str}"
        
        # Chỉ cập nhật hiển thị tốc độ sau một khoảng thời gian nhất định
        # hoặc khi có sự thay đổi đáng kể
        should_update_speed = False
        
        # Kiểm tra xem đã đến thời gian cập nhật chưa
        if current_time - self.last_speed_update_time >= self.speed_update_interval:
            should_update_speed = True
        
        if should_update_speed and len(self.speed_history) > 0:
            # Tính trung bình tốc độ để làm mượt, loại bỏ giá trị cao nhất và thấp nhất
            if len(self.speed_history) > 2:
                sorted_speeds = sorted(self.speed_history)
                # Loại bỏ giá trị cao nhất và thấp nhất
                filtered_speeds = sorted_speeds[1:-1]
                avg_speed = sum(filtered_speeds) / len(filtered_speeds)
            else:
                avg_speed = sum(self.speed_history) / len(self.speed_history)
            
            # Làm tròn tốc độ để giảm sự thay đổi nhỏ
            # Làm tròn đến KB gần nhất nếu < 1MB/s, đến 0.1MB gần nhất nếu >= 1MB/s
            if avg_speed < 1024 * 1024:  # < 1MB/s
                rounded_speed = round(avg_speed / 1024) * 1024  # Làm tròn đến KB gần nhất
            else:  # >= 1MB/s
                rounded_speed = round(avg_speed / (102.4 * 1024)) * (102.4 * 1024)  # Làm tròn đến 0.1MB gần nhất
            
            self.last_displayed_speed = rounded_speed
            self.last_speed_update_time = current_time
        
        # Hiển thị tốc độ tải xuống
        if self.last_displayed_speed > 0:
            speed_str = format_size(self.last_displayed_speed)
            info_text += f" | Tốc độ: {speed_str}/s"
        
        self.download_info_label.setText(info_text)
        
        # Lưu giá trị hiện tại để tính toán lần sau
        self.last_downloaded = downloaded
        self.last_time = current_time
        
        # Đảm bảo UI được cập nhật ngay lập tức
        self.progress_bar.repaint()
        self.download_info_label.repaint()
        QApplication.processEvents()  # Xử lý tất cả các sự kiện đang chờ
    
    def on_download_finished(self, message):
        """Xử lý khi tải xuống hoàn tất"""
        # Không cần đặt lại giá trị 100% vì nó đã được cập nhật trong quá trình tải xuống
        # self.progress_bar.setValue(100)
        
        self.status_label.setText(message)
        self.download_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)  # Vô hiệu hóa nút hủy
        
        # Hiển thị thông báo hoàn tất nếu được bật
        if self.show_notification_checkbox.isChecked():
            QMessageBox.information(self, "Hoàn tất", "Tải xuống đã hoàn tất!")
        
        # Tự động mở thư mục sau khi tải xuống nếu được bật
        if self.open_folder_checkbox.isChecked():
            save_path = self.save_path_input.text()
            if os.path.exists(save_path):
                if os.name == 'nt':  # Windows
                    os.startfile(save_path)
                elif os.name == 'posix':  # macOS, Linux
                    subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', save_path])
    
    def on_download_error(self, error_message):
        """Xử lý khi có lỗi tải xuống"""
        self.progress_bar.setVisible(False)
        self.download_info_label.setVisible(False)
        self.status_label.setText("Có lỗi xảy ra")
        self.download_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)  # Vô hiệu hóa nút hủy
        
        # Nếu không phải là thông báo hủy, hiển thị lỗi
        if error_message != "Đã hủy tải xuống":
            QMessageBox.critical(self, "Lỗi", error_message)
        else:
            self.status_label.setText(error_message)

    def cancel_download(self):
        """Hủy quá trình tải xuống"""
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.cancel_download()
            self.status_label.setText("Đang hủy tải xuống...")
            self.cancel_btn.setEnabled(False)

    def reset_progress_ui(self):
        """Đặt lại giao diện tiến trình"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.download_info_label.setVisible(False)
        self.download_info_label.setText("")
        self.last_downloaded = 0
        self.last_time = 0
        self.speed_history = []  # Đặt lại lịch sử tốc độ
        self.last_displayed_speed = 0  # Đặt lại tốc độ hiển thị cuối cùng
        self.last_speed_update_time = 0  # Đặt lại thời điểm cập nhật tốc độ cuối cùng

    def setup_settings_tab(self, tab):
        """Thiết lập giao diện cho tab cài đặt"""
        # Layout chính cho tab
        tab_layout = QVBoxLayout(tab)
        
        # Nhóm cài đặt tải xuống
        download_settings_group = QGroupBox("Cài đặt tải xuống")
        download_settings_layout = QVBoxLayout(download_settings_group)
        
        # Số lượng tải xuống đồng thời
        concurrent_layout = QHBoxLayout()
        concurrent_label = QLabel("Số lượng tải xuống đồng thời:")
        self.concurrent_spinbox = QSpinBox()
        self.concurrent_spinbox.setMinimum(1)
        self.concurrent_spinbox.setMaximum(16)
        self.concurrent_spinbox.setValue(8)  # Giá trị mặc định
        concurrent_layout.addWidget(concurrent_label)
        concurrent_layout.addWidget(self.concurrent_spinbox)
        concurrent_layout.addStretch()
        
        # Kích thước buffer
        buffer_layout = QHBoxLayout()
        buffer_label = QLabel("Kích thước buffer (MB):")
        self.buffer_spinbox = QSpinBox()
        self.buffer_spinbox.setMinimum(1)
        self.buffer_spinbox.setMaximum(64)
        self.buffer_spinbox.setValue(16)  # Giá trị mặc định
        buffer_layout.addWidget(buffer_label)
        buffer_layout.addWidget(self.buffer_spinbox)
        buffer_layout.addStretch()
        
        # Số lần thử lại
        retry_layout = QHBoxLayout()
        retry_label = QLabel("Số lần thử lại:")
        self.retry_spinbox = QSpinBox()
        self.retry_spinbox.setMinimum(1)
        self.retry_spinbox.setMaximum(20)
        self.retry_spinbox.setValue(10)  # Giá trị mặc định
        retry_layout.addWidget(retry_label)
        retry_layout.addWidget(self.retry_spinbox)
        retry_layout.addStretch()
        
        download_settings_layout.addLayout(concurrent_layout)
        download_settings_layout.addLayout(buffer_layout)
        download_settings_layout.addLayout(retry_layout)
        
        # Nhóm cài đặt giao diện
        ui_settings_group = QGroupBox("Cài đặt giao diện")
        ui_settings_layout = QVBoxLayout(ui_settings_group)
        
        # Hiển thị thông báo khi tải xuống hoàn tất
        self.show_notification_checkbox = QCheckBox("Hiển thị thông báo khi tải xuống hoàn tất")
        self.show_notification_checkbox.setChecked(True)
        
        # Tự động mở thư mục sau khi tải xuống
        self.open_folder_checkbox = QCheckBox("Tự động mở thư mục sau khi tải xuống")
        self.open_folder_checkbox.setChecked(False)
        
        # Lưu đường dẫn tải xuống cuối cùng
        self.save_last_path_checkbox = QCheckBox("Lưu đường dẫn tải xuống cuối cùng")
        self.save_last_path_checkbox.setChecked(True)
        
        # Tần suất cập nhật tốc độ
        speed_update_layout = QHBoxLayout()
        speed_update_label = QLabel("Tần suất cập nhật tốc độ (giây):")
        self.speed_update_spinbox = QSpinBox()
        self.speed_update_spinbox.setMinimum(1)
        self.speed_update_spinbox.setMaximum(5)
        self.speed_update_spinbox.setValue(1)  # Giá trị mặc định
        speed_update_layout.addWidget(speed_update_label)
        speed_update_layout.addWidget(self.speed_update_spinbox)
        speed_update_layout.addStretch()
        
        ui_settings_layout.addWidget(self.show_notification_checkbox)
        ui_settings_layout.addWidget(self.open_folder_checkbox)
        ui_settings_layout.addWidget(self.save_last_path_checkbox)
        ui_settings_layout.addLayout(speed_update_layout)
        
        # Nhóm cài đặt ffmpeg
        ffmpeg_settings_group = QGroupBox("Cài đặt FFmpeg")
        ffmpeg_settings_layout = QVBoxLayout(ffmpeg_settings_group)
        
        # Đường dẫn đến ffmpeg
        ffmpeg_path_layout = QHBoxLayout()
        ffmpeg_path_label = QLabel("Đường dẫn FFmpeg:")
        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_path_input.setPlaceholderText("Tự động phát hiện")
        self.browse_ffmpeg_btn = QPushButton("Duyệt...")
        self.browse_ffmpeg_btn.clicked.connect(self.browse_ffmpeg_location)
        ffmpeg_path_layout.addWidget(ffmpeg_path_label)
        ffmpeg_path_layout.addWidget(self.ffmpeg_path_input)
        ffmpeg_path_layout.addWidget(self.browse_ffmpeg_btn)
        
        # Tự động phát hiện ffmpeg
        self.auto_detect_ffmpeg_checkbox = QCheckBox("Tự động phát hiện FFmpeg")
        self.auto_detect_ffmpeg_checkbox.setChecked(True)
        self.auto_detect_ffmpeg_checkbox.toggled.connect(self.toggle_ffmpeg_path)
        
        ffmpeg_settings_layout.addLayout(ffmpeg_path_layout)
        ffmpeg_settings_layout.addWidget(self.auto_detect_ffmpeg_checkbox)
        
        # Nút lưu cài đặt
        save_settings_btn = QPushButton("Lưu cài đặt")
        save_settings_btn.clicked.connect(self.save_settings)
        save_settings_btn.setMinimumWidth(120)
        save_settings_btn.setMinimumHeight(40)
        
        # Thêm tất cả vào layout chính
        tab_layout.addWidget(download_settings_group)
        tab_layout.addWidget(ui_settings_group)
        tab_layout.addWidget(ffmpeg_settings_group)
        tab_layout.addStretch()
        
        # Thêm nút lưu cài đặt vào layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_settings_btn)
        tab_layout.addLayout(button_layout)
        
        # Khởi tạo cài đặt
        self.load_settings()
        self.toggle_ffmpeg_path()

    def toggle_ffmpeg_path(self):
        """Bật/tắt trường nhập đường dẫn ffmpeg"""
        self.ffmpeg_path_input.setEnabled(not self.auto_detect_ffmpeg_checkbox.isChecked())
        self.browse_ffmpeg_btn.setEnabled(not self.auto_detect_ffmpeg_checkbox.isChecked())

    def browse_ffmpeg_location(self):
        """Chọn đường dẫn đến ffmpeg"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn FFmpeg", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.ffmpeg_path_input.setText(file_path)

    def save_settings(self):
        """Lưu cài đặt người dùng"""
        # Lưu cài đặt vào file cấu hình
        import json
        settings = {
            "concurrent_downloads": self.concurrent_spinbox.value(),
            "buffer_size": self.buffer_spinbox.value(),
            "retry_count": self.retry_spinbox.value(),
            "show_notification": self.show_notification_checkbox.isChecked(),
            "open_folder_after_download": self.open_folder_checkbox.isChecked(),
            "save_last_path": self.save_last_path_checkbox.isChecked(),
            "auto_detect_ffmpeg": self.auto_detect_ffmpeg_checkbox.isChecked(),
            "ffmpeg_path": self.ffmpeg_path_input.text(),
            "last_save_path": self.save_path_input.text(),
            "speed_update_interval": self.speed_update_spinbox.value()
        }
        
        try:
            config_dir = os.path.join(os.path.expanduser('~'), '.lappytube')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config_file = os.path.join(config_dir, 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt thành công!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu cài đặt: {str(e)}")

    def load_settings(self):
        """Tải cài đặt người dùng"""
        import json
        config_file = os.path.join(os.path.expanduser('~'), '.lappytube', 'config.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Áp dụng cài đặt
                self.concurrent_spinbox.setValue(settings.get("concurrent_downloads", 8))
                self.buffer_spinbox.setValue(settings.get("buffer_size", 16))
                self.retry_spinbox.setValue(settings.get("retry_count", 10))
                self.show_notification_checkbox.setChecked(settings.get("show_notification", True))
                self.open_folder_checkbox.setChecked(settings.get("open_folder_after_download", False))
                self.save_last_path_checkbox.setChecked(settings.get("save_last_path", True))
                self.auto_detect_ffmpeg_checkbox.setChecked(settings.get("auto_detect_ffmpeg", True))
                self.ffmpeg_path_input.setText(settings.get("ffmpeg_path", ""))
                
                # Nếu lưu đường dẫn cuối cùng, áp dụng nó
                if settings.get("save_last_path", True) and "last_save_path" in settings:
                    self.save_path_input.setText(settings.get("last_save_path"))
                
                # Cập nhật tần suất cập nhật tốc độ
                self.speed_update_spinbox.setValue(settings.get("speed_update_interval", 1))
                self.speed_update_interval = float(self.speed_update_spinbox.value())
            except Exception as e:
                print(f"Lỗi khi tải cài đặt: {str(e)}")

    def on_download_type_changed(self, index):
        """Xử lý khi người dùng thay đổi loại tải xuống"""
        download_type = self.download_type_combo.currentData()
        
        # Nếu đã phân tích video, cập nhật danh sách chất lượng
        if hasattr(self, 'video_info') and self.video_info:
            self.update_quality_options(self.video_info, download_type)

    def update_quality_options(self, video_info, download_type=None):
        """Cập nhật các tùy chọn chất lượng dựa trên thông tin video"""
        if download_type is None:
            download_type = self.download_type_combo.currentData()
        
        self.quality_combo.clear()
        
        if download_type == "video":
            # Lọc ra các tùy chọn video
            video_qualities = [q for q in video_info['qualities'] if not q.startswith('0kbps') and not 'kbps' in q]
            if video_qualities:
                for quality in video_qualities:
                    self.quality_combo.addItem(quality)
                # Thêm tùy chọn "Tốt nhất"
                self.quality_combo.addItem("Chất lượng cao nhất", "best")
                # Chọn chất lượng cao nhất theo mặc định
                self.quality_combo.setCurrentIndex(self.quality_combo.count() - 1)
        else:  # audio
            # Lọc ra các tùy chọn audio
            audio_qualities = [q for q in video_info['qualities'] if 'kbps' in q]
            
            # Ưu tiên hiển thị các tùy chọn MP3 trước
            mp3_qualities = [q for q in audio_qualities if 'mp3' in q]
            other_audio_qualities = [q for q in audio_qualities if 'mp3' not in q]
            
            # Sắp xếp theo bitrate
            def get_bitrate(quality_str):
                try:
                    if 'kbps' in quality_str:
                        return float(quality_str.split('kbps')[0])
                    return 0
                except:
                    return 0
            
            mp3_qualities.sort(key=get_bitrate)
            other_audio_qualities.sort(key=get_bitrate)
            
            # Kết hợp lại, đặt MP3 lên đầu
            sorted_audio_qualities = mp3_qualities + other_audio_qualities
            
            if sorted_audio_qualities:
                for quality in sorted_audio_qualities:
                    self.quality_combo.addItem(quality)
                # Thêm tùy chọn "Tốt nhất"
                self.quality_combo.addItem("Chất lượng cao nhất (MP3)", "bestaudio")
                # Chọn chất lượng cao nhất theo mặc định
                self.quality_combo.setCurrentIndex(self.quality_combo.count() - 1)
            else:
                # Nếu không có tùy chọn audio cụ thể, thêm tùy chọn mặc định
                self.quality_combo.addItem("Chất lượng cao nhất (MP3)", "bestaudio")
        
        self.quality_combo.setEnabled(True)

class AnalyzeThread(QThread):
    """Thread xử lý phân tích video"""
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, downloader, url):
        super().__init__()
        self.downloader = downloader
        self.url = url
        
    def run(self):
        try:
            video_info = self.downloader.get_video_info(self.url)
            self.finished_signal.emit(video_info)
        except Exception as e:
            self.error_signal.emit(str(e)) 