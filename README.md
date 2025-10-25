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

