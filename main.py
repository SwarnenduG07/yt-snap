import re
import json
import requests

class YouTubeDownloader:
    def __init__(self, url):
        self.url = url
        self.video_id = self._extract_video_id(url)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/'
        })
        
    def _extract_video_id(self, url):
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Invalid YouTube URL")
    
    def _get_video_info(self):
        # Use innertube API
        api_url = "https://www.youtube.com/youtubei/v1/player"
        
        payload = {
            "context": {
                "client": {
                    "clientName": "ANDROID",
                    "clientVersion": "19.09.37",
                    "androidSdkVersion": 30,
                    "hl": "en",
                    "gl": "US"
                }
            },
            "videoId": self.video_id
        }
        
        response = self.session.post(api_url, json=payload)
        return response.json()
    
    def get_formats(self):
        data = self._get_video_info()
        
        if 'playabilityStatus' in data:
            status = data['playabilityStatus'].get('status')
            if status != 'OK':
                reason = data['playabilityStatus'].get('reason', 'Unknown error')
                raise Exception(f"Video not available: {reason}")
        
        formats = data.get('streamingData', {}).get('formats', []) + \
                  data.get('streamingData', {}).get('adaptiveFormats', [])
        
        video_formats = []
        for fmt in formats:
            if 'url' in fmt:
                video_formats.append({
                    'itag': fmt.get('itag'),
                    'quality': fmt.get('qualityLabel', fmt.get('quality')),
                    'mime': fmt.get('mimeType', '').split(';')[0],
                    'url': fmt['url'],
                    'has_video': 'video' in fmt.get('mimeType', ''),
                    'has_audio': 'audio' in fmt.get('mimeType', ''),
                    'filesize': fmt.get('contentLength', 0)
                })
        
        return video_formats
    
    def download(self, output_file='video.mp4', itag=None, quality=None):
        formats = self.get_formats()
        
        if not formats:
            raise Exception("No downloadable formats found")
        
        # Select format
        if itag:
            selected = next((f for f in formats if f['itag'] == itag), None)
            if not selected:
                raise Exception(f"Format with itag {itag} not found")
        elif quality:
            selected = next((f for f in formats if quality in str(f['quality'])), None)
            if not selected:
                raise Exception(f"Quality {quality} not found")
        else:
            # Prefer formats with both video and audio
            with_both = [f for f in formats if f['has_video'] and f['has_audio']]
            selected = with_both[0] if with_both else formats[0]
        
        print(f"Downloading: {selected['quality']} - {selected['mime']}")
        if selected['filesize']:
            print(f"Size: {int(selected['filesize']) / (1024*1024):.2f} MB")
        
        # Download with proper headers
        headers = {
            'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11)',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Range': 'bytes=0-'
        }
        
        response = self.session.get(selected['url'], headers=headers, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_file, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB)", end='', flush=True)
        
        print(f"\n✓ Downloaded to {output_file}")
        return output_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <youtube_url> [output_file] [--quality 720p|1080p|etc]")
        print("       python main.py <youtube_url> [output_file] [--itag 18|22|etc]")
        sys.exit(1)
    
    url = sys.argv[1]
    output = "video.mp4"
    itag = None
    quality = None
    
    # Parse arguments
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
