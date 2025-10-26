# ytsnap

A modern, community-driven alternative to yt-dlp. Built from scratch for simplicity, speed, and extensibility.

[![PyPI version](https://badge.fury.io/py/ytsnap.svg)](https://pypi.org/project/ytsnap/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-friendly-blueviolet)](https://hacktoberfest.com/)

## Why ytsnap over yt-dlp?

- 🚀 **Lightweight**: Minimal dependencies, just requests library
- 🔄 **Modern API**: Uses YouTube's official innertube API
- 🛠 **Simple Architecture**: Easy to understand and contribute to
- 📦 **Fast Installation**: No complex build process
- 🔧 **Maintainable**: Built with modern Python practices
- 👥 **Community First**: Designed for community contributions

## Hacktoberfest 2025 🎃

This repository is participating in Hacktoberfest 2025! We welcome contributions from the community.

### How to Contribute

1. Check out our [CONTRIBUTING.md](CONTRIBUTING.md) guide
2. Look for issues labeled with `hacktoberfest` or `good first issue`
3. Fork the repository and create your branch
4. Make your changes and submit a pull request
5. Wait for review and address any feedback

Please ensure you read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Installation

```bash
pip install ytsnap
```

## CLI Usage

```bash
# Basic download
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID"

# Custom output filename
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" output.mp4

# Download specific quality
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" video.mp4 --quality 720p

# Download by itag
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" video.mp4 --itag 18

# Download entire playlist
ytsnap --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Download playlist with custom output directory
ytsnap --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --output-dir "./my_videos"

# Download playlist with specific quality and concurrency
ytsnap --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --quality 720p --concurrency 5

# Download playlist without resume (start fresh)
ytsnap --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --no-resume
```

## Library Usage

### Single Video Download

```python
from youtube_downloader import YouTubeDownloader

# Initialize downloader
downloader = YouTubeDownloader("https://www.youtube.com/watch?v=jNQXAC9IVRw")

# Get available formats
formats = downloader.get_formats()
for fmt in formats[:5]:  # Show first 5 formats
    print(f"itag={fmt['itag']}, quality={fmt['quality']}, "
          f"video={fmt['has_video']}, audio={fmt['has_audio']}")

# Download video (auto-selects best format)
downloader.download("video.mp4")

# Download specific quality
downloader.download("video_720p.mp4", quality="720p")

# Download by specific itag
downloader.download("video.mp4", itag=22)  # itag 22 = 720p with audio
```

### Playlist Download

```python
from youtube_downloader import PlaylistDownloader

# Initialize playlist downloader (accepts URL or playlist ID)
playlist = PlaylistDownloader("PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")

# Get playlist metadata without downloading
metadata = playlist.get_playlist_metadata()
print(f"Playlist: {metadata['title']}")
print(f"Videos: {metadata['video_count']}")
print(f"Author: {metadata['author']}")

# Get list of all videos
videos = playlist.get_video_list()
for i, video in enumerate(videos[:5], 1):
    print(f"{i}. {video['title']} (ID: {video['video_id']})")

# Download entire playlist with default settings
result = playlist.download()

# Download with custom settings
result = playlist.download(
    output_dir="./my_downloads",  # Custom output directory
    quality="720p",                # Prefer 720p quality
    max_workers=3,                 # Download 3 videos concurrently
    resume=True                    # Resume interrupted downloads (default)
)

print(f"✅ Completed: {len(result['completed'])} videos")
print(f"❌ Failed: {len(result['failed'])} videos")

# Download without resume (start fresh)
result = playlist.download(
    output_dir="./videos",
    resume=False  # Ignore previous state
)
```

### Advanced Usage

```python
from youtube_downloader import PlaylistDownloader

# Custom progress tracking
def my_progress(current, total, title, status):
    """Custom callback for progress updates"""
    print(f"[{current}/{total}] {status}: {title}")

playlist = PlaylistDownloader("PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")

result = playlist.download(
    output_dir="./downloads",
    quality="1080p",               # Prefer 1080p
    max_workers=5,                 # 5 concurrent downloads
    progress_callback=my_progress, # Custom progress handler
    resume=True
)

# Error handling
try:
    playlist = PlaylistDownloader("invalid_url")
except ValueError as e:
    print(f"Invalid playlist URL: {e}")

# Check for failed downloads
if result['failed']:
    print("Some videos failed:")
    for video_id in result['failed']:
        print(f"  - {video_id}")
```

### Different URL Formats Supported

```python
from youtube_downloader import PlaylistDownloader

# All these formats work:
playlist1 = PlaylistDownloader("PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")  # Direct ID
playlist2 = PlaylistDownloader("https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")  # Full URL
playlist3 = PlaylistDownloader("https://www.youtube.com/watch?v=VIDEO_ID&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")  # Watch URL with list
```

### API Reference

#### `YouTubeDownloader`

**Methods:**

- `get_formats()` → List of available formats with itag, quality, mime type, etc.
- `download(output_file, quality=None, itag=None, quiet=False)` → Download the video

#### `PlaylistDownloader`

**Constructor:**

- `PlaylistDownloader(url)` - Accepts playlist URL or ID

**Methods:**

- `get_playlist_metadata()` → Dict with title, author, video_count, videos
- `get_video_list()` → List of all videos in the playlist
- `download(output_dir="./downloads", quality=None, itag=None, max_workers=3, progress_callback=None, resume=True)` → Download all videos

**Download Parameters:**

- `output_dir` (str): Directory to save videos (default: "./downloads")
- `quality` (str): Quality preference like "720p", "1080p" (default: best available)
- `itag` (int): Specific format identifier (overrides quality)
- `max_workers` (int): Concurrent downloads, 1-10 (default: 3)
- `progress_callback` (callable): Function(current, total, title, status) for progress updates
- `resume` (bool): Resume interrupted downloads (default: True)

**Returns:** Dict with `completed` (list of video IDs) and `failed` (list of video IDs)

### Key Features

- **Concurrent Downloads**: Download multiple videos simultaneously (configurable 1-10 workers)
- **Resume Support**: Automatically resumes interrupted downloads using state files
- **Error Resilience**: Failed videos don't stop the entire download
- **Progress Tracking**: Real-time progress for each video and overall completion
- **Thread-Safe**: Safe concurrent downloads with proper locking
- **Clean Interrupts**: Ctrl+C gracefully saves state and exits

## Features

- ✅ No yt-dlp dependency
- ✅ Uses YouTube's innertube API
- ✅ Multiple quality options
- ✅ Progress tracking
- ✅ Both CLI and library usage
- ✅ Video and audio formats
- ✅ Fast and lightweight
- ✅ **Playlist downloads with resume support**
- ✅ **Concurrent downloads for playlists**
- ✅ **Automatic error handling and retry**

## How it works

Uses YouTube's official innertube API with Android client credentials to fetch direct CDN URLs without signature decryption complexity.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Areas for Contribution

- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🧪 Test coverage
- 🎨 Code quality improvements

## License

MIT
