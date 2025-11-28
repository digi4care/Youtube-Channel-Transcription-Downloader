# Troubleshooting Guide

Common issues and solutions for the YouTube Channel Transcript Downloader.

## Common Issues and Solutions

### Transcript Issues

- **"No transcript available"**: The video doesn't have subtitles or they're disabled
- **"Video unavailable"**: The video is private, deleted, or region-locked
- **"Age restricted"**: These videos require authentication and can't be processed
- **"Subtitles disabled"**: The creator has disabled subtitles for this video

### Rate Limiting Issues

- **"Rate limited"**: YouTube is temporarily blocking your IP - wait 5-7 minutes
- **Getting banned frequently**: Reduce workers and increase delays in config

### Configuration Issues

- **Config not loading**: Ensure `config.toml` is in the project root directory
- **Environment variables not working**: Check variable names match exactly (case-sensitive)

### Installation Issues

- **Import errors**: Make sure virtual environment is activated
- **Permission errors**: Check write permissions for output directories
- **ffmpeg not found**: Install ffmpeg for audio/video format conversion

## Performance Tips

### For Large Channels

- **Conservative settings**: 3s delay, 1-2 workers
- **Monitor rate limits**: Start slow, increase gradually
- **Use archive feature**: Automatic resume after interruptions

### For Quick Tests

- **Faster settings**: 1s delay, 3-5 workers
- **Monitor bans**: Be ready to stop if getting blocked
- **Small batches**: Test with fewer videos first

### For Batch Processing

- **Sequential processing**: Process one channel at a time
- **Stagger runs**: Space out large downloads
- **Monitor API usage**: Track your YouTube quota

## Archive Feature Issues

### Reset Archive

```bash
# Delete archive file to start fresh
rm downloads/ChannelName/.transcript_archive.txt
```

### Archive Not Working

- Check `enable_archive = true` in config.toml
- Ensure write permissions for channel directories
- Verify archive file is not corrupted (should contain video IDs only)

## Language Issues

### Wrong Language Detected

- Specify explicit language: `-t en`
- Check config.toml default language settings
- Use `-all` to see available languages

### Language Not Available

- Video may not have subtitles in requested language
- Check available languages with different video from same channel
- Use auto-detection or fallback languages

## File System Issues

### Permission Errors

```bash
# Fix permissions
chmod 755 downloads/
chmod 644 downloads/*/*
```

### Filename Issues

- Use `--advanced-filename-sanitize` for problematic filenames
- Check filesystem encoding (UTF-8 recommended)
- Avoid special characters in output directory names

## YouTube API Issues

### yt-dlp Errors

- Update yt-dlp: `uv pip install --upgrade yt-dlp`
- Check YouTube URL format
- Try different video from same channel

### Transcript API Errors

- Update youtube-transcript-api
- Check internet connection
- Wait for YouTube API to recover (temporary issues)

## Getting Help

### Debug Mode

```bash
# Enable verbose logging
python Youtube_Transcribe.py --log-level DEBUG [url]
```

### Check Dependencies

```bash
# Verify all packages are installed
uv pip list | grep -E "(yt-dlp|youtube-transcript-api|tqdm|colorama)"
```

### Report Issues

- Include full error message
- Specify YouTube URL (without personal data)
- Include your config.toml (remove sensitive data)
- Mention your operating system and Python version

---

**← Back to [README.md](../README.md)**
