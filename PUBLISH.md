# Publishing to PyPI

## 1. Update package info in pyproject.toml

Edit `pyproject.toml` and update:
- `name` (if "yt-saver" is taken, choose another)
- `version`
- `authors` (your name and email)
- `Homepage` and `Repository` URLs

## 2. Build the package

```bash
cd youtube-downloader
uv run python -m build
```

This creates `dist/` folder with `.whl` and `.tar.gz` files.

## 3. Create PyPI account

- Go to https://pypi.org/account/register/
- Verify your email
- Enable 2FA (required)
- Create API token at https://pypi.org/manage/account/token/

## 4. Upload to TestPyPI (optional, recommended first)

```bash
uv run twine upload --repository testpypi dist/*
```

Username: `__token__`
Password: Your TestPyPI API token

Test install:
```bash
pip install --index-url https://test.pypi.org/simple/ ytsnap
```

## 5. Upload to PyPI

```bash
uv run twine upload dist/*
```

Username: `__token__`
Password: Your PyPI API token

## 6. Install and test

```bash
pip install ytsnap
ytsnap "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Using in your project

### Install from PyPI
```bash
pip install ytsnap
```

### Use as library
```python
from youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader("https://www.youtube.com/watch?v=VIDEO_ID")
downloader.download("output.mp4")
```

### Install from local directory (for development)
```bash
pip install -e /path/to/youtube-downloader
```

## Updating the package

1. Update version in `pyproject.toml`
2. Rebuild: `uv run python -m build`
3. Upload: `uv run twine upload dist/*`
