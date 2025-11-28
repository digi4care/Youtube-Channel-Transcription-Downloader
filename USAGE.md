# Usage Guide

Complete usage guide for the YouTube Channel Transcript Downloader.

## Basic Usage

```bash
uv run python Youtube_Transcribe.py [options] <channel_or_video_url(s)>
```

## Examples

### Download transcript for a single YouTube video

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --transcript en
```

### Download English transcripts from a channel

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw --transcript en
```

### Download multiple languages

```bash
uv run python Youtube_Transcribe.py https://youtube.com/c/channel1 --transcript en --transcript es --transcript fr
```

### Download all available languages

```bash
uv run python Youtube_Transcribe.py https://youtube.com/c/channel1 -all
```

### Create configuration file

```bash
uv run python Youtube_Transcribe.py --create-config
```

## Command Line Options

- `--create-config`    Create default config.toml file
- `--show-config`      Show current configuration
- `-t LANG, --transcript LANG`  Language code for transcripts. Can be repeated for multiple languages (e.g., `-t en -t es -t fr`)
- `-all`               Download all available languages for each video
- `-txt`               Download only TXT files (no JSON)
- `-json`              Download only JSON files (no TXT)
- `--advanced-filename-sanitize`  Use WordPress-style advanced filename sanitization
- `-h, --help`         Show help message

## Audio/Video Format Selection

The script supports all yt-dlp format options, allowing you to download audio-only, video-only, or custom format combinations.

### Audio-Only Downloads

Download only audio (perfect for music playlists or podcasts):

```bash
# Best available audio quality
uv run python Youtube_Transcribe.py <URL> --format "bestaudio/best" --transcript en

# Extract and convert to MP3 (requires ffmpeg)
uv run python Youtube_Transcribe.py <URL> -x --audio-format mp3 --transcript en

# Specific audio format
uv run python Youtube_Transcribe.py <URL> --format "bestaudio[ext=m4a]" --transcript en

# Audio with specific quality
uv run python Youtube_Transcribe.py <URL> --format "ba[abr>=128]" --transcript en
```

### Video Downloads

Download video with optional audio:

```bash
# Best video + audio
uv run python Youtube_Transcribe.py <URL> --format "bestvideo+bestaudio/best" --transcript en

# Video only (no audio)
uv run python Youtube_Transcribe.py <URL> --format "bestvideo" --transcript en

# Specific resolution
uv run python Youtube_Transcribe.py <URL> --format "best[height<=1080]" --transcript en

# Combine with transcript download
uv run python Youtube_Transcribe.py <URL> --format "bestaudio" --transcript en
```

### Playlist-Specific Options

```bash
# Download only first 10 videos from playlist
uv run python Youtube_Transcribe.py <PLAYLIST_URL> --format "bestaudio" -I 1:10 --transcript en

# Download specific videos (1, 5, 10, 15)
uv run python Youtube_Transcribe.py <PLAYLIST_URL> --format "bestaudio" -I 1,5,10,15 --transcript en
```

### Common Format Codes

- `bestaudio/ba` - Best audio only
- `bestvideo/bv` - Best video only
- `best/b` - Best combined (video + audio)
- `bestaudio[ext=m4a]` - M4A audio format
- `best[height<=720]` - Max 720p video
- `worst/w` - Lowest quality (not recommended)

### Setting Default Format in config.toml

```toml
[yt_dlp.options]
# Audio-only as default
format = "bestaudio/best"
skip_download = false  # Enable audio/video download

# For transcripts only (default)
# format = ""
# skip_download = true
```

**Note:** Audio/video downloads require ffmpeg for format conversion and merging. Transcripts are downloaded separately regardless of video/audio settings.

---

**← Back to [README.md](../README.md)**
