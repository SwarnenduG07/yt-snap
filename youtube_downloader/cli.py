import sys
from .downloader import YouTubeDownloader
from .playlist import PlaylistDownloader

def main():
    if len(sys.argv) < 2:
        print("Usage: ytsnap <youtube_url> [output_file] [--quality 720p|1080p|etc]")
        print("       ytsnap <youtube_url> [output_file] [--itag 18|22|etc]")
        print("       ytsnap --playlist <playlist_url> [--output-dir ./downloads] [--quality 720p]")
        print("       ytsnap --playlist <playlist_url> [--concurrency 3] [--no-resume]")
        sys.exit(1)
    
    # Check for playlist mode
    is_playlist = '--playlist' in sys.argv
    
    if is_playlist:
        # Playlist download mode
        try:
            playlist_idx = sys.argv.index('--playlist')
            if playlist_idx + 1 >= len(sys.argv):
                print("Error: --playlist requires a URL")
                sys.exit(1)
            
            url = sys.argv[playlist_idx + 1]
            output_dir = "./downloads"
            quality = None
            itag = None
            concurrency = 3
            resume = True
            
            # Parse remaining arguments
            i = 1
            while i < len(sys.argv):
                if sys.argv[i] == '--output-dir' and i + 1 < len(sys.argv):
                    output_dir = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--quality' and i + 1 < len(sys.argv):
                    quality = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--itag' and i + 1 < len(sys.argv):
                    itag = int(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == '--concurrency' and i + 1 < len(sys.argv):
                    concurrency = int(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == '--no-resume':
                    resume = False
                    i += 1
                else:
                    i += 1
            
            # Download playlist
            downloader = PlaylistDownloader(url)
            result = downloader.download(
                output_dir=output_dir,
                quality=quality,
                itag=itag,
                max_workers=concurrency,
                resume=resume
            )
            
            # Exit with error code if any failed
            if result['failed']:
                sys.exit(1)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    else:
        # Single video download mode
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
        
        except KeyboardInterrupt:
            print("\n\n👋 Download cancelled.")
            sys.exit(0)
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
