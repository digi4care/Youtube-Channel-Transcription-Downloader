# Youtube.Transcribe.py - Complete Redesign Plan

## Overview

**Project:** YouTube Channel Transcript Downloader with yt-dlp integration
**Approach:** yt-dlp for video discovery + youtube_transcript_api for transcripts + orchestration logic
**Goal:** Full config.toml configurability with yt-dlp flag passthrough

---

## Architecture

### Core Components

#### 1. **yt-dlp Integration (Video Discovery)**

- Video/channel discovery using yt-dlp
- Video metadata extraction (id, title, upload_date, etc.)
- Output template handling
- Command logging for debugging
- Flag translation: config option → yt-dlp flag

#### 2. **youtube_transcript_api Integration (Transcript Download)**

- Fetch transcripts from YouTube API
- Multi-language support
- Language fallback logic
- Quality scoring (manual vs auto captions)
- Rate limiting & retry logic

#### 3. **Transcript Orchestration (Unique Value)**

- Batch processing of videos for transcripts
- Concurrent transcript downloading
- Transcript availability detection
- Queue management
- Differential downloads (new videos only)
- Archive/history management

#### 4. **File Organization**

- Auto language folder creation
- Transcript naming conventions
- File format options (txt/json/metadata)
- Reorganizing existing transcripts
- Path templating

---

## Configuration Structure

### config.toml Structure

```toml
# ============================================================================
# YT_DLP OPTIONS
# ============================================================================
# These options are passed directly to yt-dlp
# Format: option_name → --option-name flag
# Boolean options: set to true → add flag, false → omit flag

[yt_dlp.options]
# Output template for video files (yt-dlp --output)
output = "%(title)s [%(id)s].%(ext)s"

# Video filtering
skip_download = true              # --skip-download (transcripts only)
max_downloads = 0                 # --max-downloads (0 = no limit)
playlist_items = ""               # --playlist-items "1:10"

# Download options
concurrent_fragments = 1          # --concurrent-fragments N
sleep_interval = 1.5              # --sleep-interval SECONDS
max_sleep_interval = 20           # --max-sleep-interval SECONDS
retry_sleep = "http:1,linear"     # --retry-sleep TYPE:EXPR

# Format selection
format = "bestvideo+bestaudio/best"  # --format FORMAT
format_sort = "res,codec"         # --format-sort SORTORDER

# Output options
restrict_filenames = true         # --restrict-filenames
no_warnings = false               # --no-warnings

# Logging
verbose = false                   # --verbose (detailed output)
quiet = false                     # --quiet (minimal output)

# ============================================================================
# TRANSCRIPT OPTIONS
# ============================================================================
# Options specific to transcript handling and orchestration

[transcripts]
# Download settings
download_formats = ["txt", "json"]  # Available: txt, json, srt, vtt
use_language_folders = true         # Create language-specific subdirectories
sanitize_filenames = true           # Remove invalid characters from filenames

# Language handling
default_language = "en"             # Default language if none specified
auto_detect_language = true         # Auto-detect system language
language_priority = ["en", "es", "fr", "de"]  # Priority order for languages

# Batch processing
concurrent_workers = 3              # Concurrent transcript downloads
batch_size = 100                    # Videos to process per batch
max_videos_per_channel = 0          # 0 = no limit, N = max N videos

# File organization
organize_existing = true            # Reorganize existing transcript files
timestamp_prefix_format = "%Y%m%d_%H%M%S"  # For file versioning
overwrite_existing = false          # Skip if file exists

# ============================================================================
# RATE LIMITING & PERFORMANCE
# ============================================================================
# Rate limiting for transcript API (independent of yt-dlp)

[rate_limiting]
# Base delay between transcript requests (seconds)
base_delay = 1.5

# Number of concurrent workers for transcript downloads
max_workers = 3

# Retry settings
max_retries = 3
retry_backoff_factor = 2.0          # Exponential backoff multiplier
jitter_percentage = 0.2             # Random delay variation (0.0-1.0)

# Ban recovery (automatic rate limit detection)
ban_recovery_time = [300, 420]      # Min/max seconds to wait after ban detection

# Strategy settings
rate_strategy = "balanced"          # conservative, balanced, aggressive
strategy_multipliers = {            # Apply multipliers to base_delay
    conservative = 3.0,
    balanced = 1.0,
    aggressive = 0.5
}

# ============================================================================
# API SETTINGS
# ============================================================================

[api_settings]
# YouTube Transcript API timeout
api_timeout = 600                   # Seconds

# Cache settings for transcript metadata
enable_cache = true
cache_dir = "./cache"
cache_expiry_hours = 24

# ============================================================================
# LOGGING & UI
# ============================================================================

[ui]
show_progress = true                # Show progress bars
clear_screen = true                 # Clear screen on startup
show_errors = true                  # Display error messages
color_scheme = "default"            # Colorama color scheme

[logging]
level = "INFO"                      # DEBUG, INFO, WARNING, ERROR
file = ""                          # Log file path (empty = console only)
log_ytdlp_commands = true           # Log yt-dlp commands to file
command_log_file = "ytdlp_commands.log"

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

[performance]
memory_usage = "medium"             # low, medium, high
network_speed = "medium"            # slow, medium, fast
cpu_cores = 0                       # 0 = auto-detect, N = use N cores
```

