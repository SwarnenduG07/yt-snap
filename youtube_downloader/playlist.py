import re
import os
import json
import time
import sys
import threading
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
from .downloader import YouTubeDownloader

# Thread-safe print lock to prevent garbled output
print_lock = threading.Lock()


class PlaylistDownloader:
    """Downloads entire YouTube playlists with progress tracking and error handling."""
    
    def __init__(self, url: str):
        """
        Initialize playlist downloader.
        
        Args:
            url: YouTube playlist URL or playlist ID
        """
        self.url = url
        self.playlist_id = self._extract_playlist_id(url)
        
        # Network timeout for API requests (seconds)
        self.request_timeout = 15
        
        # Create session with proper headers for YouTube API
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/'
        })
        
        self._playlist_info = None
        self._video_list = None
        
    def _extract_playlist_id(self, url: str) -> str:
        """
        Extract playlist ID from URL or return if already an ID.
        
        Args:
            url: YouTube playlist URL or ID
            
        Returns:
            Playlist ID
            
        Raises:
            ValueError: If URL format is invalid
        """
        # Remove backslashes that might come from shell escaping
        url = url.replace('\\', '')
        
        patterns = [
            r'[?&]list=([a-zA-Z0-9_-]+)',  # ?list=... or &list=...
            r'^([a-zA-Z0-9_-]{24,})$'       # Direct playlist ID (at least 24 chars)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                playlist_id = match.group(1)
                # Basic validation - playlist IDs are typically 24+ characters
                if len(playlist_id) >= 13:  # Minimum reasonable length
                    return playlist_id
        
        raise ValueError(f"Invalid YouTube playlist URL or ID: {url}")
    
    def _get_playlist_info(self) -> Dict:
        """
        Fetch playlist metadata using YouTube innertube API.
        
        Returns:
            Dictionary containing playlist information
            
        Raises:
            Exception: If playlist is unavailable or private
        """
        if self._playlist_info:
            return self._playlist_info
            
        api_url = "https://www.youtube.com/youtubei/v1/browse"
        
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20231219.01.00",
                    "hl": "en",
                    "gl": "US"
                }
            },
            "browseId": f"VL{self.playlist_id}"
        }
        
        try:
            response = self.session.post(api_url, json=payload, timeout=self.request_timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch playlist info: {e}") from e
        except ValueError as e:
            raise RuntimeError("Failed to decode playlist info JSON") from e
        
        # Extract playlist metadata
        try:
            header = data.get('header', {})
            if 'playlistHeaderRenderer' in header:
                renderer = header['playlistHeaderRenderer']
            elif 'pageHeaderRenderer' in header:
                # Alternative structure
                renderer = header['pageHeaderRenderer']['content']['playlistHeaderRenderer']
            else:
                raise KeyError("Could not find playlist header")
                
            self._playlist_info = {
                'title': renderer.get('title', {}).get('simpleText', 'Unknown Playlist'),
                'video_count': self._extract_video_count(renderer),
                'author': self._extract_author(renderer)
            }
            
        except (KeyError, TypeError) as e:
            # Fallback for different API response structures
            self._playlist_info = {
                'title': 'Unknown Playlist',
                'video_count': 0,
                'author': 'Unknown'
            }
        
        return self._playlist_info
    
    def _extract_video_count(self, renderer: Dict) -> int:
        """Extract video count from playlist renderer."""
        try:
            # Try different possible locations for video count
            if 'numVideosText' in renderer:
                text = renderer['numVideosText'].get('runs', [{}])[0].get('text', '0')
            elif 'stats' in renderer:
                text = renderer['stats'][0].get('runs', [{}])[0].get('text', '0')
            else:
                return 0
            
            # Extract number from text like "50 videos"
            numbers = re.findall(r'\d+', text.replace(',', ''))
            return int(numbers[0]) if numbers else 0
        except (KeyError, IndexError, ValueError):
            return 0
    
    def _extract_author(self, renderer: Dict) -> str:
        """Extract author from playlist renderer."""
        try:
            if 'ownerText' in renderer:
                return renderer['ownerText'].get('runs', [{}])[0].get('text', 'Unknown')
            elif 'subtitle' in renderer:
                return renderer['subtitle'].get('simpleText', 'Unknown')
            return 'Unknown'
        except (KeyError, IndexError):
            return 'Unknown'
    
    def get_video_list(self) -> List[Dict[str, str]]:
        """
        Get list of all videos in the playlist.
        
        Returns:
            List of dictionaries containing video ID, title, and URL
        """
        if self._video_list:
            return self._video_list
            
        api_url = "https://www.youtube.com/youtubei/v1/browse"
        
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20231219.01.00",
                    "hl": "en",
                    "gl": "US"
                }
            },
            "browseId": f"VL{self.playlist_id}"
        }
        
        videos = []
        continuation_token = None
        
        while True:
            if continuation_token:
                payload = {
                    "context": payload["context"],
                    "continuation": continuation_token
                }
            
            try:
                response = self.session.post(api_url, json=payload, timeout=self.request_timeout)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                # Stop on network failure; return what we have
                with print_lock:
                    print(f"❌ Playlist fetch error: {e}")
                break
            except ValueError:
                with print_lock:
                    print("❌ Invalid JSON in playlist response")
                break
            
            # Extract video items
            try:
                if continuation_token:
                    # Continuation response
                    items = data['onResponseReceivedActions'][0]['appendContinuationItemsAction']['continuationItems']
                else:
                    # Initial response
                    tabs = data['contents']['twoColumnBrowseResultsRenderer']['tabs']
                    for tab in tabs:
                        if 'tabRenderer' in tab and tab['tabRenderer'].get('selected'):
                            contents = tab['tabRenderer']['content']['sectionListRenderer']['contents']
                            items = contents[0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
                            break
                
                for item in items:
                    if 'playlistVideoRenderer' in item:
                        video = item['playlistVideoRenderer']
                        video_id = video.get('videoId')
                        
                        if video_id:
                            # Extract title
                            title = 'Unknown Title'
                            if 'title' in video:
                                if 'runs' in video['title']:
                                    title = video['title']['runs'][0].get('text', title)
                                elif 'simpleText' in video['title']:
                                    title = video['title']['simpleText']
                            
                            videos.append({
                                'video_id': video_id,
                                'title': self._sanitize_filename(title),
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            })
                    
                
                # Find continuation token for next page; if none, we're done
                next_token = None
                for item in items:
                    if 'continuationItemRenderer' in item:
                        next_token = item['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
                        break
                
                if next_token:
                    continuation_token = next_token
                else:
                    break
                    
            except (KeyError, IndexError, TypeError) as e:
                # No more videos or error in parsing
                break
        
        self._video_list = videos
        return videos
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove invalid characters from filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename or 'video'
    
    def _load_download_state(self, state_file: Path) -> Dict:
        """Load download state from file."""
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {'completed': [], 'failed': []}
    
    def _save_download_state(self, state_file: Path, state: Dict):
        """Save download state to file."""
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except IOError:
            pass
    
    def download(
        self,
        output_dir: str = "./downloads",
        quality: Optional[str] = None,
        itag: Optional[int] = None,
        max_workers: int = 3,
        progress_callback: Optional[Callable] = None,
        resume: bool = True
    ) -> Dict[str, List[str]]:
        """
        Download all videos from the playlist.
        
        Args:
            output_dir: Directory to save videos
            quality: Quality preference (e.g., "720p", "1080p")
            itag: Specific format itag
            max_workers: Number of concurrent downloads (default: 3)
            progress_callback: Optional callback function(current, total, video_title, status)
            resume: Whether to resume previous download session
            
        Returns:
            Dictionary with 'completed' and 'failed' lists of video IDs
        """
        # Validate max_workers
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if max_workers > 10:
            raise ValueError("max_workers must be <= 10 (recommended 1-5 for stability)")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get playlist info and videos
        print(f"Fetching playlist information...")
        playlist_info = self._get_playlist_info()
        videos = self.get_video_list()
        
        if not videos:
            print("No videos found in playlist!")
            return {'completed': [], 'failed': []}

        print(f"\nPlaylist: {playlist_info['title']}")
        print(f"Author: {playlist_info['author']}")
        print(f"Videos: {len(videos)}")
        print(f"Output: {output_path.absolute()}")
        print(f"Concurrency: {max_workers} workers\n")
        
        # Load previous state if resuming
        state_file = output_path / '.ytsnap_state.json'
        state = self._load_download_state(state_file) if resume else {'completed': [], 'failed': []}
        
        completed = set(state['completed'])
        failed = []
        
        # Filter out already completed videos
        videos_to_download = [v for v in videos if v['video_id'] not in completed]
        
        if len(videos_to_download) < len(videos):
            print(f"📝 Resuming: {len(completed)} already downloaded, {len(videos_to_download)} remaining\n")
        
        def download_video(index: int, video: Dict) -> tuple:
            """Download a single video."""
            video_num = index + 1
            total = len(videos)
            
            try:
                # Create safe filename
                filename = f"{video_num:03d}_{video['title']}.mp4"
                filepath = output_path / filename
                
                # Skip if already exists and completed
                if video['video_id'] in completed:
                    return (True, video['video_id'], f"Already downloaded")
                
                # Thread-safe print
                with print_lock:
                    print(f"[{video_num}/{total}] Downloading: {video['title']}")
                    sys.stdout.flush()
                
                # Download video in quiet mode to avoid progress bar conflicts
                downloader = YouTubeDownloader(video['url'])
                downloader.download(str(filepath), quality=quality, itag=itag, quiet=True)
                
                # Thread-safe print
                with print_lock:
                    print(f"✓ [{video_num}/{total}] {video['title']}")
                    sys.stdout.flush()
                
                if progress_callback:
                    progress_callback(video_num, total, video['title'], 'completed')
                
                return (True, video['video_id'], filename)
                
            except KeyboardInterrupt:
                # Re-raise to propagate to main thread
                raise
                
            except Exception as e:
                error_msg = str(e)
                with print_lock:
                    print(f"❌ [{video_num}/{total}] Failed: {video['title']} - {error_msg}")
                    sys.stdout.flush()
                
                if progress_callback:
                    progress_callback(video_num, total, video['title'], f'failed: {error_msg}')
                
                return (False, video['video_id'], error_msg)
        
        # Download videos with thread pool
        start_time = time.time()
        interrupted = False
        executor = ThreadPoolExecutor(max_workers=max_workers)
        futures = {}
        
        try:
            # Submit all download tasks
            futures = {
                executor.submit(download_video, i, video): video 
                for i, video in enumerate(videos)
                if video['video_id'] not in completed
            }
            
            # Process completed downloads
            for future in as_completed(futures):
                success, video_id, result = future.result()
                
                if success:
                    completed.add(video_id)
                else:
                    failed.append(video_id)
                
                # Save state after each video
                state = {
                    'completed': list(completed),
                    'failed': failed
                }
                self._save_download_state(state_file, state)
        
        except KeyboardInterrupt:
            interrupted = True
            print("\n\n⚠️  Download interrupted by user (Ctrl+C)")
            print("📝 Progress has been saved. Run the same command to resume.\n")
            
            # Save current state
            state = {
                'completed': list(completed),
                'failed': failed
            }
            self._save_download_state(state_file, state)
            
            # Cancel remaining futures gracefully
            for future in futures:
                future.cancel()
            
            # Show quick summary
            elapsed = time.time() - start_time
            print(f"{'='*60}")
            print(f"✅ Completed: {len(completed)}/{len(videos)} videos")
            if failed:
                print(f"❌ Failed: {len(failed)} videos")
            print(f"⏱️  Time: {elapsed:.1f} seconds")
            print(f"{'='*60}\n")
            print("💡 To resume, run the same command again.")
            print(f"   State saved in: {state_file}\n")
        
        finally:
            # Shutdown executor gracefully without waiting for cancelled futures
            executor.shutdown(wait=False, cancel_futures=True)
        
        # Summary
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        
        if interrupted:
            print(f"⚠️  INTERRUPTED")
        
        print(f"✅ Completed: {len(completed)}/{len(videos)} videos")
        if failed:
            print(f"❌ Failed: {len(failed)} videos")
        print(f"⏱️  Time: {elapsed:.1f} seconds")
        print(f"{'='*60}\n")
        
        if interrupted:
            print("💡 To resume, run the same command again.")
            print(f"   State saved in: {state_file}\n")
        
        if resume and state_file.exists():
            # Clean up state file if all done
            if len(completed) == len(videos):
                state_file.unlink()
                print("✨ All videos downloaded! State file cleaned up.\n")
        
        return {
            'completed': list(completed),
            'failed': failed
        }
    
    def get_playlist_metadata(self) -> Dict:
        """
        Get playlist metadata without downloading.
        
        Returns:
            Dictionary containing playlist title, author, video count, and video list
        """
        info = self._get_playlist_info()
        videos = self.get_video_list()
        
        return {
            'title': info['title'],
            'author': info['author'],
            'video_count': len(videos),
            'videos': videos
        }
