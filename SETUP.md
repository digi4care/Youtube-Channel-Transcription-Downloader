# Setup Guide

This guide covers installation and setup of the YouTube Channel Transcript Downloader.

## Requirements

- Python 3.11+
- uv package manager (recommended) OR pip

All requirements are listed in `pyproject.toml` and `requirements.txt`.

## Option 1: Using UV (Recommended)

### 1. Clone the repository

```bash
git clone https://github.com/digi4care/Youtube-Channel-Transcription-Downloader.git
cd Youtube-Channel-Transcription-Downloader
```

### 2. Install uv if you haven't already

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create a virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 4. Update the virtual environment (important for YouTube compatibility)

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

### 5. Run the application

```bash
# Create configuration
python Youtube_Transcribe.py --create-config

# Download transcripts
python Youtube_Transcribe.py https://youtube.com/c/channel1 --transcript en
```

## Option 2: Using pip (Traditional)

### 1. Clone the repository

```bash
git clone https://github.com/digi4care/Youtube-Channel-Transcription-Downloader.git
cd Youtube-Channel-Transcription-Downloader
```

### 2. Create and activate a virtual environment

```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the required packages

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python Youtube_Transcribe.py --create-config
python Youtube_Transcribe.py https://youtube.com/c/channel1 --transcript en
```

## Quick Start

Get up and running in 3 simple steps:

1. **Create default configuration**:

   ```bash
   python Youtube_Transcribe.py --create-config
   ```

2. **Edit `config.toml`** to customize settings like rate limiting, output formats, etc.

3. **Run with your preferred configuration**:

   ```bash
   python Youtube_Transcribe.py https://youtube.com/c/channel1 --transcript en
   ```

---

**← Back to [README.md](../README.md)**
