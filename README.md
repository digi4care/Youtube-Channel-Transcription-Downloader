

---

# YouTube Channel Transcript Downloader

This script downloads transcripts for videos on YouTube channels or individual videos. It creates a separate folder for each channel and organizes files into subdirectories. Downloads are processed with rate limiting to avoid YouTube IP bans. Files that already exist will be skipped, allowing you to resume or update channels.

## Usage

```bash
python Youtube.Transcribe.py [options] <channel_or_video_url(s)>
```

## Examples

- **Download transcript for a single YouTube video**
  ```bash
  python Youtube.Transcribe.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -en
  ```
- **Short URL also works**
  ```bash
  python Youtube.Transcribe.py https://youtu.be/dQw4w9WgXcQ -en
  ```
- **Multiple URLs**
  ```bash
  python Youtube.Transcribe.py https://youtu.be/aDkzgTWhVY4 https://youtu.be/3ZC1iqYfFGU -en
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
- **Download only JSON files (no TXT)**
  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -json
  ```
- **Faster downloads (may increase risk of IP ban)**
  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -delay 1 -workers 5
  ```
- **Slower, safer downloads (to prevent IP bans)**
  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -delay 3 -workers 2
  ```
- **Download from multiple channels**
  ```bash
  python Youtube.Transcribe.py https://youtube.com/c/channel1 https://youtube.com/c/channel2 -en
  ```
- **Download from channels listed in a file (one URL per line or comma-separated)**
  ```bash
  python Youtube.Transcribe.py -f channels.txt -en
  ```

## Options

- `-f, --file FILE`    Read channel URLs from a text file (one per line or comma-separated)
- `-LANG`              Language code for transcripts (e.g., `-en` for English). Multiple language codes can be specified (e.g., `-en -es -fr`)
- `-all`               Download all available languages for each video
- `-txt`               Download only TXT files (no JSON)
- `-json`              Download only JSON files (no TXT)
- `-delay N`           Delay between API requests in seconds (default: 1.5). Higher values reduce risk of IP bans but slow downloads
- `-workers N`         Number of concurrent downloads (default: 3, range: 1-10). Lower values reduce risk of IP bans but slow downloads
- `-h, --help`         Show this help message

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
  ```
  ./transcripts/[Channel Name]/json/[Video Title]_[VideoID]_[lang].json
  ./transcripts/[Channel Name]/[Video Title]_[VideoID]_[lang].txt
  ```
- **Multiple language mode** (triggered when):
  - Multiple languages are requested in the command
  - Multiple languages already exist in the folder
  - A new language is requested that doesn't match existing files

  In this mode, files are organized as:
  ```
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
```
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

## Requirements

- Python 3.6+
- youtube_transcript_api (`pip install youtube-transcript-api`)
- yt-dlp (`pip install yt-dlp`)

---
