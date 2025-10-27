"""Example usage of youtube_downloader as a library"""

from youtube_downloader import YouTubeDownloader, PlaylistDownloader, ProxyManager, ProxyConfig

# ===================================================================
# SINGLE VIDEO DOWNLOAD EXAMPLES
# ===================================================================

# Example 1: Basic download
url = "https://www.youtube.com/watch?v=cTTYRbiARqw"
downloader = YouTubeDownloader(url)

# Get available formats
formats = downloader.get_formats()
print(f"Found {len(formats)} formats")

# Download video
downloader.download("my_video.mp4")

# Example 2: Download specific quality
downloader.download("video_720p.mp4", quality="720p")

# Example 3: Download by itag
downloader.download("video_itag.mp4", itag=18)

# Example 4: Using proxy from file
proxy_manager = ProxyManager.from_file("proxies.example.txt")
downloader = YouTubeDownloader(url, proxy_manager=proxy_manager)
downloader.download("video_with_proxy.mp4")

# Example 5: Using single proxy
proxy_config = ProxyConfig(
    host="127.0.0.1",
    port=8080,
    scheme="http"
)
proxy_manager = ProxyManager(proxies=[proxy_config])
downloader = YouTubeDownloader(url, proxy_manager=proxy_manager)
downloader.download("video_with_single_proxy.mp4")

# Example 6: SOCKS5 proxy with authentication
proxy_config = ProxyConfig(
    host="proxy.example.com",
    port=1080,
    scheme="socks5",
    username="user",
    password="pass"
)
proxy_manager = ProxyManager(proxies=[proxy_config])
downloader = YouTubeDownloader(url, proxy_manager=proxy_manager)
downloader.download("video_socks5.mp4")

# ===================================================================
# PLAYLIST DOWNLOAD EXAMPLES
# ===================================================================

# Example 7: Basic playlist download
playlist_url = "https://www.youtube.com/playlist?list=PLxxx"
playlist_downloader = PlaylistDownloader(playlist_url, concurrency=3)

# Get list of videos in playlist
videos = playlist_downloader.get_videos()
print(f"Found {len(videos)} videos in playlist")

# Download entire playlist
stats = playlist_downloader.download(output_dir="./playlist_downloads")
print(f"Downloaded {stats['successful']}/{stats['total']} videos")

# Example 8: Download playlist with specific quality
playlist_downloader = PlaylistDownloader(playlist_url, concurrency=3)
stats = playlist_downloader.download(output_dir="./downloads", quality="720p")

# Example 9: Download playlist with custom concurrency
playlist_downloader = PlaylistDownloader(playlist_url, concurrency=5)
stats = playlist_downloader.download(output_dir="./downloads")

# Example 10: Download playlist with callbacks
def on_video_start(video):
    print(f"🔄 Starting: {video['title']}")

def on_video_complete(video, output_file):
    print(f"✅ Completed: {video['title']}")

def on_error(video, error):
    print(f"❌ Error downloading {video['title']}: {error}")

playlist_downloader = PlaylistDownloader(playlist_url, concurrency=3)
stats = playlist_downloader.download(
    output_dir="./downloads",
    on_video_start=on_video_start,
    on_video_complete=on_video_complete,
    on_error=on_error
)

# Example 11: Download playlist with proxies
proxy_manager = ProxyManager.from_file("proxies.example.txt")
playlist_downloader = PlaylistDownloader(
    playlist_url,
    proxy_manager=proxy_manager,
    concurrency=3
)
stats = playlist_downloader.download(output_dir="./downloads")

# Example 12: Download playlist with specific itag
playlist_downloader = PlaylistDownloader(playlist_url, concurrency=3)
stats = playlist_downloader.download(output_dir="./downloads", itag=18)
