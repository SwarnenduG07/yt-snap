import sys
from typing import Optional
from .downloader import YouTubeDownloader, PlaylistDownloader
from .proxy_manager import ProxyManager, ProxyConfig


def print_usage():
    """Print usage information."""
    print("Usage: ytsnap <youtube_url> [output_file] [options]")
    print("\nOptions:")
    print("  --quality <quality>    Select specific quality (e.g., 720p, 1080p)")
    print("  --itag <itag>          Select format by itag number")
    print("  --proxy-file <file>    Load proxies from file")
    print("  --proxy <proxy_url>    Use single proxy (e.g., http://host:port)")
    print("  --no-health-check      Disable proxy health checking")
    print("\nPlaylist Options:")
    print("  --playlist             Download entire playlist")
    print("  --output-dir <dir>     Output directory for playlist downloads (default: ./downloads)")
    print("  --concurrency <num>    Number of parallel downloads (default: 3)")
    print("\nProxy file format:")
    print("  http://host:port")
    print("  https://host:port")
    print("  socks4://host:port")
    print("  socks5://host:port")
    print("  http://user:pass@host:port")
    print("\nExamples:")
    print("  # Download single video")
    print("  ytsnap https://www.youtube.com/watch?v=VIDEO_ID")
    print("  # Download playlist")
    print("  ytsnap --playlist https://www.youtube.com/playlist?list=PLxxx --output-dir ./my_playlist")
    print("  # Download playlist with custom quality")
    print("  ytsnap --playlist https://www.youtube.com/playlist?list=PLxxx --output-dir ./videos --quality 720p")


def parse_proxy_url(proxy_url: str) -> Optional[ProxyConfig]:
    """Parse a proxy URL into ProxyConfig."""
    try:
        return ProxyManager._parse_proxy_line(proxy_url)
    except Exception as e:
        print(f"Error parsing proxy URL: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    url = sys.argv[1]
    output = "video.mp4"
    itag = None
    quality = None
    proxy_manager = None
    proxy_file = None
    proxy_url = None
    enable_health_check = True
    is_playlist = False
    output_dir = "./downloads"
    concurrency = 3
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--itag' and i + 1 < len(sys.argv):
            itag = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--quality' and i + 1 < len(sys.argv):
            quality = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--proxy-file' and i + 1 < len(sys.argv):
            proxy_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--proxy' and i + 1 < len(sys.argv):
            proxy_url = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--no-health-check':
            enable_health_check = False
            i += 1
        elif sys.argv[i] == '--playlist':
            is_playlist = True
            i += 1
        elif sys.argv[i] == '--output-dir' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--concurrency' and i + 1 < len(sys.argv):
            try:
                concurrency = int(sys.argv[i + 1])
                if concurrency < 1:
                    raise ValueError
            except ValueError:
                print("Error: --concurrency must be a positive integer")
                sys.exit(1)
            i += 2
        elif sys.argv[i] == '--help' or sys.argv[i] == '-h':
            print_usage()
            sys.exit(0)
        elif not sys.argv[i].startswith('--'):
            output = sys.argv[i]
            i += 1
        else:
            i += 1
    
    # Setup proxy manager
    if proxy_file:
        try:
            proxy_manager = ProxyManager.from_file(
                proxy_file,
                enable_health_check=enable_health_check
            )
            stats = proxy_manager.get_stats()
            print(f"✓ Loaded {stats['healthy']}/{stats['total']} healthy proxies from {proxy_file}\n")
        except Exception as e:
            print(f"Error loading proxy file: {e}")
            sys.exit(1)
    elif proxy_url:
        proxy_config = parse_proxy_url(proxy_url)
        if proxy_config:
            proxy_manager = ProxyManager(
                proxies=[proxy_config],
                enable_health_check=enable_health_check
            )
            print(f"✓ Using proxy: {proxy_config}\n")
        else:
            sys.exit(1)
    
    try:
        # Handle playlist downloads
        if is_playlist or 'playlist?list=' in url or 'list=' in url:
            print("=" * 60)
            print("Playlist Download Mode")
            print("=" * 60)
            
            playlist_downloader = PlaylistDownloader(
                url, 
                proxy_manager=proxy_manager, 
                concurrency=concurrency
            )
            
            if proxy_manager:
                stats = proxy_manager.get_stats()
                print(f"Proxies: {stats['healthy']}/{stats['total']} healthy")
            
            playlist_downloader.download(
                output_dir=output_dir,
                quality=quality,
                itag=itag
            )
        
        # Handle single video downloads
        else:
            downloader = YouTubeDownloader(url, proxy_manager=proxy_manager)
            
            print(f"Video ID: {downloader.video_id}")
            if proxy_manager:
                stats = proxy_manager.get_stats()
                print(f"Proxies: {stats['healthy']}/{stats['total']} healthy")
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
