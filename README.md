# YouTube Video Downloader

A minimal YouTube video downloader built from scratch without yt-dlp.

## Installation

```bash
uv sync
```

## Usage

Download a video:
```bash
uv run python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Download with custom output name:
```bash
uv run python main.py "https://www.youtube.com/watch?v=VIDEO_ID" output.mp4
```

## Features

- Extracts video formats directly from YouTube
- Downloads from YouTube CDN links
- Shows download progress
- Supports multiple video qualities
- No external video download libraries

## How it works

1. Extracts video ID from YouTube URL
2. Fetches video page and parses `ytInitialPlayerResponse`
3. Extracts direct CDN URLs from streaming data
4. Downloads video with progress tracking
