# CLI Options Reference

This document provides a complete reference for all CLI options available in YouTube Channel Transcript Downloader v2.0.

## Usage

```bash
uv run python Youtube_Transcribe.py [OPTIONS] <URL(s)>
```

## Priority Order

Configuration settings are applied in the following priority order (highest to lowest):

1. **CLI Flags** (user overrides)
2. **Environment Variables**
3. **config.toml**
4. **yt-dlp defaults**
5. **Application defaults**

---

## Application Flags

### `--create-config`

<<<<<<< HEAD
Create a default `config.toml` file with all available options.

**Example:**
=======

Create a default `config.toml` file with all available options.

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --create-config
```

### `--show-config`

<<<<<<< HEAD
Display the current configuration (after applying all overrides).

**Example:**
=======

Display the current configuration (after applying all overrides).

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --show-config
```

### `-h, --help`

<<<<<<< HEAD
Show the help message with usage instructions and examples.

**Example:**
=======

Show the help message with usage instructions and examples.

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --help
```

---

## yt-dlp Flags (Passthrough)

These flags are passed directly to yt-dlp with the same names and behavior. See [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage) for details.

### `--output-template TEMPLATE`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Override the yt-dlp output template for video filenames.

**Default:** `%(title)s [%(id)s].%(ext)s`

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --output-template "%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s" <URL>
```

### `--skip-download`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Skip video download (transcripts only mode).

**Default:** `True`

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --skip-download <URL>
```

### `--format FORMAT`

<<<<<<< HEAD
Video format selector for yt-dlp.

**Example:**
=======

Video format selector for yt-dlp.

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --format "bestvideo+bestaudio/best" <URL>
```

### `--format-sort SORTORDER`

<<<<<<< HEAD
Format sort order for yt-dlp.

**Example:**
=======

Format sort order for yt-dlp.

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --format-sort "res,codec" <URL>
```

### `--sleep-interval SECONDS`

<<<<<<< HEAD
Seconds to sleep between requests (yt-dlp rate limiting).

**Example:**
=======

Seconds to sleep between requests (yt-dlp rate limiting).

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --sleep-interval 2.0 <URL>
```

### `--verbose`

<<<<<<< HEAD
Enable verbose yt-dlp output.

**Example:**
=======

Enable verbose yt-dlp output.

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --verbose <URL>
```

### `--quiet`

<<<<<<< HEAD
Enable quiet yt-dlp output (suppress warnings).

**Example:**
=======

Enable quiet yt-dlp output (suppress warnings).

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --quiet <URL>
```

---

## Transcript-Specific Flags

These flags control transcript-specific behavior.

### `--transcript-format FORMAT`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Transcript format to download.

**Choices:** `txt`, `json`, `srt`, `vtt`

**Default:** `txt, json` (both)

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --transcript-format json <URL>
```

### `--concurrent-workers N`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Number of concurrent transcript downloads.

**Default:** `3`

**Range:** 1-10

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --concurrent-workers 5 <URL>
```

### `--batch-size N`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Number of videos to process per batch.

**Default:** `100`

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --batch-size 50 <URL>
```

### `--default-language CODE`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Default transcript language code.

**Default:** `en`

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --default-language es <URL>
```

### `--overwrite-existing`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Overwrite existing transcript files.

**Default:** `False` (skip existing files)

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --overwrite-existing <URL>
```

### `--no-organize`

<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration
Disable file organization into language folders.

**Default:** `False` (organize enabled)

**Example:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py --no-organize <URL>
```

---

## Standard Flags

### `-t LANG, --transcript LANG`

<<<<<<< HEAD
Specify transcript language code. Can be repeated for multiple languages.

**Example:**
=======

Specify transcript language code. Can be repeated for multiple languages.

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py <URL> -t en -t es -t fr
```

**Shorthand:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py <URL> -en -es -fr
```

### `-all`

<<<<<<< HEAD
Download all available languages for each video.

**Example:**
=======

Download all available languages for each video.

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py <URL> -all
```

### `-txt`

<<<<<<< HEAD
Download only TXT format (no JSON).

**Example:**
=======

Download only TXT format (no JSON).

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py <URL> -txt
```

### `-json`

<<<<<<< HEAD
Download only JSON format (no TXT).

**Example:**
=======

Download only JSON format (no TXT).

**Example:**

>>>>>>> feature/phase2-ytdlp-integration

```bash
uv run python Youtube_Transcribe.py <URL> -json
```

---

## URL Format

You can specify one or more YouTube URLs:

```bash
uv run python Youtube_Transcribe.py <URL1> <URL2> <URL3>
```

**Supported URL types:**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

