'''Test Types Needed
Unit Tests

URL parsing
Format selection
Progress calculation
Error handling
Integration Tests

Video downloads
Quality selection
Format handling
Mock Tests

YouTube API responses
Network errors
Rate limiting
'''


from youtube_downloader.downloader import YouTubeDownloader

urls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://www.youtube.com/embed/dQw4w9WgXcQ"
]

def test_url_propagation():
    for url in urls:
        downloader = YouTubeDownloader(url)
        assert downloader.url == url
       
def test_video_id_extraction():
    for url in urls:
        downloader = YouTubeDownloader(url)
        assert downloader.video_id == "dQw4w9WgXcQ"
        
def test_session_response():
    for url in urls:
        downloader = YouTubeDownloader(url)
        assert downloader.session.get(url).status_code == 200