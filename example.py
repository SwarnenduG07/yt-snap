"""Example usage of youtube_downloader as a library"""

from youtube_downloader import YouTubeDownloader, ProxyManager, ProxyConfig

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
