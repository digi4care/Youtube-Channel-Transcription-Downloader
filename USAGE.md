# Usage Guide

Complete usage guide for the YouTube Channel Transcript Downloader.

## Basic Usage

```bash
uv run python Youtube_Transcribe.py [options] <channel_or_video_url(s)>
```

## Examples

📖 **Complete examples collection**: **[EXAMPLES.md](EXAMPLES.md)**

### Basic Examples

- **Download transcript for a single YouTube video**

  ```bash
  uv run python Youtube_Transcribe.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -t en
  ```

- **Download English transcripts from a channel**

  ```bash
  uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw -t en
  ```

- **Download all available languages**

  ```bash
  uv run python Youtube_Transcribe.py https://youtube.com/c/channel1 -all
  ```

See **[EXAMPLES.md](EXAMPLES.md)** for complete examples including audio/video downloads and advanced format options.

---

**← Back to [README.md](../README.md)**
