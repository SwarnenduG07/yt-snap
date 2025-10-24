# ytsnap

Fast and independent YouTube video downloader built from scratch.

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
```

## Library Usage

```python
from youtube_downloader import YouTubeDownloader

# Initialize downloader
downloader = YouTubeDownloader("https://www.youtube.com/watch?v=VIDEO_ID")

# Get available formats
formats = downloader.get_formats()
for fmt in formats:
    print(f"itag={fmt['itag']} quality={fmt['quality']} size={fmt['filesize']}")

# Download video (auto-selects best format)
downloader.download("video.mp4")

# Download specific quality
downloader.download("video_720p.mp4", quality="720p")

# Download by itag
downloader.download("video.mp4", itag=18)
```

## Features

- ✅ No yt-dlp dependency
- ✅ Uses YouTube's innertube API
- ✅ Multiple quality options
- ✅ Progress tracking
- ✅ Both CLI and library usage
- ✅ Video and audio formats
- ✅ Fast and lightweight

## How it works

Uses YouTube's official innertube API with Android client credentials to fetch direct CDN URLs without signature decryption complexity.

## License

MIT

