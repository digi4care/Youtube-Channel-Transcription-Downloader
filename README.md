# YouTube Channel Transcript Downloader

> **Note**: This is an enhanced fork of the original project by [titusrugabunda](https://github.com/rugabunda).
> The original project can be found at: <https://github.com/rugabunda/youtube-transcript-downloader>

## Credits

- Original Author: [titusrugabunda](https://github.com/rugabunda)
- Forked and Enhanced by: [digi4care](https://github.com/digi4care)

## About This Fork

This version includes various improvements and extensions over the original project. You're welcome to contribute to make it even better!

### 📋 What's New

See **[CHANGELOG.md](CHANGELOG.md)** for detailed version history and feature updates.

### Key Features (v2.2)

- ✅ **Archive & Resume**: Automatic recovery from rate limiting interruptions
- ✅ **Advanced Filename Sanitization**: Optional WordPress-style filename cleaning
- ✅ **Smart Language Detection**: Only when needed, respects explicit language choices
- ✅ **TOML Configuration**: User-friendly configuration management
- ✅ **Rate Limit Optimization**: No wasted API calls

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

📖 **Complete setup instructions**: **[SETUP.md](SETUP.md)**

Quick setup with uv:

```bash
git clone https://github.com/digi4care/Youtube-Channel-Transcription-Downloader.git
cd Youtube-Channel-Transcription-Downloader
uv venv && source .venv/bin/activate && uv sync
python Youtube_Transcribe.py --create-config
```

## Usage

📖 **Complete usage guide**: **[USAGE.md](USAGE.md)**

Basic usage:

```bash
uv run python Youtube_Transcribe.py [options] <channel_or_video_url(s)>
```

### Examples

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

### Command Line Options

- `-t LANG, --transcript LANG`  Language code for transcripts. Can be repeated for multiple languages (e.g., `-t en -t es -t fr`)
- `-all`               Download all available languages for each video
- `--advanced-filename-sanitize`  Use WordPress-style advanced filename sanitization
- `--create-config`    Create default config.toml file
- `--show-config`      Show current configuration
- `-h, --help`         Show help message

See **[USAGE.md](USAGE.md)** for complete options, audio/video formats, and advanced examples.

## Configuration

The script uses a `config.toml` file for easy configuration management:

### Creating Configuration

   ```bash
   # Create default config file
   python Youtube_Transcribe.py --create-config
   python Youtube_Transcribe.py --show-config
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
   YTD_BASE_DELAY=3 YTD_MAX_WORKERS=2 python Youtube_Transcribe.py https://youtube.com/c/channel1 --transcript en
   ```

## Archive & Resume Functionaliteit

> **Nieuwe feature in v2.1** - Lost het probleem op van rate limiting onderbrekingen bij grote kanaal downloads!

### Wat is Archive Functionaliteit?

De archive functionaliteit houdt automatisch bij welke videos al succesvol gedownload zijn, zodat het script kan hervatten waar het gebleven was na rate limiting of onderbrekingen.

### Hoe het werkt

1. **Per kanaal archive bestand**: `.transcript_archive.txt` in elke kanaal directory
2. **Automatisch hervatten**: Slaat al verwerkte videos over bij volgende runs
3. **API rate limit besparing**: Geen onnodige YouTube Transcript API calls
4. **Backward compatible**: Werkt met bestaande installs

### Voorbeeld Workflow

```bash
# Eerste run - grote kanaal met 100 videos
uv run python Youtube_Transcribe.py https://youtube.com/@BigChannel -t en
# Downloadt eerste 40 videos, raakt rate limit

# Volgende dag - hervat automatisch
uv run python Youtube_Transcribe.py https://youtube.com/@BigChannel -t en
# Slaat eerste 40 over, downloadt videos 41-80
# Archive bestand toont: 80 verwerkte videos
```

### Archive Bestand Formaat

```text
downloads/BigChannel/.transcript_archive.txt
├── V5IhsHEHXOg  # Video ID 1
├── dQw4w9WgXcQ  # Video ID 2
└── ...          # Alle verwerkte videos
```

### Configuratie

Archive is standaard **ingeschakeld**. Uitschakelen in `config.toml`:

```toml
[transcripts]
enable_archive = false  # Archive uitschakelen (niet aanbevolen)
```

### Voordelen

- ✅ **Geen verloren werk** bij rate limiting
- ✅ **Bespaart API calls** - verlengt YouTube Transcript API quota
- ✅ **Snellere hervatting** - slaat verwerkte videos direct over
- ✅ **Veilig** - archive bestanden zijn eenvoudig tekst en herstelbaar
- ✅ **Per kanaal** - verschillende kanalen verstoren elkaar niet

### Troubleshooting Archive

- **Archive bestand ontbreekt?** Script maakt het automatisch aan
- **Archive bestand corrupt?** Verwijder het bestand - script begint opnieuw
- **Wil archive resetten?** Verwijder `.transcript_archive.txt` uit kanaal directory
- **Archive niet gebruiken?** Stel `enable_archive = false` in config

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
