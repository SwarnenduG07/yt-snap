from main import YouTubeDownloader

# Test video URL
test_url = "https://www.youtube.com/watch?v=cTTYRbiARqw"

print("Testing YouTube Downloader\n")

# Initialize downloader
downloader = YouTubeDownloader(test_url)
print(f"✓ Video ID extracted: {downloader.video_id}\n")

# Get formats
print("Fetching available formats...")
formats = downloader.get_formats()
print(f"✓ Found {len(formats)} formats\n")

# Show first 5 formats
print("Sample formats:")
for fmt in formats[:5]:
    av = []
    if fmt['has_video']: av.append('V')
    if fmt['has_audio']: av.append('A')
    size = f"{int(fmt['filesize'])/(1024*1024):.1f}MB" if fmt['filesize'] else "?"
    print(f"  itag={fmt['itag']} [{'+'.join(av)}] {fmt['quality']} - {fmt['mime']} - {size}")

# Download smallest format for testing
smallest = min(formats, key=lambda x: int(x['filesize']) if x['filesize'] else float('inf'))
print(f"\nDownloading smallest format (itag={smallest['itag']}) for testing...")
downloader.download('test_output.mp4', itag=smallest['itag'])

print("\n✓ All tests passed!")