---

## Command-Line Interface

### Priority Order (Highest to Lowest)

1. **CLI Flags** (user overrides)
2. **config.toml**
3. **yt-dlp defaults**
4. **Application defaults**

### Supported CLI Flags

#### yt-dlp Flags (passthrough)

```bash
--output-template TEMPLATE         # Override config [yt_dlp.options].output
--skip-download                    # Override config [yt_dlp.options].skip_download
--format FORMAT                    # Override config [yt_dlp.options].format
--format-sort SORTORDER            # Override config [yt_dlp.options].format_sort
--sleep-interval SECONDS           # Override config [yt_dlp.options].sleep_interval
--verbose                          # Override config [yt_dlp.options].verbose
--quiet                            # Override config [yt_dlp.options].quiet
```

#### Transcript-Specific Flags

```bash
--transcript-format FORMAT         # txt, json, srt, vtt
--concurrent-workers N             # Override config [transcripts].concurrent_workers
--batch-size N                     # Override config [transcripts].batch_size
--default-language CODE            # Override config [transcripts].default_language
--overwrite-existing               # Override config [transcripts].overwrite_existing
--no-organize                      # Override config [transcripts].organize_existing
--timestamp-prefix                 # Enable timestamp prefix in filenames
```

#### Application Flags

```bash
--create-config                    # Create default config.toml
--show-config                      # Display current configuration
--help, -h                         # Show help message
```

#### Standard Flags

```bash
-t LANG, --transcript LANG         # Download transcript for language
-en -es -fr -de                    # Multiple languages (positional)
--all                              # Download all available languages
--txt                              # Download only TXT format
--json                             # Download only JSON format
<URL(s)>                           # YouTube URLs (channel, video, playlist)
```

---

## Implementation Details

### 1. Config Loading & Validation

```python
def load_config(config_path="config.toml") -> Config:
    """Load and validate configuration with priority handling"""
    # 1. Load config.toml defaults
    # 2. Override with environment variables
    # 3. Override with CLI arguments
    # 4. Validate all settings
    # 5. Return complete config
```

### 2. Flag Translation (config → yt-dlp)

```python
def translate_yt_dlp_options(options: Dict[str, Any]) -> List[str]:
    """Translate config options to yt-dlp flags"""
    flags = []

    for key, value in options.items():
        flag = f"--{key.replace('_', '-')}"

        if isinstance(value, bool):
            if value:
                flags.append(flag)
        elif isinstance(value, (int, float)):
            flags.extend([flag, str(value)])
        elif isinstance(value, str):
            flags.extend([flag, value])
        elif isinstance(value, list):
            for item in value:
                flags.extend([flag, str(item)])

    return flags
```

### 3. Command Logging

```python
def log_ytdlp_command(command: List[str], output_dir: str):
    """Log yt-dlp command for debugging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd_str = " ".join(command)

    log_entry = f"""
[{timestamp}] Executing yt-dlp:
  Command: {cmd_str}
  Output Directory: {output_dir}
  Template: {get_output_template()}
========================================
"""

    with open(command_log_file, "a") as f:
        f.write(log_entry)
```

### 4. Transcript Processing Pipeline

```python
def process_videos(urls: List[str], config: Config):
    """Main processing pipeline"""
    for url in urls:
        # 1. Discover videos using yt-dlp
        videos = discover_videos(url, config)

        # 2. Detect available transcripts
        for video in videos:
            available_langs = get_available_transcripts(video["id"])

            # 3. Download transcripts based on config
            for lang in config.requested_languages:
                if lang in available_langs:
                    download_transcript(video, lang, config)

                # 4. Apply rate limiting
                rate_limiter.wait()

                # 5. Save with file organization
                file_manager.save(video, lang, transcript_data)
```

---

## File Organization Logic

### Directory Structure

```text
downloads/
├── ChannelName/
│   ├── en/                          # Language folder
│   │   ├── VideoTitle_en.txt
│   │   ├── VideoTitle_en.json
│   │   └── json/                    # JSON files
│   │       ├── VideoTitle_en.json
│   ├── es/                          # Spanish transcripts
│   ├── fr/                          # French transcripts
│   └── unorganized/                 # Files before reorganization
```

### Filename Templates

**Without timestamp:**

```text
{VideoTitle}_{LanguageCode}.{Extension}
Example: "My Video Title_en.txt"
```

**With timestamp:**

```text
{YYYYMMDD_HHMMSS}_{VideoTitle}_{LanguageCode}.{Extension}
Example: "20251119_143052_My Video Title_en.txt"
```

**Timestamp format configurable:**

