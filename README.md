# YouTube Channel Transcript Downloader

> **Note**: This is an enhanced fork of the original project by [titusrugabunda](https://github.com/rugabunda).
> The original project can be found at: <https://github.com/rugabunda/youtube-transcript-downloader>

## Credits

- Original Author: [titusrugabunda](https://github.com/rugabunda)
- Forked and Enhanced by: [digi4care](https://github.com/digi4care)

## About This Fork

This version includes various improvements and extensions over the original project. You're welcome to contribute to make it even better!

### Version 2.0 - Refactored Architecture

The v2 version (`Youtube.Transcribe.py`) features:

- **SOLID Principles**: Clean, maintainable code architecture
- **TOML Configuration**: User-friendly configuration file (`config.toml`)
- **Class-Based Design**: Modular components for better testing and extension
- **Enhanced Rate Limiting**: Multiple strategies and better ban recovery
- **Improved Error Handling**: More robust error management
- **Flexible Configuration**: Override settings via environment variables

### Quick Start with v2

1. **Create default configuration**:

   ```bash
   python Youtube.Transcribe.py --create-config
   ```

2. **Edit `config.toml`** to customize settings like rate limiting, output formats, etc.

3. **Run with your preferred configuration**:

   ```bash
   python Youtube.Transcribe.py https://youtube.com/c/channel1 -en
   ```

## Requirements

- Python 3.11+
- uv package manager (recommended) OR pip

All requirements are listed in `pyproject.toml` and `requirements.txt`.

## Setup

### Option 1: Using UV (Recommended)

1. **Clone the repository**

   ```bash
   git clone https://github.com/digi4care/Youtube-Channel-Transcription-Downloader.git
   cd Youtube-Channel-Transcription-Downloader
   ```

2. **Install dependencies with UV**

   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install all dependencies
   uv sync
   ```

3. **Run the application**

   ```bash
   # Create configuration
   uv run python Youtube.Transcribe.py --create-config
   
   # Download transcripts
   uv run python Youtube.Transcribe.py https://youtube.com/c/channel1 -en
   ```

### Option 2: Using pip (Traditional)

1. **Clone the repository**

   ```bash
   git clone https://github.com/digi4care/Youtube-Channel-Transcription-Downloader.git
   cd Youtube-Channel-Transcription-Downloader
   ```

2. **Create and activate a virtual environment**

   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required packages**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python Youtube.Transcribe.py --create-config
   python Youtube.Transcribe.py https://youtube.com/c/channel1 -en
   ```

## Usage

### Version 2.0 (Recommended)

```bash
uv run python Youtube.Transcribe.py [options] <channel_or_video_url(s)>
```

### Version 1.0 (Original)

```bash
python Youtube.Transcribe.py [options] <channel_or_video_url(s)>
```

## Examples

### Version 2.0 Examples

- **Download transcript for a single YouTube video**

  ```bash
  uv run python Youtube.Transcribe.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -en
  ```

- **Download English transcripts from a channel**

  ```bash
  uv run python Youtube.Transcribe.py https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw -en
  ```

- **Download multiple languages**

  ```bash
  uv run python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -es -fr
  ```

- **Download all available languages**

  ```bash
  uv run python Youtube.Transcribe.py https://youtube.com/c/channel1 -all
  ```

- **Download from channels listed in a file**

  ```bash
  uv run python Youtube.Transcribe.py -f channels.lst -en
  ```

- **Create configuration file**

  ```bash
  uv run python Youtube.Transcribe.py --create-config
  ```

### Version 1.0 Examples (Original)

- **Download transcript for a single YouTube video**

  ```bash
  python Youtube.Transcribe.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -en
  ```

- **Download English transcripts from a channel**

  ```bash
  python Youtube.Transcribe.py https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw -en
  ```

- **Download multiple languages**

  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -es -fr
  ```

- **Download all available languages**

  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 -all
  ```

- **Download only TXT files (no JSON)**

  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -txt
  ```

- **Faster downloads (may increase risk of IP ban)**

  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -delay 1 -workers 5
  ```

- **Download from channels listed in a file**

  ```bash
  python Youtube.Transcribe.py -f channels.lst -en
  ```

## Options

### Version 2.0 Options

- `-f, --file FILE`    Read channel URLs from a text file (one per line or comma-separated)
- `--create-config`    Create default config.toml file
- `--show-config`      Show current configuration
- `-LANG`              Language code for transcripts (e.g., `-en` for English). Multiple language codes can be specified (e.g., `-en -es -fr`)
- `-all`               Download all available languages for each video
- `-txt`               Download only TXT files (no JSON)
- `-json`              Download only JSON files (no TXT)
- `-delay N`           Delay between API requests in seconds (default: 1.5). Higher values reduce risk of IP bans but slow downloads
- `-workers N`         Number of concurrent downloads (default: 3, range: 1-10). Lower values reduce risk of IP bans but slow downloads
- `-h, --help`         Show help message

### Version 1.0 Options (Original)

- `-f, --file FILE`    Read channel URLs from a text file (one per line or comma-separated)
- `-LANG`              Language code for transcripts (e.g., `-en` for English). Multiple language codes can be specified (e.g., `-en -es -fr`)
- `-all`               Download all available languages for each video
- `-txt`               Download only TXT files (no JSON)
- `-json`              Download only JSON files (no TXT)
- `-delay N`           Delay between API requests in seconds (default: 1.5). Higher values reduce risk of IP bans but slow downloads
- `-workers N`         Number of concurrent downloads (default: 3, range: 1-10). Lower values reduce risk of IP bans but slow downloads
- `-h, --help`         Show help message

## Configuration (v2)

The v2 version uses a `config.toml` file for easy configuration management:

### Creating Configuration

```bash
# Create default config file
python Youtube.Transcribe.py --create-config

# View current configuration
python Youtube.Transcribe.py --show-config
```

### Configuration Sections

**[rate_limiting]** - Control download speed and safety:

- `base_delay`: Delay between requests (seconds)
- `max_workers`: Concurrent downloads (1-10)
- `strategy`: "conservative", "balanced", or "aggressive"

**[file_handling]** - Control file organization:

- `output_dir`: Where to save transcripts
- `use_language_folders`: Organize by language
- `download_formats`: ["txt"], ["json"], or both

**[ui_settings]** - Control the interface:

- `show_progress`: Show progress bars
- `clear_screen`: Clear screen on startup
- `color_scheme`: Visual theme

**[advanced]** - Power user settings:

- `enable_cache`: Cache API responses
- `log_level`: Logging verbosity
- `log_file`: Save logs to file

### Environment Variables

Override config with environment variables:

- `YTD_DELAY`: Set base delay
- `YTD_WORKERS`: Set worker count
- `YTD_OUTPUT_DIR`: Set output directory
- `YTD_LOG_LEVEL`: Set log level
- `YTD_RATE_STRATEGY`: Set rate limiting strategy

Example:

```bash
YTD_DELAY=3 YTD_WORKERS=2 python Youtube.Transcribe.py https://youtube.com/c/channel1 -en
```

## Rate Limiting

To avoid YouTube IP bans, this script implements several protection measures:

1. Request delays: Controlled delay between API calls (adjust with `-delay`)
2. Random jitter: ±20% randomness added to each delay to avoid pattern detection
3. Limited concurrency: Restricted parallel downloads (adjust with `-workers`)
4. Smart retries: Automatic detection of non-retryable errors (age-restricted videos, etc.)
5. Exponential backoff: Increasingly longer delays after rate limit errors
6. Error skipping: No retry for videos that cannot have transcripts (subtitles disabled, etc.)

### Recommended Settings

- **Normal usage**: Default values (`-delay 1.5 -workers 3`)
- **If IP banned**:
  1. Switch to very slow settings (`-delay 5 -workers 1`) until ban is lifted
  2. After ban is lifted, continue with these slow settings for 5-7 minutes
  3. Then reduce to half your original speed (double delay, halve workers)
  4. If banned again, repeat the halving process until bans stop permanently

  Example: If original settings were `-delay 1 -workers 6`, after recovery use `-delay 2 -workers 3`, then `-delay 4 -workers 2` if banned again.

## File Organization

Files are organized based on languages detected and requested:

- **Single language mode** (when only one language exists or is requested):

  ```text
  ./transcripts/[Channel Name]/json/[Video Title]_[VideoID]_[lang].json
  ./transcripts/[Channel Name]/[Video Title]_[VideoID]_[lang].txt
  ```

- **Multiple language mode** (triggered when):
  - Multiple languages are requested in the command
  - Multiple languages already exist in the folder
  - A new language is requested that doesn't match existing files

  In this mode, files are organized as:

  ```text
  ./transcripts/[Channel Name]/[lang]/json/[Video Title]_[VideoID]_[lang].json
  ./transcripts/[Channel Name]/[lang]/[Video Title]_[VideoID]_[lang].txt
  ```

## Notes

- If no language is specified, your system language will be used
- If system language cannot be determined, English will be used
- Use Ctrl+C to properly terminate the script
- The script will automatically reorganize files when switching to multiple language mode

## File Format

The channel URL file can contain URLs in any of these formats:

- One URL per line
- Comma-separated URLs
- Comma with spaces between URLs

Example file content:

```text
https://youtube.com/channel/UC123, https://youtube.com/c/channel2
https://youtube.com/user/someuser
```

## Available Language Codes

- `-en`      - English                    - `-es`      - Spanish                    - `-fr`      - French
- `-de`      - German                     - `-it`      - Italian                    - `-pt`      - Portuguese
- `-ru`      - Russian                    - `-ja`      - Japanese                   - `-ko`      - Korean
- `-zh-Hans` - Chinese (Simplified)       - `-zh-Hant` - Chinese (Traditional)      - `-ar`      - Arabic
- `-hi`      - Hindi                      - `-bn`      - Bengali                    - `-nl`      - Dutch
- `-sv`      - Swedish                    - `-tr`      - Turkish                    - `-pl`      - Polish
- `-vi`      - Vietnamese                 - `-th`      - Thai                       - `-fa`      - Persian
- `-id`      - Indonesian                 - `-uk`      - Ukrainian                  - `-cs`      - Czech
- `-fi`      - Finnish                    - `-ro`      - Romanian                   - `-el`      - Greek
- `-he`      - Hebrew                     - `-da`      - Danish                     - `-no`      - Norwegian
- `-hu`      - Hungarian                  - `-bg`      - Bulgarian                  - `-hr`      - Croatian
- `-sk`      - Slovak                     - `-lt`      - Lithuanian                 - `-sl`      - Slovenian
- `-et`      - Estonian                   - `-lv`      - Latvian
