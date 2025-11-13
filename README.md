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

## 🚀 Future Ideas

Interested in where this project could go next? Check out **[IDEAS.md](IDEAS.md)** to see:

- Potential API server mode for programmatic access
- Web dashboard concepts
- Enhanced CLI features
- Performance improvements

*These are exploratory ideas - not committed features. Community feedback welcome!*

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

2. **Install uv if you haven't already**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Create a virtual environment and install dependencies**

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

4. **Update the virtual environment** (important for YouTube compatibility)

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install --upgrade certifi charset-normalizer idna requests urllib3 youtube-transcript-api yt-dlp
   uv pip install --upgrade $(grep -v '^#' requirements.txt | cut -d= -f1)
   uv pip freeze > requirements.txt
   uv pip list --outdated
   ```

   **Why these updates are crucial:**
   - **yt-dlp**: YouTube frequently changes their API and website structure. Keeping yt-dlp up-to-date is essential for the script to continue working with YouTube
   - **youtube-transcript-api**: YouTube's transcript system also changes regularly
   - **uv pip list --outdated**: Shows you which packages need updates so you can stay current
   - **uv pip freeze > requirements.txt**: Updates your requirements file with the latest working versions

5. **Run the application**

   ```bash
   # Create configuration
   python Youtube.Transcribe.py --create-config
   
   # Download transcripts
   python Youtube.Transcribe.py https://youtube.com/c/channel1 -en
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

## Quick Start

Get up and running in 3 simple steps:

1. **Create default configuration**:

   ```bash
   python Youtube.Transcribe.py --create-config
   ```

2. **Edit `config.toml`** to customize settings like rate limiting, output formats, etc.

3. **Run with your preferred configuration**:

   ```bash
   python Youtube.Transcribe.py https://youtube.com/c/channel1 -en
   ```

## Usage

```bash
uv run python Youtube.Transcribe.py [options] <channel_or_video_url(s)>
```

## Examples

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

## Options

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

## Configuration

The script uses a `config.toml` file for easy configuration management:

### Creating Configuration

   ```bash
   # Create default config file
   python Youtube.Transcribe.py --create-config
   python Youtube.Transcribe.py --show-config
   ```

### Configuration Sections

The config file is organized into logical sections:

- **rate_limiting**: Controls request delays, workers, and ban recovery
- **file_handling**: Manages output directories and file formats
- **api_settings**: Configures timeouts and batch processing
- **ui_settings**: Controls progress bars and visual feedback
- **advanced**: Cache, logging, and performance options

### Environment Variables

You can override any configuration setting using environment variables:

   ```bash
   YTD_DELAY=3 YTD_WORKERS=2 python Youtube.Transcribe.py https://youtube.com/c/channel1 -en
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

- **Normal usage**: Default values (1.5s delay, 3 workers)
- **If IP banned**: Switch to very slow settings (5s delay, 1 worker) until ban is lifted
- **After ban lifted**: Continue with slow settings for 5-7 minutes, then reduce to half speed
- **Repeat halving** until bans stop permanently

## Troubleshooting

### Common Issues and Solutions

- **"No transcript available"**: The video doesn't have subtitles or they're disabled
- **"Video unavailable"**: The video is private, deleted, or region-locked
- **"Rate limited"**: YouTube is temporarily blocking your IP - wait 5-7 minutes
- **"Age restricted"**: These videos require authentication and can't be processed
- **"Subtitles disabled"**: The creator has disabled subtitles for this video

### Performance Tips

- **For large channels**: Start with conservative settings (3s delay, 2 workers)
- **For quick tests**: Use faster settings (1s delay, 5 workers) but monitor for bans
- **For batch processing**: Use the `-f` option to process multiple channels from a file
- **Resume downloads**: The script automatically skips existing files

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

This project uses pre-commit hooks to maintain code quality and consistency. These hooks automatically check your code for style issues, formatting, and potential bugs before each commit.

#### Why Use Pre-commit Hooks?

Pre-commit hooks help you:

- Catch errors before they're committed
- Maintain consistent code style across the project
- Automatically format your code
- Prevent common issues like trailing whitespace or large files
- Ensure type safety with static type checking

#### Prerequisites

- Python 3.8+
- `uv` package manager (faster alternative to pip)

#### Installation

1. **Install pre-commit using uv**:

   ```bash
   uv pip install pre-commit
   ```

2. **Install the git hooks**:

   ```bash
   uv run pre-commit install
   ```

   This sets up the hooks to run automatically on every `git commit`.

3. **Run the hooks manually** (optional):

   ```bash
   uv run pre-commit run --all-files
   ```

   This will run all checks on your entire codebase.

#### What Each Hook Does

- **Black**: Automatically formats your Python code to be consistent
- **isort**: Sorts your Python imports in a standard way
- **Ruff**: A fast linter that catches common errors and style issues
- **mypy**: Static type checker that helps catch type-related bugs
- **File validators**: Check YAML, JSON, and TOML files for syntax errors
- **Basic checks**: Ensure consistent line endings, no trailing whitespace, etc.

#### First Time Setup

The first time you run the hooks, they will install their required environments. This might take a minute or two. Subsequent runs will be much faster.

#### Fixing Issues

If a hook finds issues:

1. Many issues can be fixed automatically. The hook will tell you if it can fix them.
2. For other issues, the hook will show you exactly what needs to be fixed and where.
3. After fixing the issues, stage your changes and try committing again.

#### Skipping Hooks (When Needed)

If you need to skip the hooks for a single commit (not recommended for regular use):

```bash
git commit --no-verify -m "Your commit message"
```

Remember: The pre-commit hooks are there to help maintain code quality, so please try to fix any issues they find rather than skipping them.