```text
config: timestamp_prefix_format = "%Y%m%d_%H%M%S"
```

---

## Testing Strategy

### Unit Tests

1. **Config Loading**
   - Load default config
   - Override with CLI args
   - Environment variable override
   - Validation of all settings

2. **Flag Translation**
   - Boolean flags
   - String flags
   - List flags
   - Special characters in values

3. **yt-dlp Integration**
   - Command generation
   - Output template handling
   - Error handling

4. **Transcript API**
   - Language detection
   - Rate limiting
   - Retry logic
   - File saving

### Integration Tests

1. **Full Pipeline**
   - Download transcripts for single video
   - Download transcripts for channel
   - Multi-language downloads
   - Concurrent downloads

2. **Config Override**
   - CLI overrides config.toml
   - Environment overrides both
   - Priority order

3. **File Organization**
   - Language folder creation
   - Existing file reorganization
   - Timestamp prefix handling

### Manual Tests

```bash
# Test 1: Basic usage
python Youtube.Transcribe.py <url> -en

# Test 2: Multi-language
python Youtube.Transcribe.py <url> -en -es -fr

# Test 3: Custom config
python Youtube.Transcribe.py --create-config
# Edit config.toml
python Youtube.Transcribe.py <url>

# Test 4: CLI override
python Youtube.Transcribe.py <url> --output-template "%(upload_date>%Y%m%d)s_%(title)s.%(ext)s"

# Test 5: Transcript-only mode
python Youtube.Transcribe.py <url> --skip-download -en

# Test 6: All languages
python Youtube.Transcribe.py <url> --all

# Test 7: Command logging
python Youtube.Transcribe.py <url> -en
cat ytdlp_commands.log  # Check logged commands
```

---

## Backward Compatibility

### Config Migration

**Old Config Format:**

```toml
[rate_limiting]
base_delay = 1.5
max_workers = 3

[file_handling]
output_dir = "./downloads"
use_language_folders = true
download_formats = ["txt", "json"]
sanitize_filenames = true
```

**New Config Format:**

```toml
[yt_dlp.options]
output = "%(title)s [%(id)s].%(ext)s"
skip_download = true

[transcripts]
download_formats = ["txt", "json"]
use_language_folders = true
sanitize_filenames = true

[rate_limiting]
base_delay = 1.5
max_workers = 3
```

**Migration Strategy:**

- Detect old config format
- Auto-convert to new format with warnings
- Create backup of old config
- Generate new config with all options

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅

- [x] Refactor config system (new structure)
- [x] Implement config loading with priority order
- [x] Create yt-dlp flag translation system
- [x] Add command logging

### Phase 2: yt-dlp Integration ✅

- [x] Update video discovery logic
- [x] Pass output template to yt-dlp
- [x] Handle yt-dlp errors gracefully
- [x] Log all yt-dlp commands

### Phase 3: Transcript Orchestration ✅

- [x] Update transcript download logic
- [x] Add language priority & fallback
- [x] Implement quality scoring
- [x] Add file organization

### Phase 4: CLI Updates ✅

- [x] Update argument parser
- [x] Add yt-dlp flag passthrough
- [x] Update help documentation
- [x] Add --create-config with new format

### Phase 5: Testing & Validation ✅

- [x] Write unit tests
- [x] Integration testing
- [x] Performance testing
- [x] Manual testing

### Phase 6: Documentation ✅

- [x] Update README.md
- [x] Create config.toml examples
- [x] Document all CLI options
- [x] Add troubleshooting guide

---

## Future Enhancements

### Potential Features

1. **Transcript Filtering**
   - Skip auto-generated captions
   - Prefer manual captions
   - Minimum duration threshold

2. **Advanced Organization**
   - Date-based folder structure
   - Channel folder hierarchy
   - Custom naming templates

3. **Smart Downloads**
   - Detect transcript updates
   - Incremental sync
   - Change notifications

4. **Export Options**
   - Merge transcripts across videos
   - Export to different formats
   - Create transcript collections

5. **Integration Features**
   - Webhook notifications
   - API endpoints
   - GUI frontend

---

## Open Questions & Decisions

1. **File Extension Naming**
   - `VideoTitle_en.txt` vs `VideoTitle (en).txt`
   - Timestamp placement: prefix or suffix?
   - Include video ID in filename?

2. **Language Priority**
   - Configurable priority list?
   - Auto-detect based on channel language?
   - Fallback logic (en → auto → skip)?

3. **Rate Limiting**
   - Separate from yt-dlp rate limiting?
   - Per-channel or global?
   - Dynamic adjustment based on errors?

4. **Config Migration**
   - Auto-migrate old configs?
   - Support both formats temporarily?
   - Breaking changes policy?

---

## Approval Required

**This plan is ready for review and approval.**

- [ ] Architecture approved
- [ ] Config structure approved
- [ ] CLI interface approved
- [ ] Implementation approach approved
- [ ] Backward compatibility plan approved

**Ready to proceed with implementation?**
