# Configuration Guide

Complete configuration guide for the YouTube Channel Transcript Downloader.

## Configuration File

The script uses a `config.toml` file for easy configuration management:

### Creating Configuration

```bash
# Create default config file
python Youtube_Transcribe.py --create-config

# Show current configuration
python Youtube_Transcribe.py --show-config
```

### Configuration Sections

The config file is organized into logical sections:

- **transcripts**: Language, file format, and sanitization settings
- **rate_limiting**: Request delays, workers, and ban recovery
- **api_settings**: Timeouts and cache configuration
- **ui**: Progress bars and visual feedback
- **logging**: Log levels and file output

### Environment Variables

You can override any configuration setting using environment variables:

```bash
YTD_BASE_DELAY=3 YTD_MAX_WORKERS=2 python Youtube_Transcribe.py https://youtube.com/c/channel1 --transcript en
```

## Archive & Resume Feature

> **New feature in v2.1** - Solves the problem of rate limiting interruptions for large channel downloads!

### What is Archive Functionality?

The archive functionality automatically tracks which videos have been successfully downloaded, allowing the script to resume where it left off after rate limiting or interruptions.

### How it Works

1. **Per-channel archive file**: `.transcript_archive.txt` in each channel directory
2. **Automatic resume**: Skips already processed videos on subsequent runs
3. **API rate limit optimization**: No unnecessary YouTube Transcript API calls
4. **Backward compatible**: Works with existing installations

### Example Workflow

```bash
# First run - large channel with 100 videos
uv run python Youtube_Transcribe.py https://youtube.com/@BigChannel -t en
# Downloads first 40 videos, hits rate limit

# Next day - resumes automatically
uv run python Youtube_Transcribe.py https://youtube.com/@BigChannel -t en
# Skips first 40, downloads videos 41-80
# Archive file shows: 80 processed videos
```

### Archive File Format

```text
downloads/BigChannel/.transcript_archive.txt
├── V5IhsHEHXOg  # Video ID 1
├── dQw4w9WgXcQ  # Video ID 2
└── ...          # All processed videos
```

### Configuration

Archive is **enabled by default**. Disable in `config.toml`:

```toml
[transcripts]
enable_archive = false  # Disable archive (not recommended)
```

### Benefits

- ✅ **No lost work** from rate limiting
- ✅ **Saves API calls** - extends YouTube Transcript API quota
- ✅ **Faster resume** - instantly skips already done videos
- ✅ **Safe** - archive files are simple text and recoverable
- ✅ **Per-channel** - different channels don't interfere

### Archive Troubleshooting

- **Archive file missing?** Script creates it automatically
- **Archive file corrupted?** Delete the file - script starts fresh
- **Want to reset archive?** Delete `.transcript_archive.txt` from channel directory
- **Don't want archive?** Set `enable_archive = false` in config

## Advanced Filename Sanitization

Choose between basic and advanced filename sanitization:

### Basic Mode (Default)

```python
"café spécial.mp4" → "café spécial.mp4"  # Only removes filesystem-dangerous chars
```

### Advanced Mode

```python
"café spécial.mp4" → "cafe-special.mp4"  # WordPress-style cleaning
```

### Configuration

```toml
[transcripts]
advanced_filename_sanitize = true  # Enable WordPress-style sanitization
```

Or use CLI flag:

```bash
uv run python Youtube_Transcribe.py [url] --advanced-filename-sanitize
```

## Rate Limiting

This script implements sophisticated rate limiting to avoid YouTube IP bans:

### Why Rate Limiting Matters

YouTube monitors API requests and may temporarily block IPs that make too many requests too quickly. This script includes multiple protection mechanisms:

### Protection Mechanisms

- **Request Delays**: Configurable delays between requests with random jitter
- **Concurrent Workers**: Limited parallel downloads to prevent overwhelming YouTube
- **Smart Retries**: Automatic detection of retryable vs non-retryable errors
- **Exponential Backoff**: Increasing delays after rate limit errors
- **Ban Recovery**: Automatic adjustment of settings when bans are detected

### Recommended Settings

- **Normal usage**: Default values (1.5s delay, 1 worker)
- **If IP banned**: Switch to very slow settings (5s delay, 1 worker) until ban is lifted
- **After ban lifted**: Continue with slow settings for 5-7 minutes, then reduce to half speed
- **Repeat halving** until bans stop permanently

### Configuration

```toml
[rate_limiting]
base_delay = 1.5      # Delay between requests in seconds
max_workers = 1       # Number of concurrent downloads
max_retries = 3       # Maximum retry attempts
rate_strategy = "balanced"  # conservative/balanced/aggressive
```

---

**← Back to [README.md](../README.md)**
