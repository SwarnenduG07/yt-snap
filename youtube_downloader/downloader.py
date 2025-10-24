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
        
        if itag:
            selected = next((f for f in formats if f['itag'] == itag), None)
            if not selected:
                raise Exception(f"Format with itag {itag} not found")
        elif quality:
            selected = next((f for f in formats if quality in str(f['quality'])), None)
            if not selected:
                raise Exception(f"Quality {quality} not found")
        else:
            with_both = [f for f in formats if f['has_video'] and f['has_audio']]
            selected = with_both[0] if with_both else formats[0]
        
        print(f"Downloading: {selected['quality']} - {selected['mime']}")
        if selected['filesize']:
            print(f"Size: {int(selected['filesize']) / (1024*1024):.2f} MB")
        
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

