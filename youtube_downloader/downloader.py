import re
import json
import os
import requests
from typing import Optional, List, Dict, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from .proxy_manager import ProxyManager, ProxyConfig
from tqdm import tqdm

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
            selected = next((f for f in formats if f['quality'] == quality and f['has_video'] and f['has_audio']), None)
            if not selected:
                selected = next((f for f in formats if quality in str(f['quality'])), None)
            if not selected:
                raise Exception(f"Quality {quality} not found")
        else:
            with_both = [f for f in formats if f['has_video'] and f['has_audio']]
            selected = with_both[0] if with_both else formats[0]

        headers = {
            'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11)',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Range': 'bytes=0-'
        }
        # Handle rate limiting during download
        retries = 3
        response = None
        
        for attempt in range(retries):
            try:
                if self.proxy_manager:
                    maybe = self.proxy_manager.get_proxy()
                    if maybe and maybe is not self._active_proxy:
                        self._apply_proxy(maybe)
                current_proxy = self._active_proxy
                
                response = self.session.get(selected['url'], headers=headers, stream=True, timeout=60)
               
                if response.status_code == 429:
                    if self.proxy_manager and attempt < retries - 1:
                        print("\nâš  Rate limited during download. Rotating proxy...")
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
                    print(f"\nâš  Download failed ({e.__class__.__name__}). Retrying with new proxy...")
                    if current_proxy:
                        self.proxy_manager.record_failure(current_proxy, e)
                    self._rotate_proxy()
                else:
                    raise 
        
        if response is None:
            raise Exception("Failed to get a successful response after all retries.")

        total_size = int(response.headers.get('content-length', 0))
        if total_size == 0: #
            total_size = int(selected.get('filesize', 0))

        file_desc = f"{output_file} [{selected.get('quality', 'unknown')}]"

        with open(output_file, 'wb') as f, tqdm(
            desc=file_desc,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}, {elapsed}<{remaining}]'
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
        print(f"✔ Downloaded to {output_file}")
        return output_file


