"""Example usage of youtube_downloader as a library"""

from youtube_downloader import YouTubeDownloader

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
