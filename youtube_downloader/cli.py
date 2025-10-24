import sys
from .downloader import YouTubeDownloader

def main():
    if len(sys.argv) < 2:
        print("Usage: ytsnap <youtube_url> [output_file] [--quality 720p|1080p|etc]")
        print("       ytsnap <youtube_url> [output_file] [--itag 18|22|etc]")
        sys.exit(1)
    
    url = sys.argv[1]
    output = "video.mp4"
    itag = None
    quality = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--itag' and i + 1 < len(sys.argv):
            itag = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--quality' and i + 1 < len(sys.argv):
            quality = sys.argv[i + 1]
            i += 2
        elif not sys.argv[i].startswith('--'):
            output = sys.argv[i]
            i += 1
        else:
            i += 1
    
    try:
        downloader = YouTubeDownloader(url)
        
        print(f"Video ID: {downloader.video_id}")
        print("Fetching video info...\n")
        
        formats = downloader.get_formats()
        
        print("Available formats:")
        for i, fmt in enumerate(formats[:20]):
            av = []
            if fmt['has_video']: av.append('V')
            if fmt['has_audio']: av.append('A')
            size = f"{int(fmt['filesize'])/(1024*1024):.1f}MB" if fmt['filesize'] else "?"
            print(f"{i+1}. itag={fmt['itag']:3} [{'+'.join(av)}] {str(fmt['quality']):6} {fmt['mime']:20} {size}")
        
        print()
        downloader.download(output, itag=itag, quality=quality)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
