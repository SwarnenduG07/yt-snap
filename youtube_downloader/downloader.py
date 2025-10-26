import re
import json
import requests
from typing import Optional, List
from .proxy_manager import ProxyManager, ProxyConfig

class YouTubeDownloader:
    def __init__(self, url, proxy_manager: Optional[ProxyManager] = None):
        self.url = url
        self.video_id = self._extract_video_id(url)
        self.proxy_manager = proxy_manager
        self._active_proxy = None  # type: Optional[ProxyConfig]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/'
        })
        
        # Configure proxy for session if proxy manager is provided
        if self.proxy_manager:
            self._setup_proxy()
        
    def _setup_proxy(self):
        """Setup proxy for the session."""
        if not self.proxy_manager:
            return
        
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            self._apply_proxy(proxy)
    
    def _apply_proxy(self, proxy: ProxyConfig):
        """Apply a proxy configuration to the session."""
        self._active_proxy = proxy
        proxy_dict = proxy.to_dict()
        
        # Handle SOCKS proxies using requests[socks]
        if proxy.scheme in ('socks4', 'socks5'):
            # Convert to proper SOCKS URL format
            socks_version = 'socks4' if proxy.scheme == 'socks4' else 'socks5'
            auth = (
                f"{proxy.username}:{proxy.password}@"
                if (proxy.username and proxy.password)
                else (f"{proxy.username}@" if proxy.username else "")
            )
            proxy_url = f"{socks_version}://{auth}{proxy.host}:{proxy.port}"
            proxy_dict = {
                'http': proxy_url,
                'https': proxy_url
            }
        elif proxy.username and proxy.password:
            # For authenticated HTTP proxies, set up authentication
            from requests.auth import HTTPProxyAuth
            self.session.auth = HTTPProxyAuth(proxy.username, proxy.password)
        
        self.session.proxies = proxy_dict
    
    def _rotate_proxy(self):
        """Rotate to a new proxy."""
        if not self.proxy_manager:
            return
        
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            self._apply_proxy(proxy)
    
    def _extract_video_id(self, url):
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Invalid YouTube URL")
    
    def _get_video_info(self, retries: int = 3):
        api_url = "https://www.youtube.com/youtubei/v1/player"
        
        payload = {
            "context": {
                "client": {
                    "clientName": "ANDROID",
                    "clientVersion": "19.09.37",
                    "androidSdkVersion": 30,
                    "hl": "en",
                    "gl": "US"
                }
            },
            "videoId": self.video_id
        }
        
        for attempt in range(retries):
            try:
                # Refresh session proxy if manager rotated by time
                if self.proxy_manager:
                    maybe = self.proxy_manager.get_proxy()
                    if maybe and maybe is not self._active_proxy:
                        self._apply_proxy(maybe)
                # Record against the actual active proxy
                current_proxy = self._active_proxy
                
                response = self.session.post(api_url, json=payload, timeout=30)
                
                # Handle rate limiting
                if response.status_code == 429:
                    if self.proxy_manager:
                        print("⚠ Rate limited (429). Rotating proxy...")
                        if current_proxy:
                            self.proxy_manager.record_failure(
                                current_proxy,
                                Exception("429 Too Many Requests")
                            )
                        self._rotate_proxy()
                        if attempt < retries - 1:
                            continue
                    raise Exception("Rate limited by YouTube (429 Too Many Requests)")
                
                response.raise_for_status()
                
                # Record success if using proxies
                if self.proxy_manager and current_proxy:
                    self.proxy_manager.record_success(current_proxy)
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if self.proxy_manager and attempt < retries - 1:
                    print(f"⚠ Request failed. Rotating proxy... ({attempt + 1}/{retries})")
                    if current_proxy:
                        self.proxy_manager.record_failure(current_proxy, e)
                    self._rotate_proxy()
                else:
                    raise
        
        raise Exception("Failed to fetch video info after multiple attempts")
    
    def get_formats(self):
        data = self._get_video_info()
        
        if 'playabilityStatus' in data:
            status = data['playabilityStatus'].get('status')
            if status != 'OK':
                reason = data['playabilityStatus'].get('reason', 'Unknown error')
                raise Exception(f"Video not available: {reason}")
        
        formats = data.get('streamingData', {}).get('formats', []) + \
                  data.get('streamingData', {}).get('adaptiveFormats', [])
        
        video_formats = []
        for fmt in formats:
            if 'url' in fmt:
                video_formats.append({
                    'itag': fmt.get('itag'),
                    'quality': fmt.get('qualityLabel', fmt.get('quality')),
                    'mime': fmt.get('mimeType', '').split(';')[0],
                    'url': fmt['url'],
                    'has_video': 'video' in fmt.get('mimeType', ''),
                    'has_audio': 'audio' in fmt.get('mimeType', ''),
                    'filesize': fmt.get('contentLength', 0)
                })
        
        return video_formats
    
    def download(self, output_file='video.mp4', itag=None, quality=None):
        formats = self.get_formats()
        
        if not formats:
            raise Exception("No downloadable formats found")
        
        if itag:
            selected = next((f for f in formats if f['itag'] == itag), None)
            if not selected:
                raise Exception(f"Format with itag {itag} not found")
        elif quality:
            selected = next((f for f in formats if quality in str(f['quality'])), None)
            if not selected:
                raise Exception(f"Quality {quality} not found")
        else:
            with_both = [f for f in formats if f['has_video'] and f['has_audio']]
            selected = with_both[0] if with_both else formats[0]
        
        print(f"Downloading: {selected['quality']} - {selected['mime']}")
        if selected['filesize']:
            print(f"Size: {int(selected['filesize']) / (1024*1024):.2f} MB")
        
        headers = {
            'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11)',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Range': 'bytes=0-'
        }
        
        # Handle rate limiting during download
        retries = 3
        
        for attempt in range(retries):
            try:
                # Refresh session proxy if manager rotated by time
                if self.proxy_manager:
                    maybe = self.proxy_manager.get_proxy()
                    if maybe and maybe is not self._active_proxy:
                        self._apply_proxy(maybe)
                # Record against the actual active proxy
                current_proxy = self._active_proxy
                
                response = self.session.get(selected['url'], headers=headers, stream=True, timeout=60)
                
                # Check for rate limiting
                if response.status_code == 429:
                    if self.proxy_manager and attempt < retries - 1:
                        print("\n⚠ Rate limited during download. Rotating proxy...")
                        if current_proxy:
                            self.proxy_manager.record_failure(
                                current_proxy,
                                Exception("429 Too Many Requests")
                            )
                        self._rotate_proxy()
                        continue
                    response.raise_for_status()
                
                response.raise_for_status()
                
                if self.proxy_manager and current_proxy:
                    self.proxy_manager.record_success(current_proxy)
                
                break
                
            except requests.exceptions.RequestException as e:
                if self.proxy_manager and attempt < retries - 1:
                    print("\n⚠ Download failed. Retrying with new proxy...")
                    if current_proxy:
                        self.proxy_manager.record_failure(current_proxy, e)
                    self._rotate_proxy()
                else:
                    raise
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_file, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB)", end='', flush=True)
        
        print(f"\n✓ Downloaded to {output_file}")
        return output_file

