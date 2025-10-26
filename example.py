"""
Example usage of youtube_downloader as a library

This file demonstrates both single video and playlist downloads
with various configuration options.
"""

from youtube_downloader import YouTubeDownloader, PlaylistDownloader

print("=" * 70)
print("YTSNAP - YouTube Downloader Library Examples")
print("=" * 70)

# ============================================================================
# EXAMPLE 1: Single Video Download
# ============================================================================
print("\n[Example 1] Single Video Download")
print("-" * 70)

url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
downloader = YouTubeDownloader(url)

# Get available formats
print("Fetching available formats...")
formats = downloader.get_formats()
print(f"✓ Found {len(formats)} available formats\n")

# Show some format examples
print("Sample formats:")
for fmt in formats[:5]:
    print(f"  - itag={fmt['itag']:3d}, quality={fmt.get('quality', 'N/A'):6s}, "
          f"mime={fmt['mime']:15s}, video={fmt['has_video']}, audio={fmt['has_audio']}")

# Uncomment to download:
# print("\nDownloading video...")
# downloader.download("my_video.mp4")
# print("✓ Download complete!")


# ============================================================================
# EXAMPLE 2: Download Specific Quality
# ============================================================================
print("\n[Example 2] Download with Specific Quality")
print("-" * 70)

# Uncomment to download in 720p:
# downloader.download("video_720p.mp4", quality="720p")
# print("✓ 720p video downloaded!")

print("Usage: downloader.download('video_720p.mp4', quality='720p')")


# ============================================================================
# EXAMPLE 3: Download by itag
# ============================================================================
print("\n[Example 3] Download by Specific itag")
print("-" * 70)

# Uncomment to download specific format:
# downloader.download("video.mp4", itag=22)  # itag 22 = 720p with audio
# print("✓ Video downloaded using itag 22!")

print("Usage: downloader.download('video.mp4', itag=22)")


# ============================================================================
# EXAMPLE 4: Playlist Metadata (Without Downloading)
# ============================================================================
print("\n[Example 4] Get Playlist Metadata")
print("-" * 70)

playlist_url = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
print(f"Playlist ID: {playlist_url}")

playlist = PlaylistDownloader(playlist_url)

# Get metadata without downloading
print("Fetching playlist metadata...")
metadata = playlist.get_playlist_metadata()
print(f"\n✓ Playlist Title: {metadata['title']}")
print(f"✓ Author: {metadata['author']}")
print(f"✓ Total Videos: {metadata['video_count']}\n")

# Show video list
print("Videos in playlist:")
videos = playlist.get_video_list()
for i, video in enumerate(videos[:10], 1):  # Show first 10
    print(f"  {i:2d}. {video['title']}")
    print(f"      ID: {video['id']}")

if len(videos) > 10:
    print(f"  ... and {len(videos) - 10} more videos")


# ============================================================================
# EXAMPLE 5: Download Entire Playlist
# ============================================================================
print("\n[Example 5] Download Entire Playlist")
print("-" * 70)

# Uncomment to download entire playlist:
"""
result = playlist.download(
    output_dir="./my_playlist",
    quality="720p",
    max_workers=3,  # Download 3 videos concurrently
    resume=True     # Resume if interrupted (default)
)

print(f"\n✓ Successfully downloaded: {len(result['completed'])} videos")
if result['failed']:
    print(f"✗ Failed: {len(result['failed'])} videos")
    for video_id in result['failed']:
        print(f"  - {video_id}")
"""

print("To download, uncomment the code in example.py")
print("\nConfiguration options:")
print("  - output_dir: Directory to save videos")
print("  - quality: Preferred quality (e.g., '720p', '1080p')")
print("  - max_workers: Concurrent downloads (1-10, default: 3)")
print("  - resume: Resume interrupted downloads (default: True)")


# ============================================================================
# EXAMPLE 6: Download with Custom Progress Tracking
# ============================================================================
print("\n[Example 6] Custom Progress Tracking")
print("-" * 70)

def my_progress_callback(current, total, title, status):
    """Custom callback function for download progress"""
    percentage = (current / total) * 100
    print(f"[{percentage:5.1f}%] Video {current}/{total}: {status}")
    print(f"         Title: {title}")

