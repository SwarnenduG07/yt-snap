from youtube_downloader.downloader import YouTubeDownloader

def test_video_id_extraction():
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ"
    ]
    for url in urls:
        downloader = YouTubeDownloader(url)
        assert downloader.video_id == "dQw4w9WgXcQ"