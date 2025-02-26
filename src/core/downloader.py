import os
import yt_dlp
import sys
import subprocess

class YouTubeDownloader:
    """Lớp xử lý tải xuống video từ YouTube"""
    
    def get_video_info(self, url):
        """
        Lấy thông tin video từ URL
        
        Args:
            url (str): URL của video YouTube
            
        Returns:
            dict: Thông tin video bao gồm tiêu đề, tác giả, thời lượng và danh sách chất lượng
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'format': 'best',
                'listformats': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            # Lấy danh sách chất lượng có sẵn
            qualities = []
            audio_qualities = []
            
            # Danh sách các độ phân giải phổ biến để kiểm tra
            common_resolutions = [144, 240, 360, 480, 720, 1080, 1440, 2160, 4320]
            available_resolutions = set()
            
            # In ra tất cả các định dạng để kiểm tra
            print("Tất cả các định dạng có sẵn:")
            for format in info.get('formats', []):
                format_id = format.get('format_id', '')
                ext = format.get('ext', '')
                vcodec = format.get('vcodec', 'none')
                acodec = format.get('acodec', 'none')
                height = format.get('height')
                
                print(f"ID: {format_id}, Ext: {ext}, Height: {height}, VCodec: {vcodec}, ACodec: {acodec}")
                
                # Kiểm tra nếu là video (có thể chỉ có video hoặc video+audio)
                if vcodec != 'none' and vcodec != 'images':
                    if height:
                        available_resolutions.add(height)
                        if acodec != 'none':
                            qualities.append(f"{height}p ({ext})")
                        else:
                            qualities.append(f"{height}p (video only, {ext})")
                # Kiểm tra nếu chỉ là audio
                elif acodec != 'none' and (vcodec == 'none' or vcodec == 'images'):
                    abr = format.get('abr')
                    if abr:
                        audio_qualities.append(f"{abr}kbps ({ext})")
            
            # Thêm các độ phân giải phổ biến vào danh sách nếu có sẵn
            for res in common_resolutions:
                if res in available_resolutions:
                    qualities.append(f"{res}p (best)")
            
            # Thêm tùy chọn MP3 cho audio
            if len(audio_qualities) > 0:
                # Lấy bitrate cao nhất từ các định dạng audio có sẵn
                max_bitrate = 0
                for quality in audio_qualities:
                    try:
                        bitrate = float(quality.split('kbps')[0])
                        max_bitrate = max(max_bitrate, bitrate)
                    except:
                        pass
                
                # Thêm các tùy chọn MP3 với các bitrate phổ biến
                mp3_bitrates = [64, 128, 192, 256, 320]
                for bitrate in mp3_bitrates:
                    if bitrate <= max_bitrate or max_bitrate == 0:
                        audio_qualities.append(f"{bitrate}kbps (mp3)")
            
            # Loại bỏ các phần tử trùng lặp
            qualities = list(set(qualities))
            audio_qualities = list(set(audio_qualities))
            
            # Sắp xếp theo độ phân giải
            def get_resolution(quality_str):
                try:
                    if 'p' in quality_str:
                        return float(quality_str.split('p')[0])
                    return 0
                except:
                    return 0
            
            def get_bitrate(quality_str):
                try:
                    if 'kbps' in quality_str:
                        return float(quality_str.split('kbps')[0])
                    return 0
                except:
                    return 0
            
            qualities.sort(key=get_resolution)
            audio_qualities.sort(key=get_bitrate)
            
            print("Danh sách chất lượng sau khi xử lý:")
            for q in qualities:
                print(f"- {q}")
            for q in audio_qualities:
                print(f"- {q}")
            
            # Kết hợp danh sách chất lượng, đảm bảo audio được đánh dấu rõ ràng
            all_qualities = qualities + audio_qualities
            
            return {
                'title': info.get('title', 'Unknown'),
                'author': info.get('uploader', 'Unknown'),
                'length': info.get('duration', 0),
                'qualities': all_qualities
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi lấy thông tin video: {str(e)}")
    
    def download(self, url, save_path, download_type="video", quality="highest", progress_callback=None, 
                 speed_limit=0, concurrent_downloads=8, buffer_size=16*1024*1024, retry_count=10, ffmpeg_path=None):
        try:
            # Xác định đường dẫn đến ffmpeg
            if ffmpeg_path is None:
                if getattr(sys, 'frozen', False):
                    # Nếu ứng dụng đã được đóng gói bằng PyInstaller
                    base_path = sys._MEIPASS
                else:
                    # Nếu đang chạy từ mã nguồn
                    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                
                ffmpeg_path = os.path.join(base_path, 'assets', 'bin', 'ffmpeg.exe')
                
                # Kiểm tra xem ffmpeg có tồn tại không
                ffmpeg_exists = os.path.exists(ffmpeg_path)
                if not ffmpeg_exists:
                    print(f"Cảnh báo: Không tìm thấy ffmpeg tại {ffmpeg_path}")
                    # Thử tìm ffmpeg trong PATH
                    import shutil
                    ffmpeg_in_path = shutil.which('ffmpeg')
                    if ffmpeg_in_path:
                        ffmpeg_path = ffmpeg_in_path
                        ffmpeg_exists = True
                        print(f"Đã tìm thấy ffmpeg trong PATH: {ffmpeg_path}")
            else:
                ffmpeg_exists = os.path.exists(ffmpeg_path)
            
            # Thêm tùy chọn để chỉ định định dạng đầu ra là mp4
            if download_type == "audio":
                # Nếu chỉ tải audio, sử dụng định dạng mp3
                ext = 'mp3'
                format_str = 'bestaudio/best'
                
                # Xác định bitrate cho MP3 nếu được chỉ định
                audio_quality = '192'  # Mặc định
                if 'kbps' in quality and 'mp3' in quality:
                    try:
                        # Trích xuất bitrate từ chuỗi chất lượng (ví dụ: "192kbps (mp3)")
                        audio_quality = quality.split('kbps')[0].strip()
                    except:
                        pass
                
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }]
            else:
                # Nếu tải video, sử dụng định dạng mp4
                ext = 'mp4'
                
                if quality == "highest":
                    if ffmpeg_exists:
                        # Chỉ định rõ ràng muốn mp4 cho video chất lượng cao
                        format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    else:
                        # Fallback nếu không có ffmpeg, chọn định dạng muxed cao nhất
                        ydl_opts_info = {'quiet': True, 'no_warnings': True, 'skip_download': True}
                        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                            info = ydl.extract_info(url, download=False)
                        muxed_formats = [(f.get('height'), f.get('format_id')) for f in info.get('formats', []) 
                                        if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                        muxed_formats.sort(reverse=True)
                        if muxed_formats:
                            _, format_str = muxed_formats[0]
                        else:
                            raise Exception("Không tìm thấy định dạng muxed.")
                else:
                    resolution = quality.split('p')[0] if 'p' in quality else '360'
                    if ffmpeg_exists:
                        # Chỉ định rõ ràng muốn mp4 cho video với độ phân giải cụ thể
                        format_str = f'bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best'
                    else:
                        # Fallback nếu không có ffmpeg, chọn định dạng muxed gần nhất
                        ydl_opts_info = {'quiet': True, 'no_warnings': True, 'skip_download': True}
                        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                            info = ydl.extract_info(url, download=False)
                        muxed_formats = [(f.get('height'), f.get('format_id')) for f in info.get('formats', []) 
                                        if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                        muxed_formats.sort(reverse=True)
                        selected_format = None
                        for height, fmt in muxed_formats:
                            if height <= int(resolution):
                                selected_format = fmt
                                break
                        if selected_format:
                            format_str = selected_format
                        else:
                            _, format_str = muxed_formats[0] if muxed_formats else '18'

                # Thêm postprocessor để chuyển đổi sang mp4 nếu cần
                postprocessors = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]

            # Cấu hình yt-dlp
            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'postprocessors': postprocessors,
                'buffersize': buffer_size,
                'concurrent_fragment_downloads': concurrent_downloads,
                'retries': retry_count,
                'fragment_retries': retry_count,
                'file_access_retries': retry_count,
                'extractor_retries': retry_count,
            }
            
            # Thêm giới hạn tốc độ nếu được chỉ định
            if speed_limit > 0:
                ydl_opts['ratelimit'] = speed_limit

            # Nếu có ffmpeg, sử dụng nó
            if ffmpeg_exists:
                ydl_opts['ffmpeg_location'] = ffmpeg_path

            # Thêm callback tiến trình với thông tin chi tiết hơn
            if progress_callback:
                # Thêm biến để lưu trữ tổng kích thước đã biết
                total_size = 0

                def my_hook(d):
                    if d['status'] == 'downloading':
                        nonlocal total_size
                        # Lấy thông tin về tổng kích thước và đã tải
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes', 0)
                        
                        # Nếu không có total_bytes, thử dùng total_bytes_estimate
                        if total == 0:
                            total = d.get('total_bytes_estimate', 0)
                        
                        # Lưu tổng kích thước đã biết để sử dụng cho các lần gọi tiếp theo
                        # Chỉ cập nhật nếu giá trị mới lớn hơn giá trị đã lưu
                        if total > 0:
                            if total_size == 0 or (total > total_size and total_size > 0):
                                total_size = total
                            else:
                                # Sử dụng giá trị đã lưu nếu giá trị mới nhỏ hơn
                                total = total_size
                        
                        # Tính phần trăm
                        if total > 0:
                            # Đảm bảo phần trăm được tính chính xác dựa trên dung lượng đã tải và tổng dung lượng
                            percent = min(int(downloaded * 100 / total), 100)  # Đảm bảo không vượt quá 100%
                            print(f"Tính phần trăm: {downloaded}/{total} = {percent}%")
                        else:
                            # Nếu không có thông tin về tổng kích thước, dùng _percent_str
                            p = d.get('_percent_str', '0%')
                            p = p.replace('%', '')
                            try:
                                percent = int(float(p))
                            except:
                                percent = 0
                        
                        # Truyền thông tin chi tiết về tiến trình
                        speed = d.get('speed', 0)
                        # In ra để debug
                        print(f"Raw speed from yt-dlp: {speed}")
                        # Đảm bảo tốc độ là hợp lý và không phải None
                        if speed is None:
                            speed = 0
                        elif speed > 100 * 1024 * 1024:  # > 100MB/s
                            # Có thể là lỗi đơn vị, điều chỉnh lại
                            speed = speed / 1024  # Chuyển về KB/s
                        
                        # Gọi callback và kiểm tra kết quả
                        # Nếu callback trả về False, dừng tải xuống
                        if progress_callback(percent, downloaded, total, speed) is False:
                            raise Exception("Đã hủy tải xuống")
                        
                    elif d['status'] == 'finished':
                        # Khi tải xong, gửi thông báo 100%
                        progress_callback(100, 0, 0, 0)
                
                ydl_opts['progress_hooks'] = [my_hook]

            # Tải xuống
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            # Chuyển đổi sang mp4 nếu cần
            if ffmpeg_exists and download_type == "video" and not file_path.lower().endswith('.mp4'):
                file_path = self.convert_to_mp4(file_path, ffmpeg_path)

            return file_path

        except Exception as e:
            raise Exception(f"Lỗi khi tải xuống video: {str(e)}")

    def convert_to_mp4(self, input_file, ffmpeg_path):
        """
        Chuyển đổi file video sang định dạng mp4
        
        Args:
            input_file (str): Đường dẫn đến file đầu vào
            ffmpeg_path (str): Đường dẫn đến ffmpeg
            
        Returns:
            str: Đường dẫn đến file mp4 đã chuyển đổi
        """
        try:
            # Tạo tên file đầu ra
            output_file = os.path.splitext(input_file)[0] + '.mp4'
            
            # Nếu file đầu vào đã là mp4, không cần chuyển đổi
            if input_file.lower().endswith('.mp4'):
                return input_file
            
            # Chạy lệnh ffmpeg để chuyển đổi
            subprocess.run([
                ffmpeg_path,
                '-i', input_file,  # File đầu vào
                '-c:v', 'copy',    # Giữ nguyên codec video
                '-c:a', 'aac',     # Chuyển đổi audio sang AAC (phù hợp với MP4)
                '-strict', 'experimental',
                output_file        # File đầu ra
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Xóa file gốc sau khi chuyển đổi thành công
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                os.remove(input_file)
                return output_file
            else:
                return input_file
        except Exception as e:
            print(f"Lỗi khi chuyển đổi sang MP4: {e}")
            return input_file