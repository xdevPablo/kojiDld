import yt_dlp
import threading
import os
import platform
import subprocess
import imageio_ffmpeg
from typing import Any
import socket
import urllib.request
from urllib.parse import urlparse

class YoutubeDownloaderCore:
    def __init__(self, on_status_change, on_progress_update, on_download_complete, on_analysis_complete):
        self.on_status = on_status_change
        self.on_progress = on_progress_update
        self.on_complete = on_download_complete
        self.on_analysis = on_analysis_complete
        
        self.download_path = os.path.join(os.getcwd(), "downloads")
        os.makedirs(self.download_path, exist_ok=True)
        
        # Timeout global rápido para não travar o app em redes ruins
        socket.setdefaulttimeout(3.0)

    def get_ffmpeg_path(self):
        return imageio_ffmpeg.get_ffmpeg_exe()

    def open_download_folder(self):
        try:
            if platform.system() == "Windows":
                os.startfile(self.download_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", self.download_path])
            else:
                subprocess.Popen(["xdg-open", self.download_path])
        except Exception as e:
            print(f"Error opening folder: {e}")

    # --- BATCH DOWNLOAD LOGIC ---
    def start_download(self, urls, quality, format_type):
        threading.Thread(target=self._download_worker, args=(urls, quality, format_type), daemon=True).start()

    def _download_worker(self, urls, quality, format_type):
        try:
            ydl_opts: dict[str, Any] = {
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'noprogress': True,
                'ffmpeg_location': self.get_ffmpeg_path(),
            }

            if format_type == "Audio (MP3)":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }, {'key': 'FFmpegMetadata', 'add_metadata': True}],
                })
            else:
                format_map = {
                    "High (Default)": 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
                    "Medium (720p)": 'bestvideo[height<=720]+bestaudio/best',
                    "Low (Eco)": 'worst'
                }
                ydl_opts.update({
                    'format': format_map.get(quality, 'best'),
                    'merge_output_format': 'mp4',
                    'postprocessor_args': {'merger': ['-c:v', 'copy', '-c:a', 'aac']},
                    'postprocessors': [{'key': 'FFmpegMetadata', 'add_metadata': True}],
                })

            total_items = len(urls)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                for i, url in enumerate(urls):
                    self.on_status(f"Starting extraction for item {i+1} of {total_items}...", False)
                    try:
                        ydl.download([url])
                    except Exception as item_err:
                        print(f"Item error {url}: {item_err}")
                        continue 
            
            self.on_complete()

        except Exception as e:
            error_msg = str(e).split('\n')[0] 
            self.on_status(f"CRITICAL ERROR: {error_msg[:60]}...", True)

    def _progress_hook(self, d):
        try:
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                
                percent = (downloaded / total_bytes) if total_bytes > 0 else 0.0
                size_str = f"{total_bytes / (1024**2):.2f} MB" if total_bytes > 0 else "-- MB"
                
                # Coleta dados extras de ETA e Velocidade
                eta = d.get('_eta_str', 'N/A')
                speed = d.get('_speed_str', '-- KB/s')
                
                self.on_progress(percent, eta, size_str, speed)
                
            elif d['status'] == 'finished':
                self.on_progress(1.0, "00:00", "Complete", "0 MB/s")
                self.on_status("Finalizing and optimizing current file...")
        except Exception:
            pass 

    # --- ADVANCED SCANNER LOGIC ---
    def start_analysis(self, url):
        threading.Thread(target=self._scan_worker, args=(url,), daemon=True).start()

    def _scan_worker(self, url):
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc or parsed_url.path
            if not domain:
                raise ValueError("Domain not identified in the URL.")

            # 1. DNS Resolution
            try:
                ip_address = socket.gethostbyname(domain)
            except socket.gaierror:
                ip_address = "Masked IP / DNS Failure"

            protocol = parsed_url.scheme.upper() if parsed_url.scheme else "UNKNOWN"
            is_secure = protocol == "HTTPS"

            # 2. Server Architecture Probe (Ping rápido no servidor)
            server_software = "Unknown"
            try:
                # Disfarça o bot como um navegador comum
                req = urllib.request.Request(f"https://{domain}", method="HEAD", headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3.0) as response:
                    server_software = response.headers.get('Server', 'Hidden (Secure Firewall)')
            except Exception:
                server_software = "Protected / CDN Routed"

            scan_data = {
                "domain": domain,
                "ip": ip_address,
                "protocol": protocol,
                "server": server_software,
                "status": "SECURE (SSL/TLS)" if is_secure else "VULNERABLE (UNENCRYPTED)",
                "color": "#10B981" if is_secure else "#F59E0B"
            }
            self.on_analysis(scan_data)
        except Exception as e:
            self.on_status(f"Scan Error: Connection failure or invalid link.", True)