- Single video: `https://www.youtube.com/watch?v=VIDEO_ID`
- Channel: `https://www.youtube.com/channel/CHANNEL_ID`
- Channel (custom): `https://www.youtube.com/c/CHANNEL_NAME`
- User: `https://www.youtube.com/user/USERNAME`
- Playlist: `https://www.youtube.com/playlist?list=PLAYLIST_ID`

---

## Environment Variables

You can override configuration using environment variables. These have higher priority than config.toml but lower than CLI flags.

### Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `YTD_OUTPUT` | yt-dlp output template | `YTD_OUTPUT="%(title)s.%(ext)s"` |
| `YTD_SKIP_DOWNLOAD` | Skip video download | `YTD_SKIP_DOWNLOAD=true` |
| `YTD_SLEEP_INTERVAL` | yt-dlp sleep interval | `YTD_SLEEP_INTERVAL=2.0` |
| `YTD_CONCURRENT_WORKERS` | Concurrent transcript workers | `YTD_CONCURRENT_WORKERS=5` |
| `YTD_BATCH_SIZE` | Batch size | `YTD_BATCH_SIZE=50` |
| `YTD_DEFAULT_LANGUAGE` | Default language | `YTD_DEFAULT_LANGUAGE=es` |
| `YTD_BASE_DELAY` | Base delay (seconds) | `YTD_BASE_DELAY=2.0` |
| `YTD_MAX_WORKERS` | Max workers | `YTD_MAX_WORKERS=5` |
| `YTD_RATE_STRATEGY` | Rate strategy | `YTD_RATE_STRATEGY=conservative` |
| `YTD_LOG_LEVEL` | Log level | `YTD_LOG_LEVEL=DEBUG` |
| `YTD_LOG_FILE` | Log file path | `YTD_LOG_FILE=/var/log/ytd.log` |
| `YTD_LOG_YTDLP_COMMANDS` | Log yt-dlp commands | `YTD_LOG_YTDLP_COMMANDS=true` |

### Example Usage

```bash
YTD_CONCURRENT_WORKERS=5 YTD_DEFAULT_LANGUAGE=es uv run python Youtube_Transcribe.py <URL> -en
```

---

## Configuration File (config.toml)

For persistent configuration, edit `config.toml`:

### Sections

- **`[yt_dlp.options]`** - yt-dlp options passed directly to yt-dlp
- **`[transcripts]`** - Transcript-specific settings
- **`[rate_limiting]`** - Rate limiting and retry settings
- **`[api_settings]`** - YouTube API settings
- **`[ui]`** - UI and display settings
- **`[logging]`** - Logging configuration
- **`[performance]`** - Performance tuning

### Example config.toml

```toml
[yt_dlp.options]
output = "%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s"
skip_download = true
format = "bestvideo+bestaudio/best"
sleep_interval = 1.5

[transcripts]
download_formats = ["txt", "json"]
use_language_folders = true
default_language = "en"
concurrent_workers = 3
batch_size = 100

[rate_limiting]
base_delay = 1.5
max_workers = 3
rate_strategy = "balanced"
```

---

## Complete Examples

### Download English transcripts from a channel

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC_CHANNEL_ID -en
```

### Download multiple languages

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC_CHANNEL_ID -en -es -fr
```

### Download with custom output template

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC_CHANNEL_ID -en \
  --output-template "%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s"
```

### Download all available languages

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC_CHANNEL_ID -all
```

### Use faster settings for testing

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC_CHANNEL_ID -en \
  --concurrent-workers 10 --batch-size 200
```

### Use conservative settings for large channels

```bash
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC_CHANNEL_ID -en \
  --concurrent-workers 2 --sleep-interval 3.0
```

### Download with environment variables

```bash
YTD_CONCURRENT_WORKERS=2 YTD_DEFAULT_LANGUAGE=es \
uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC_CHANNEL_ID -en
```

### Show current configuration

```bash
uv run python Youtube_Transcribe.py --show-config
```

---

## Notes

- **URLs must be last** in the command line (after all flags)
- **Language codes** follow ISO 639-1 standard (en, es, fr, de, etc.)
- **Rate limiting** is applied automatically to avoid IP bans
- **Existing files** are skipped by default (use `--overwrite-existing` to override)
- **File organization** creates language-specific subdirectories by default

---

## Troubleshooting

### Common Issues

**"No transcript available"**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

- Video doesn't have subtitles or they're disabled
- Try a different language

**"Rate limited"**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

- YouTube is temporarily blocking your IP
- Wait 5-7 minutes and try again with slower settings

**"Video unavailable"**
<<<<<<< HEAD
=======

>>>>>>> feature/phase2-ytdlp-integration

- Video is private, deleted, or region-locked
- Cannot be processed

### Getting Help

```bash
uv run python Youtube_Transcribe.py --help
```

For more information, see the main [README.md](README.md).
