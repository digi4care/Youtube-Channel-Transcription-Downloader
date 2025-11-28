# YouTube Channel Transcript Downloader

> **Enhanced fork** of the original [youtube-transcript-downloader](https://github.com/rugabunda/youtube-transcript-downloader) by titusrugabunda.

A robust Python tool for downloading YouTube video transcripts in bulk, with advanced features for large-scale processing.

## ✨ Key Features

- 🔄 **Archive & Resume**: Automatic recovery from rate limiting interruptions
- 🧹 **Smart Sanitization**: Optional WordPress-style filename cleaning
- 🌐 **Multi-language**: Support for all available transcript languages
- ⚙️ **TOML Config**: User-friendly configuration management
- 🛡️ **Rate Limiting**: Built-in protection against YouTube bans
- 📊 **Progress Tracking**: Real-time download progress and statistics

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/digi4care/Youtube-Channel-Transcription-Downloader.git
cd Youtube-Channel-Transcription-Downloader
uv venv && source .venv/bin/activate && uv sync

# Configure
python Youtube_Transcribe.py --create-config

# Download transcripts
uv run python Youtube_Transcribe.py https://youtube.com/@ChannelName -t en
```

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Complete installation guide
- **[USAGE.md](USAGE.md)** - Command reference and basic usage
- **[EXAMPLES.md](EXAMPLES.md)** - Detailed examples and advanced usage
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration options and features
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup and contribution guidelines

## 📋 Requirements

- Python 3.11+
- uv package manager (recommended) or pip
- ffmpeg (for audio/video downloads)

## 🤝 Contributing

Contributions welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for development setup and guidelines.

## 📄 License

This project is open source. See individual files for license details.

---

**Created with ❤️ by [digi4care](https://github.com/digi4care)**
