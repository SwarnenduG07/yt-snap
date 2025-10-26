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

# Use proxies from file (bypass rate limits)
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" video.mp4 --proxy-file proxies.txt

# Use single proxy
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" video.mp4 --proxy "http://127.0.0.1:8080"

# Use authenticated proxy
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" video.mp4 --proxy "http://user:pass@proxy.com:8080"
```

## Library Usage

```python
from youtube_downloader import YouTubeDownloader, ProxyManager, ProxyConfig

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

# Use proxy manager to bypass rate limits
proxy_manager = ProxyManager.from_file("proxies.txt")
downloader = YouTubeDownloader("https://www.youtube.com/watch?v=VIDEO_ID", proxy_manager=proxy_manager)
downloader.download("video_with_proxy.mp4")

# Use single proxy
proxy_config = ProxyConfig(host="127.0.0.1", port=8080, scheme="http")
proxy_manager = ProxyManager(proxies=[proxy_config])
downloader = YouTubeDownloader("https://www.youtube.com/watch?v=VIDEO_ID", proxy_manager=proxy_manager)
downloader.download("video.mp4")
```

## Features

- ✅ No yt-dlp dependency
- ✅ Uses YouTube's innertube API
- ✅ Multiple quality options
- ✅ Progress tracking
- ✅ Both CLI and library usage
- ✅ Video and audio formats
- ✅ Fast and lightweight
- ✅ **Proxy support** (HTTP, HTTPS, SOCKS4, SOCKS5)
- ✅ **Proxy rotation** to bypass rate limits
- ✅ **Automatic failover** and health checking
- ✅ **Proxy authentication** support

## Proxy Support

ytsnap includes robust proxy support to bypass rate limiting and distribute requests across multiple IPs.

### Proxy Types Supported
- **HTTP/HTTPS** proxies
- **SOCKS4/SOCKS4A** proxies
- **SOCKS5** proxies
- **Authenticated** proxies (username:password)

### Features
- ✅ Automatic proxy rotation
- ✅ Health checking and failure tracking
- ✅ Automatic failover on rate limits (429 errors)
- ✅ Support for proxy lists from files
- ✅ Time-based and round-robin rotation

### Creating a Proxy File

Create a file (e.g., `proxies.txt`) with one proxy per line:

```
http://127.0.0.1:8080
https://proxy.example.com:8443
socks5://127.0.0.1:1080
http://username:password@proxy.example.com:8080
```

### CLI Usage with Proxies

```bash
# Use proxy file
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" output.mp4 --proxy-file proxies.txt

# Use single proxy
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" output.mp4 --proxy "http://127.0.0.1:8080"

# Use SOCKS5 proxy
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" output.mp4 --proxy "socks5://127.0.0.1:1080"

# Disable health checking
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID" output.mp4 --proxy-file proxies.txt --no-health-check
```

### Library Usage with Proxies

```python
from youtube_downloader import YouTubeDownloader, ProxyManager, ProxyConfig

# Load proxies from file
proxy_manager = ProxyManager.from_file("proxies.txt")

# Initialize downloader with proxy manager
downloader = YouTubeDownloader(url, proxy_manager=proxy_manager)
downloader.download("video.mp4")

# Create custom proxy configuration
proxy_config = ProxyConfig(
    host="127.0.0.1",
    port=8080,
    scheme="http",
    username="user",  # optional
    password="pass"   # optional
)
proxy_manager = ProxyManager(proxies=[proxy_config])
downloader = YouTubeDownloader(url, proxy_manager=proxy_manager)
downloader.download("video.mp4")
```

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

