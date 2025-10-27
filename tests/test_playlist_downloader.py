"""Tests for PlaylistDownloader functionality"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from youtube_downloader.downloader import PlaylistDownloader


class TestPlaylistDownloader(unittest.TestCase):
    """Test cases for PlaylistDownloader"""

    def test_extract_playlist_id(self):
        """Test playlist ID extraction from various URL formats"""
        downloader = PlaylistDownloader("https://www.youtube.com/playlist?list=PLxxx")
        self.assertEqual(downloader.playlist_id, "PLxxx")
        
        downloader = PlaylistDownloader("https://www.youtube.com/playlist?list=PLabcdef")
        self.assertEqual(downloader.playlist_id, "PLabcdef")
        
        downloader = PlaylistDownloader("PLdirect")
        self.assertEqual(downloader.playlist_id, "PLdirect")
    
    def test_extract_playlist_id_invalid(self):
        """Test that invalid playlist URLs raise ValueError"""
        with self.assertRaises(ValueError):
            PlaylistDownloader("https://www.youtube.com/watch?v=VIDEO_ID")
        
        with self.assertRaises(ValueError):
            PlaylistDownloader("not_a_playlist_url")
    
    def test_concurrency_config(self):
        """Test that concurrency is properly configured"""
        downloader = PlaylistDownloader("https://www.youtube.com/playlist?list=PLxxx", concurrency=5)
        self.assertEqual(downloader.concurrency, 5)
        
        downloader = PlaylistDownloader("https://www.youtube.com/playlist?list=PLxxx", concurrency=1)
        self.assertEqual(downloader.concurrency, 1)
        
        # Test default
        downloader = PlaylistDownloader("https://www.youtube.com/playlist?list=PLxxx")
        self.assertEqual(downloader.concurrency, 3)
    
    def test_get_videos_empty_playlist(self):
        """Test handling of empty playlist"""
        downloader = PlaylistDownloader("https://www.youtube.com/playlist?list=PLxxx")
        
        with patch.object(downloader, '_get_playlist_info', return_value={'contents': {}}):
            with patch.object(downloader, '_extract_videos_from_playlist_info', return_value=[]):
                with self.assertRaises(Exception) as context:
                    downloader.get_videos()
                
                self.assertIn("No videos found", str(context.exception))
    
    def test_download_statistics(self):
        """Test that download returns proper statistics"""
        downloader = PlaylistDownloader("https://www.youtube.com/playlist?list=PLxxx", concurrency=1)
        
        # Mock videos
        mock_videos = [
            {'video_id': 'vid1', 'title': 'Video 1', 'url': 'https://www.youtube.com/watch?v=vid1'},
            {'video_id': 'vid2', 'title': 'Video 2', 'url': 'https://www.youtube.com/watch?v=vid2'}
        ]
        
        with patch.object(downloader, 'get_videos', return_value=mock_videos):
            with patch.object(downloader, '_download_single_video', return_value=True):
                with patch('os.makedirs'):
                    with patch('os.path.exists', return_value=False):
                        import os
                        os.path.join = lambda *args: '/'.join(args)
                        stats = downloader.download(output_dir="./test")
                        
                        self.assertEqual(stats['total'], 2)
                        self.assertEqual(stats['successful'], 2)
                        self.assertEqual(stats['failed'], 0)


if __name__ == '__main__':
    unittest.main()