# Uncomment to use custom progress:
"""
result = playlist.download(
    output_dir="./downloads",
    max_workers=2,
    progress_callback=my_progress_callback
)
"""

print("Custom progress callback example:")
print("  def my_progress_callback(current, total, title, status):")
print("      print(f'[{current}/{total}] {title}: {status}')")
print("\n  playlist.download(progress_callback=my_progress_callback)")


# ============================================================================
# EXAMPLE 7: Different URL Formats
# ============================================================================
print("\n[Example 7] Different Playlist URL Formats")
print("-" * 70)

url_formats = [
    ("Direct ID", "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"),
    ("Full URL", "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"),
    ("Watch URL", "https://www.youtube.com/watch?v=VIDEO_ID&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"),
]

print("All these URL formats are supported:\n")
for name, url_format in url_formats:
    try:
        pl = PlaylistDownloader(url_format)
        print(f"✓ {name:15s}: {url_format[:60]}...")
        print(f"  → Extracted ID: {pl.playlist_id}")
    except Exception as e:
        print(f"✗ {name:15s}: {e}")


# ============================================================================
# EXAMPLE 8: Error Handling
# ============================================================================
print("\n[Example 8] Error Handling")
print("-" * 70)

# Test invalid URL handling
invalid_urls = [
    "not_a_url",
    "https://example.com",
    "PLtest",  # Too short
]

print("Testing invalid URLs:\n")
for invalid_url in invalid_urls:
    try:
        PlaylistDownloader(invalid_url)
        print(f"✗ Should have raised error for: {invalid_url}")
    except ValueError as e:
        print(f"✓ Correctly rejected: {invalid_url}")
        print(f"  Error: {str(e)[:60]}...")


# ============================================================================
# EXAMPLE 9: Download Without Resume (Start Fresh)
# ============================================================================
print("\n[Example 9] Download Without Resume")
print("-" * 70)

# Uncomment to download without resuming:
"""
result = playlist.download(
    output_dir="./fresh_download",
    resume=False  # Start fresh, ignore previous state
)
"""

print("To start a fresh download (ignoring previous state):")
print("  playlist.download(output_dir='./videos', resume=False)")
print("\nNote: By default, resume=True, so interrupted downloads continue")
print("      State is saved in .ytsnap_state.json in the output directory")


# ============================================================================
# EXAMPLE 10: High Concurrency Download
# ============================================================================
print("\n[Example 10] High Concurrency Download")
print("-" * 70)

# Uncomment for faster downloads with more workers:
"""
result = playlist.download(
    output_dir="./downloads",
    max_workers=10,  # Maximum allowed
    quality="720p"
)
"""

print("For faster downloads, increase max_workers:")
print("  - 1 worker:  Sequential (slowest)")
print("  - 3 workers: Default (balanced)")
print("  - 5 workers: Fast (recommended for good internet)")
print("  - 10 workers: Maximum (fastest, but resource intensive)")
print("\nUsage: playlist.download(max_workers=5)")


# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 70)
print("TIPS & BEST PRACTICES")
print("=" * 70)
print("""
1. Resume Support:
   - Downloads automatically resume if interrupted (Ctrl+C)
   - State is saved in .ytsnap_state.json
   - Use resume=False to start fresh

2. Concurrency:
   - Adjust max_workers based on your internet speed
   - More workers = faster but more resource intensive

3. Quality Selection:
   - Use quality='720p' for general preference
   - Use itag=22 for specific format
   - If both specified, itag takes precedence

4. Error Handling:
   - Failed videos don't stop the entire download
   - Check result['failed'] for failed video IDs

5. File Naming:
   - Files are numbered (001_, 002_, etc.)
   - Special characters are sanitized automatically
   - All files saved as .mp4

6. Interrupting Downloads:
   - Press Ctrl+C to interrupt gracefully
   - State is saved automatically
   - Resume by running the same command again
""")

print("=" * 70)
print("For more examples, see: README.md and USAGE_EXAMPLES.md")
print("=" * 70)
