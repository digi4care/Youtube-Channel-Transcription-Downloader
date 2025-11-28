# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2025-11-28 - Advanced Filename Sanitization

### Added to Advanced Filename Sanitization

- **Advanced Filename Sanitization**: Optional WordPress-style filename cleaning with Unicode support
- **Configurable Sanitization**: Choose between basic and advanced filename sanitization modes
- `--advanced-filename-sanitize` CLI flag for enabling advanced sanitization
- `advanced_filename_sanitize` config option in `config.toml`

### Features of Advanced Mode

- Unicode accent removal (café → cafe)
- Special character cleaning and space-to-dash conversion
- Cross-platform filename safety
- Length limits and extension validation

### Changes in Advanced Filename Sanitization

- Filename sanitization now configurable between basic and advanced modes
- Default behavior unchanged (basic sanitization) for backward compatibility

## [2.1.0] - 2025-11-28 - Archive & Resume

### Added to Archive & Resume

- **Archive & Resume System**: Automatic recovery from rate limiting interruptions
- **Per-Channel Archive Files**: `.transcript_archive.txt` files track processed videos
- **Rate Limit Optimization**: No wasted API calls on already processed videos
- `--enable-archive` config option (enabled by default)

### Features of Archive & Resume

- Smart detection of processed videos
- Safe parallel processing of multiple channels
- Automatic resume after YouTube rate limit errors
- Backward compatible with existing installations

### Changes in Archive & Resume

- Language detection now only triggers when no explicit languages are provided
- Fixed CLI language argument parsing (`-t en` instead of `-en`)

## [2.0.0] - 2025-11-28 - Refactored Architecture

### Added to Refactored Architecture

- **SOLID Principles**: Complete code architecture refactor
- **TOML Configuration**: User-friendly `config.toml` file support
- **Class-Based Design**: Modular components for better maintainability
- **Enhanced Rate Limiting**: Multiple strategies with ban recovery
- **Environment Variables**: Override any config via `YTD_*` env vars
- **Improved Error Handling**: More robust error management and logging

### Changes in Refactored Architecture

- Complete internal architecture rewrite
- Configuration moved from CLI args to TOML file
- Better separation of concerns with dedicated classes

### Removed in Refactored Architecture

- Old CLI argument structure (replaced with TOML config)

## [1.0.0] - Original Fork

### Added to Original Fork

- Fork of [youtube-transcript-downloader](https://github.com/rugabunda/youtube-transcript-downloader)
- Initial enhancements and bug fixes
- Basic YouTube transcript downloading functionality

---

**Credits:**

- Original project: [titusrugabunda](https://github.com/rugabunda)
- Enhanced fork: [digi4care](https://github.com/digi4care)