class PlaylistDownloader:
    def __init__(self, playlist_url: str, proxy_manager: Optional[ProxyManager] = None, concurrency: int = 3):
        """
        Initialize PlaylistDownloader.
        
        Args:
            playlist_url: URL of the YouTube playlist
            proxy_manager: Optional ProxyManager for proxy support
            concurrency: Number of parallel downloads (default: 3)
        """
        self.playlist_url = playlist_url
        self.playlist_id = self._extract_playlist_id(playlist_url)
        self.proxy_manager = proxy_manager
        self.concurrency = concurrency
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
        
        self.videos = []
        
    def _setup_proxy(self):
        """Setup proxy for the session."""
        if not self.proxy_manager:
            return
        
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            self._apply_proxy(proxy)
    
    def _apply_proxy(self, proxy: ProxyConfig):
        """Apply a proxy configuration to the session."""
        proxy_dict = proxy.to_dict()
        
        # Handle SOCKS proxies using requests[socks]
        if proxy.scheme in ('socks4', 'socks5'):
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
            from requests.auth import HTTPProxyAuth
            self.session.auth = HTTPProxyAuth(proxy.username, proxy.password)
        
        self.session.proxies = proxy_dict
    
    def _extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from URL."""
        patterns = [
            r'list=([a-zA-Z0-9_-]+)',
            r'/playlist\?list=([a-zA-Z0-9_-]+)',
            r'^([a-zA-Z0-9_-]+)$'  # Direct ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid YouTube playlist URL")
    
    def _get_playlist_info(self) -> Dict:
        """Fetch playlist metadata from YouTube API."""
        api_url = "https://www.youtube.com/youtubei/v1/browse"
        
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
            "browseId": f"VL{self.playlist_id}"
        }
        
        try:
            response = self.session.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Try alternative endpoint
            return self._get_playlist_info_alternative()
    
    def _get_playlist_info_alternative(self) -> Dict:
        """Alternative method to get playlist info."""
        api_url = "https://www.youtube.com/youtubei/v1/browse"
        
        # Try with different browseId format
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.0",
                    "hl": "en",
                    "gl": "US"
                }
            },
            "browseId": f"VL{self.playlist_id}"
        }
        
        try:
            response = self.session.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to fetch playlist info: {e}")
    
    def _extract_videos_from_playlist_info(self, data: Dict) -> List[Dict]:
        """Extract video list from playlist response."""
        videos = []
        
        # Navigate through the response structure
        contents = data.get('contents', {})
        two_column_browser_renderer = contents.get('twoColumnBrowseResultsRenderer', {})
        tabs = two_column_browser_renderer.get('tabs', [])
        
        for tab in tabs:
            tab_renderer = tab.get('tabRenderer', {})
            content = tab_renderer.get('content', {})
            section_list_renderer = content.get('sectionListRenderer', {})
            items = section_list_renderer.get('contents', [])
            
            for item in items:
                item_section = item.get('itemSectionRenderer', {})
                playlist_video_list = item_section.get('contents', [])
                
                for playlist_video in playlist_video_list:
                    renderer = playlist_video.get('playlistVideoRenderer')
                    if renderer:
                        video_id = renderer.get('videoId')
                        title = renderer.get('title', {}).get('runs', [{}])[0].get('text', 'Unknown')
                        
                        if video_id:
                            videos.append({
                                'video_id': video_id,
                                'title': title,
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            })
        
        return videos
    
    def get_videos(self) -> List[Dict]:
        """
        Fetch all videos from the playlist.
        
        Returns:
            List of video dictionaries with video_id, title, and url
        """
        if self.videos:
            return self.videos
        
        print(f"Fetching playlist information...")
        data = self._get_playlist_info()
        self.videos = self._extract_videos_from_playlist_info(data)
        
        if not self.videos:
            raise Exception("No videos found in playlist or playlist is private/unavailable")
        
        print(f"Found {len(self.videos)} videos in playlist")
        return self.videos
    
    def download(self, output_dir: str = "./downloads", quality: Optional[str] = None, itag: Optional[int] = None, 
                 on_video_start: Optional[Callable] = None, on_video_complete: Optional[Callable] = None,
                 on_error: Optional[Callable] = None):
        """
        Download all videos from the playlist.
        
        Args:
            output_dir: Directory to save downloaded videos
            quality: Quality preference (e.g., '720p')
            itag: Specific itag to use
            on_video_start: Optional callback when video download starts
            on_video_complete: Optional callback when video download completes
            on_error: Optional callback when video download fails
            
        Returns:
            Dict with download statistics
        """
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get playlist videos
        videos = self.get_videos()
        
        if not videos:
            print("No videos to download")
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'failed_videos': []
            }
        
        # Download statistics
        stats = {
            'total': len(videos),
            'successful': 0,
            'failed': 0,
            'failed_videos': []
        }
        
        # Download videos in parallel
        print(f"\nDownloading {len(videos)} videos with concurrency={self.concurrency}...\n")
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Submit all download tasks
            future_to_video = {
                executor.submit(self._download_single_video, video, output_dir, quality, itag, 
                               on_video_start, on_video_complete): video
                for video in videos
            }
            
            # Create overall progress bar
            with tqdm(total=len(videos), desc="Overall Progress", unit="video") as overall_bar:
                # Process completed downloads
                for future in as_completed(future_to_video):
                    video = future_to_video[future]
                    try:
                        result = future.result()
                        if result:
                            stats['successful'] += 1
                        else:
                            stats['failed'] += 1
                            stats['failed_videos'].append(video)
                            if on_error:
                                on_error(video, None)
                    except Exception as e:
                        stats['failed'] += 1
                        stats['failed_videos'].append(video)
                        if on_error:
                            on_error(video, e)
                    
                    overall_bar.update(1)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Download Summary:")
        print(f"  Total videos: {stats['total']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Saved to: {output_dir}")
        if stats['failed_videos']:
            print(f"\n  Failed videos:")
            for video in stats['failed_videos']:
                print(f"    - {video.get('title', 'Unknown')}")
        print(f"{'='*60}\n")
        
        return stats
    
    def _download_single_video(self, video: Dict, output_dir: str, quality: Optional[str], 
                               itag: Optional[int], on_video_start: Optional[Callable],
                               on_video_complete: Optional[Callable]) -> bool:
        """Download a single video from the playlist."""
        try:
            if on_video_start:
                on_video_start(video)
            
            # Create downloader for this video
            downloader = YouTubeDownloader(video['url'], proxy_manager=self.proxy_manager)
            
            # Generate safe filename from title
            safe_title = "".join(c for c in video.get('title', 'video') if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:100]  # Limit length
            output_file = os.path.join(output_dir, f"{safe_title}.mp4")
            
            # Skip if file already exists (resume support)
            if os.path.exists(output_file):
                print(f"✓ Skipping {video.get('title', 'video')} (already exists)")
                if on_video_complete:
                    on_video_complete(video, output_file)
                return True
            
            # Download the video
            downloader.download(output_file, quality=quality, itag=itag)
            
            if on_video_complete:
                on_video_complete(video, output_file)
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to download {video.get('title', 'Unknown')}: {e}")
            return False