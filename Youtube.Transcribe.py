#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import time
import re
import concurrent.futures
import argparse
import locale
import signal
import shutil
import random
from youtube_transcript_api import YouTubeTranscriptApi, _errors

# Global variables to track active processes
active_processes = []

# Ban detection and recovery tracking
original_delay = None
original_workers = None
ban_detected = False
ban_recovery_time = None

def signal_handler(sig, frame):
    """Handle termination signals properly."""
    print("\nScript termination requested. Cleaning up...")
    # Kill any active subprocesses
    for process in active_processes:
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
        except:
            pass
    
    print("Cleanup complete. Exiting.")
    os._exit(0)  # Use os._exit to force immediate termination

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Kill command
if hasattr(signal, 'SIGTSTP'):  # Ctrl+Z (not available on Windows)
    signal.signal(signal.SIGTSTP, signal_handler)

def sanitize_filename(name):
    """Remove invalid characters from filenames."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def display_help():
    """Display usage instructions and available languages."""
    print("=" * 80)
    print("YouTube Channel Transcript Downloader")
    print("=" * 80)
    print("\nThis script downloads transcripts for videos on YouTube channels or individual videos.")
    print("It creates a separate folder for each channel and organizes files into subdirectories.")
    print("Downloads are processed with rate limiting to avoid YouTube IP bans.")
    print("Files that already exist will be skipped, allowing you to resume or update channels.")
    
    print("\nUSAGE:")
    print("  python Youtube.Transcribe.py [options] <channel_or_video_url(s)>")
    
    print("\nEXAMPLES:")
    print("  # Download transcript for a single YouTube video")
    print("  python Youtube.Transcribe.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -en")
    print("  # Short URL also works")
    print("  python Youtube.Transcribe.py https://youtu.be/dQw4w9WgXcQ -en")
    print("  # Multiple URLs also works")
    print("  Youtube.Transcribe.py https://youtu.be/aDkzgTWhVY4 https://youtu.be/3ZC1iqYfFGU -en")
    
    
    print("  # Download English transcripts from a channel")
    print("  python Youtube.Transcribe.py https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw -en")
    
    print("  # Download multiple languages")
    print("  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -es -fr")
    
    print("  # Download all available languages")
    print("  python Youtube.Transcribe.py https://youtube.com/c/channel1 -all")
    
    print("  # Download only TXT files (no JSON)")
    print("  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -txt")
    
    print("  # Download only JSON files (no TXT)")
    print("  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -json")
    
    print("  # Faster downloads (may increase risk of IP ban)")
    print("  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -delay 1 -workers 5")
    
    print("  # Slower, safer downloads (to prevent IP bans)")
    print("  python Youtube.Transcribe.py https://youtube.com/c/channel1 -en -delay 3 -workers 2")
    
    print("  # Download from multiple channels")
    print("  python Youtube.Transcribe.py https://youtube.com/c/channel1 https://youtube.com/c/channel2 -en")
    
    print("  # Download from channels listed in a file (one URL per line or comma-separated)")
    print("  python Youtube.Transcribe.py -f channels.txt -en")
    
    print("\nOPTIONS:")
    print("  -f, --file FILE    Read channel URLs from a text file (one per line or comma-separated)")
    print("  -LANG              Language code for transcripts (e.g., -en for English)")
    print("                     Multiple language codes can be specified (e.g., -en -es -fr)")
    print("  -all               Download all available languages for each video")
    print("  -txt               Download only TXT files (no JSON)")
    print("  -json              Download only JSON files (no TXT)")
    print("  -delay N           Delay between API requests in seconds (default: 1.5)")
    print("                     Higher values reduce risk of IP bans but slow downloads")
    print("  -workers N         Number of concurrent downloads (default: 3, range: 1-10)")
    print("                     Lower values reduce risk of IP bans but slow downloads")
    print("  -h, --help         Show this help message")
    
    print("\nRATE LIMITING:")
    print("  To avoid YouTube IP bans, this script implements several protection measures:")
    print("  1. Request delays: Controlled delay between API calls (adjust with -delay)")
    print("  2. Random jitter: ±20% randomness added to each delay to avoid pattern detection")
    print("  3. Limited concurrency: Restricted parallel downloads (adjust with -workers)")
    print("  4. Smart retries: Automatic detection of non-retryable errors (age-restricted videos, etc.)")
    print("  5. Exponential backoff: Increasingly longer delays after rate limit errors")
    print("  6. Error skipping: No retry for videos that cannot have transcripts (subtitles disabled, etc.)")
    print("")
    print("  RECOMMENDED SETTINGS:")
    print("  - Normal usage: Default values (-delay 1.5 -workers 3)")
    print("  - If IP banned:")
    print("    1. Switch to very slow settings (-delay 5 -workers 1) until ban is lifted")
    print("    2. After ban is lifted, continue with these slow settings for 5-7 minutes")
    print("    3. Then reduce to half your original speed (double delay, halve workers)")
    print("    4. If banned again, repeat the halving process until bans stop permanently")
    print("    Example: If original settings were -delay 1 -workers 6, after recovery use")
    print("             -delay 2 -workers 3, then -delay 4 -workers 2 if banned again")
    
    print("\nFILE ORGANIZATION:")
    print("  Files are organized based on languages detected and requested:")
    print("  - Single language mode (when only one language exists or is requested):")
    print("    ./transcripts/[Channel Name]/json/[Video Title]_[VideoID]_[lang].json")
    print("    ./transcripts/[Channel Name]/[Video Title]_[VideoID]_[lang].txt")
    
    print("  - Multiple language mode (triggered when):")
    print("    * Multiple languages are requested in the command")
    print("    * Multiple languages already exist in the folder")
    print("    * A new language is requested that doesn't match existing files")
    print("    In this mode, files are organized as:")
    print("    ./transcripts/[Channel Name]/[lang]/json/[Video Title]_[VideoID]_[lang].json")
    print("    ./transcripts/[Channel Name]/[lang]/[Video Title]_[VideoID]_[lang].txt")
    
    print("\nNOTES:")
    print("  - If no language is specified, your system language will be used")
    print("  - If system language cannot be determined, English will be used")
    print("  - Use Ctrl+C to properly terminate the script")
    print("  - The script will automatically reorganize files when switching to multiple language mode")
    
    print("\nFILE FORMAT:")
    print("  The channel url file can contain URLs in any of these formats:")
    print("  - One URL per line")
    print("  - Comma-separated URLs")
    print("  - Comma with spaces between URLs")
    print("  Example file content:")
    print("    https://youtube.com/channel/UC123, https://youtube.com/c/channel2")
    print("    https://youtube.com/user/someuser")
    
    print("\nAVAILABLE LANGUAGE CODES:")
    # List of common language codes and names
    languages = [
        ("en", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("it", "Italian"),
        ("pt", "Portuguese"),
        ("ru", "Russian"),
        ("ja", "Japanese"),
        ("ko", "Korean"),
        ("zh-Hans", "Chinese (Simplified)"),
        ("zh-Hant", "Chinese (Traditional)"),
        ("ar", "Arabic"),
        ("hi", "Hindi"),
        ("bn", "Bengali"),
        ("nl", "Dutch"),
        ("sv", "Swedish"),
        ("tr", "Turkish"),
        ("pl", "Polish"),
        ("vi", "Vietnamese"),
        ("th", "Thai"),
        ("fa", "Persian"),
        ("id", "Indonesian"),
        ("uk", "Ukrainian"),
        ("cs", "Czech"),
        ("fi", "Finnish"),
        ("ro", "Romanian"),
        ("el", "Greek"),
        ("he", "Hebrew"),
        ("da", "Danish"),
        ("no", "Norwegian"),
        ("hu", "Hungarian"),
        ("bg", "Bulgarian"),
        ("hr", "Croatian"),
        ("sk", "Slovak"),
        ("lt", "Lithuanian"),
        ("sl", "Slovenian"),
        ("et", "Estonian"),
        ("lv", "Latvian"),
    ]
    
    # Display in 3 columns to save space
    col_width = 25
    for i in range(0, len(languages), 3):
        row = ""
        for j in range(3):
            if i+j < len(languages):
                code, name = languages[i+j]
                row += f"  -{code:<7} - {name:<{col_width}}"
        print(row)
    
    print("\nREQUIREMENTS:")
    print("  - python 3.6+")
    print("  - youtube_transcript_api (pip install youtube-transcript-api)")
    print("  - yt-dlp (pip install yt-dlp)")
    print("=" * 80)

def get_system_language():
    """Get the user's system language."""
    try:
        # Set locale to the user's default
        locale.setlocale(locale.LC_ALL, '')
        
        # Try to get the language from the locale
        lang_code = None
        
        # First try getlocale
        try:
            loc = locale.getlocale(locale.LC_MESSAGES)
            if loc and loc[0]:
                lang_code = loc[0].split('_')[0].lower()
        except (AttributeError, ValueError):
            pass
            
        # If that didn't work, try getencoding
        if not lang_code:
            try:
                encoding = locale.getencoding()
                if encoding and encoding.startswith(('en', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'ru', 'zh')):
                    lang_code = encoding[:2]
            except (AttributeError, ValueError):
                pass
                
        # If we found a language code, use it
        if lang_code:
            print(f"Detected system language: {lang_code}")
            return lang_code
            
    except Exception as e:
        print(f"Could not detect system language: {e}")
    
    print("Defaulting to English (en)")
    return 'en'

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="YouTube Channel Transcript Downloader", add_help=False)
    parser.add_argument('-f', '--file', help="File containing channel URLs")
    parser.add_argument('-h', '--help', action='store_true', help="Show help message")
    parser.add_argument('-all', action='store_true', help="Download all available languages")
    parser.add_argument('-txt', action='store_true', help="Download only TXT files")
    parser.add_argument('-json', action='store_true', help="Download only JSON files")
    parser.add_argument('-delay', type=float, default=1.5, help="Delay between API requests in seconds")
    parser.add_argument('-workers', type=int, default=3, help="Number of concurrent downloads")
    
    # First parse just the file and help arguments
    args, remaining = parser.parse_known_args()
    
    if args.help or len(sys.argv) <= 1:  # Show help if -h or no arguments
        display_help()
        sys.exit(0)
    
    # Extract channel URLs and languages
    urls = []
    languages = []
    download_all = args.all  # Flag to download all languages
    download_txt = True if not args.json else False  # Default to both unless only JSON is specified
    download_json = True if not args.txt else False  # Default to both unless only TXT is specified
    delay = max(0.5, args.delay)  # Ensure minimum delay of 0.5 seconds
    workers = max(1, min(10, args.workers))  # Limit workers between 1 and 10
    
    # Check for conflict
    if args.txt and args.json:
        print("Warning: Both -txt and -json specified. Will download both formats.")
        download_txt = True
        download_json = True
    
    # Parse URLs from file if specified
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split by commas or newlines
            content = content.replace(',', '\n')
            file_urls = [url.strip() for url in content.split('\n') if url.strip()]
            urls.extend(file_urls)
            
            print(f"Loaded {len(file_urls)} URLs from file: {args.file}")
        except Exception as e:
            print(f"Error reading file {args.file}: {str(e)}")
            sys.exit(1)
    
    # Parse URLs and languages from command line
    for arg in remaining:
        if arg.startswith('-'):
            if arg == '-all':
                download_all = True
            elif arg == '-txt':
                download_txt = True
                download_json = False
            elif arg == '-json':
                download_json = True
                download_txt = False
            elif arg.startswith('-delay') or arg.startswith('-workers'):
                # These are already handled by argparse
                continue
            else:
                # This is a language code
                lang_code = arg[1:]  # Remove the dash
                languages.append(lang_code)
        elif arg.startswith(('http://', 'https://', 'www.')):
            urls.append(arg)  # This is a URL
    
    # Ensure we have at least one URL
    if not urls:
        print("Error: No channel URLs provided. Use -h for help.")
        sys.exit(1)
    
    # Default to system language if no language is specified and not downloading all
    if not languages and not download_all:
        languages = [get_system_language()]
    
    return urls, languages, download_all, download_txt, download_json, delay, workers

def detect_languages_in_folder(channel_dir):
    """Detect existing transcript languages in a channel directory."""
    languages = set()
    
    if not os.path.exists(channel_dir):
        return languages
    
    # First check for dedicated language folders
    for item in os.listdir(channel_dir):
        item_path = os.path.join(channel_dir, item)
        # Check if it's a directory and follows language code naming pattern (2-10 characters)
        # Exclude the "json" directory from being treated as a language
        if os.path.isdir(item_path) and re.match(r'^[a-zA-Z\-]{2,10}$', item) and item != "json":
            languages.add(item)
    
    # If no language folders, check file suffixes
    if not languages:
        # Check TXT files in main folder
        for file in os.listdir(channel_dir):
            if file.endswith(".txt"):
                # Extract language from filename (assuming format: *_LANG.txt)
                match = re.search(r'_([a-zA-Z\-]{2,10})\.txt$', file)
                if match:
                    languages.add(match.group(1))
        
        # Check JSON files in json folder
        json_dir = os.path.join(channel_dir, "json")
        if os.path.exists(json_dir) and os.path.isdir(json_dir):
            for file in os.listdir(json_dir):
                if file.endswith(".json"):
                    # Extract language from filename (assuming format: *_LANG.json)
                    match = re.search(r'_([a-zA-Z\-]{2,10})\.json$', file)
                    if match:
                        languages.add(match.group(1))
    
    return languages

def get_channel_name(channel_url):
    """Get the channel name for directory creation."""
    print("Retrieving channel name...")
    try:
        command = [
            "yt-dlp",
            "--skip-download",
            "--print", "%(channel)s",
            "--playlist-items", "1",  # Only get info for one video to speed things up
            channel_url
        ]
        
        print(f"Running command: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        active_processes.append(process)
        
        stdout, stderr = process.communicate(timeout=30)
        active_processes.remove(process)
        
        channel_name = stdout.strip()
        
        if not channel_name:
            print("Warning: Couldn't retrieve channel name, using default.")
            return "youtube_channel"
            
        return sanitize_filename(channel_name)
    
    except subprocess.TimeoutExpired:
        print("Error: Timeout while fetching channel name")
        try:
            process.terminate()
            active_processes.remove(process)
        except:
            pass
        return "youtube_channel"
    except Exception as e:
        print(f"Error fetching channel name: {e}")
        try:
            if process in active_processes:
                process.terminate()
                active_processes.remove(process)
        except:
            pass
        return "youtube_channel"

def get_videos_from_channel(channel_url):
    """Get all video IDs and titles from a YouTube channel using yt-dlp."""
    print(f"Fetching videos from: {channel_url}")
    print("This may take a while for channels with many videos...")
    
    try:
        command = [
            "yt-dlp", 
            "--flat-playlist", 
            "--print", "%(id)s %(title)s",
            channel_url
        ]
        
        print(f"Running command: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        active_processes.append(process)
        
        stdout, stderr = process.communicate(timeout=600)
        active_processes.remove(process)
        
        if not stdout.strip():
            print("Error: No video data returned. Check the channel URL.")
            return []
            
        videos_data = []
        lines = stdout.strip().split('\n')
        
        print(f"Processing {len(lines)} video entries...")
        
        for line in lines:
            if line:
                parts = line.split(maxsplit=1)
                if len(parts) >= 2:
                    video_id = parts[0]
                    title = parts[1]
                    videos_data.append({
                        'id': video_id,
                        'title': title
                    })
                else:
                    print(f"Warning: Couldn't parse video data from: {line}")
        
        print(f"Total videos found: {len(videos_data)}")
        return videos_data
    
    except subprocess.TimeoutExpired:
        print("Error: Timeout while fetching videos list. Try again or use a different channel.")
        try:
            process.terminate()
            active_processes.remove(process)
        except:
            pass
        return []
    except Exception as e:
        print(f"Error fetching videos from channel: {e}")
        try:
            if process in active_processes:
                process.terminate()
                active_processes.remove(process)
        except:
            pass
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error output: {stderr}")
        return []

def should_use_language_folders(existing_languages, requested_languages):
    """Determine if we should use language-specific folders."""
    # Use language folders if:
    # 1. Multiple languages requested in this run, OR
    # 2. Multiple languages already exist in folder, OR
    # 3. A single language is requested that doesn't match any existing language
    
    if len(requested_languages) > 1:
        return True
    
    if len(existing_languages) > 1:
        return True
    
    # If we have one requested language and one existing language, check if they differ
    if len(requested_languages) == 1 and len(existing_languages) == 1:
        if list(requested_languages)[0] not in existing_languages:
            return True
    
    # If we have one requested language and no existing languages, no need for language folders
    if len(requested_languages) == 1 and len(existing_languages) == 0:
        return False
    
    # If we have one requested language and it's not in multiple existing languages
    if len(requested_languages) == 1 and len(existing_languages) > 0:
        if list(requested_languages)[0] not in existing_languages:
            return True
    
    return False

def move_files_to_language_folders(channel_dir, languages):
    """Move existing files to language-specific folders if needed."""
    if not os.path.exists(channel_dir):
        return
    
    print("Reorganizing existing files into language folders...")
    
    # Create language directories if they don't exist
    for lang in languages:
        lang_dir = os.path.join(channel_dir, lang)
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)
            print(f"Created language directory: {lang_dir}")
        
        # Create json subdirectory in language directory
        json_dir = os.path.join(lang_dir, "json")
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
    
    # Move TXT files from main directory to language directories
    files_to_move = []
    for file in os.listdir(channel_dir):
        if file.endswith(".txt"):
            for lang in languages:
                if f"_{lang}.txt" in file:
                    files_to_move.append((file, lang, "txt"))
    
    # Move JSON files from json directory to language/json directories
    json_dir = os.path.join(channel_dir, "json")
    if os.path.exists(json_dir) and os.path.isdir(json_dir):
        for file in os.listdir(json_dir):
            if file.endswith(".json"):
                for lang in languages:
                    if f"_{lang}.json" in file:
                        files_to_move.append((file, lang, "json"))
    
    # Actually move the files now that we've identified them
    moved_count = 0
    for file, lang, file_type in files_to_move:
        if file_type == "txt":
            src = os.path.join(channel_dir, file)
            dst = os.path.join(channel_dir, lang, file)
        else:  # json
            src = os.path.join(channel_dir, "json", file)
            dst = os.path.join(channel_dir, lang, "json", file)
        
        if not os.path.exists(dst):
            try:
                shutil.move(src, dst)
                moved_count += 1
                if moved_count % 20 == 0:  # Report every 20 files to avoid console spam
                    print(f"Moved {moved_count} files...")
            except Exception as e:
                print(f"Error moving file {file}: {e}")
    
    if moved_count > 0:
        print(f"Successfully moved {moved_count} files to language-specific folders")
    else:
        print("No files needed to be moved")
    
    # Check if the json directory is empty and remove it if it is
    json_dir = os.path.join(channel_dir, "json")
    if os.path.exists(json_dir) and os.path.isdir(json_dir):
        # Check if it's empty
        if not os.listdir(json_dir):
            try:
                os.rmdir(json_dir)
                print(f"Removed empty json directory: {json_dir}")
            except Exception as e:
                print(f"Error removing empty json directory: {e}")
    
    print("File reorganization complete")

def get_available_languages(video_id):
    """Get all available languages for a video."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        languages = []
        
        for transcript in transcript_list:
            # Get the language code
            lang_code = transcript.language_code
            languages.append(lang_code)
        
        return languages
    except Exception as e:
        print(f"Error getting available languages for video {video_id}: {e}")
        return []

def controlled_delay(base_delay):
    """Add a controlled delay with jitter to avoid predictable patterns."""
    # Add random jitter (±20% of base delay)
    jitter = base_delay * 0.2 * (random.random() * 2 - 1)
    sleep_time = base_delay + jitter
    time.sleep(sleep_time)

def adjust_rate_for_ban_recovery(current_delay, current_workers):
    """
    Adjust rate limiting parameters when a ban is detected or after recovery.
    Returns new delay and workers count.
    """
    global original_delay, original_workers, ban_detected, ban_recovery_time
    
    # First time configuration - store original settings
    if original_delay is None:
        original_delay = current_delay
        original_workers = current_workers
    
    # If we detect a ban
    if not ban_detected:
        ban_detected = True
        print("\n⚠️ YouTube rate limit/ban detected! Switching to recovery mode...")
        print(f"Original settings: delay={original_delay}s, workers={original_workers}")
        print(f"Switching to slow mode: delay=5s, workers=1")
        return 5.0, 1  # Very slow settings during ban
    
    # If ban was already detected and this is called again
    if ban_recovery_time is None:
        # First recovery after ban lifted
        ban_recovery_time = time.time()
        print("\n✓ Ban appears to be lifted, starting recovery period...")
        print(f"Continuing slow mode for 5-7 minutes: delay=5s, workers=1")
        return 5.0, 1  # Keep very slow settings during initial recovery
    
    # Check if we're past the recovery period (5-7 minutes)
    minutes_since_recovery = (time.time() - ban_recovery_time) / 60
    if minutes_since_recovery < random.uniform(5, 7):
        # Still in recovery period
        return 5.0, 1  # Keep very slow settings during recovery period
    
    # Past recovery period - calculate half speed from original
    new_delay = original_delay * 2
    new_workers = max(1, original_workers // 2)
    
    # Update original values for potential future halving
    original_delay = new_delay
    original_workers = new_workers
    
    # Reset ban tracking for future detections
    ban_detected = False
    ban_recovery_time = None
    
    print(f"\n✓ Recovery period complete. Switching to half speed:")
    print(f"New settings: delay={new_delay}s, workers={new_workers}")
    
    return new_delay, new_workers

def download_transcript_with_retry(video_id, language, max_retries=3, base_delay=1.5):
    """Download transcript with retries and exponential backoff."""
    global ban_detected
    retries = 0
    while retries <= max_retries:
        try:
            # Add a delay before each request, longer after each retry
            if retries > 0:
                backoff_delay = base_delay * (2 ** retries)  # Exponential backoff
                print(f"Retry {retries}/{max_retries} for {video_id} - waiting {backoff_delay:.1f} seconds...")
                time.sleep(backoff_delay)
            
            # Add a small delay even on first attempt
            controlled_delay(base_delay)
            
            # Attempt to get the transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            return transcript, None  # Success
            
        except _errors.NoTranscriptFound:
            # No need to retry if transcript doesn't exist
            return None, f"No {language} transcript available"
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Don't retry for these specific cases:
            if "age-restricted" in error_str:
                return None, f"Age restricted video (requires authentication)"
            
            if "subtitles are disabled" in error_str:
                return None, f"Subtitles are disabled for this video"
                
            if "this video doesn't have" in error_str or "transcript unavailable" in error_str:
                return None, f"No transcript available for this video"
            
            # Check for rate limiting indicators
            if "429" in error_str or "too many requests" in error_str or "rate limit" in error_str:
                print(f"Rate limit detected for {video_id}. Backing off...")
                # Mark ban as detected for recovery process
                ban_detected = True
                
                if retries < max_retries:
                    retries += 1
                    # Use a longer delay for rate limit errors
                    backoff_delay = base_delay * (3 ** retries)
                    time.sleep(backoff_delay)
                else:
                    return None, f"Rate limited: {str(e)}"
            else:
                # For other errors, retry fewer times
                if retries < 1:  # Only retry once for non-rate-limit errors
                    retries += 1
                else:
                    return None, str(e)
    
    return None, "Maximum retries exceeded"

def download_transcript(video_data, language, output_dir, use_language_folders, download_txt, download_json, delay):
    """Download transcript for a single video."""
    video_id = video_data['id']
    title = sanitize_filename(video_data['title'])
    
    # Create filename with title and video ID at the end
    base_filename = f"{title}_{video_id}"
    
    # Set up directories based on whether we're using language folders
    if use_language_folders:
        # Language-specific folders
        lang_dir = os.path.join(output_dir, language)
        json_dir = os.path.join(lang_dir, "json")
        text_dir = lang_dir
        
        # Create language directory if it doesn't exist
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)
    else:
        # Original structure
        json_dir = os.path.join(output_dir, "json")
        text_dir = output_dir
    
    # Create json directory if it doesn't exist and we're downloading JSON
    if download_json and not os.path.exists(json_dir):
        os.makedirs(json_dir)
    
    # Define file paths
    json_filename = os.path.join(json_dir, f"{base_filename}_{language}.json")
    text_filename = os.path.join(text_dir, f"{base_filename}_{language}.txt")
    
    # Check if files already exist - only check files we plan to download
    files_exist = True
    if download_json and not os.path.exists(json_filename):
        files_exist = False
    if download_txt and not os.path.exists(text_filename):
        files_exist = False
    
    if files_exist:
        return {
            'success': True,
            'video_id': video_id,
            'title': title,
            'skipped': True,
            'language': language
        }
    
    # Download transcript with retry logic
    transcript, error = download_transcript_with_retry(video_id, language, base_delay=delay)
    
    if transcript:
        # Save transcript to JSON file if requested
        if download_json:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, ensure_ascii=False, indent=2)
        
        # Save text version if requested
        if download_txt:
            with open(text_filename, 'w', encoding='utf-8') as f:
                full_text = " ".join([item['text'] for item in transcript])
                f.write(full_text)
        
        return {
            'success': True,
            'video_id': video_id,
            'title': title,
            'skipped': False,
            'language': language
        }
    else:
        return {
            'success': False,
            'video_id': video_id,
            'title': title,
            'error': error,
            'language': language
        }

def download_transcripts_parallel(videos_data, languages, channel_name, download_all=False, 
                                 download_txt=True, download_json=True, delay=1.5, workers=3):
    """Download transcripts for all videos in parallel with rate limiting."""
    global ban_detected, ban_recovery_time
    
    # Create channel-specific directory
    output_dir = os.path.join("transcripts", channel_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # Detect existing languages in the folder
    existing_languages = detect_languages_in_folder(output_dir)
    print(f"Detected {len(existing_languages)} existing language(s) in folder: {', '.join(existing_languages) if existing_languages else 'None'}")
    
    # Determine if we should use language folders
    use_language_folders = should_use_language_folders(existing_languages, set(languages))
    
    # If we need to reorganize existing files when switching to language folders
    if use_language_folders:
        move_files_to_language_folders(output_dir, languages)
        print(f"Using language-specific folders for organization")
    else:
        print(f"Using standard folder structure (not using language folders)")
    
    successful = 0
    failed = 0
    skipped = 0
    
    # If download_all is True, we need to query available languages for the first video
    if download_all and videos_data:
        print("Checking available languages for the channel...")
        try:
            # Try to get available languages for the first video
            first_video = videos_data[0]['id']
            available_langs = get_available_languages(first_video)
            
            if available_langs:
                print(f"Found {len(available_langs)} available languages: {', '.join(available_langs)}")
                languages = available_langs
                # If downloading all languages, we will definitely use language folders
                use_language_folders = True
                # If we need to reorganize after finding all languages
                move_files_to_language_folders(output_dir, languages)
            else:
                print("No languages detected. Defaulting to specified languages.")
        except Exception as e:
            print(f"Error detecting available languages: {e}")
            print("Defaulting to specified languages.")
    
    file_types = []
    if download_txt:
        file_types.append("TXT")
    if download_json:
        file_types.append("JSON")
    
    print(f"\nDownloading {', '.join(file_types)} files in {len(languages)} language(s): {', '.join(languages)}")
    print(f"Rate limiting: {delay} second delay between requests with {workers} concurrent workers")
    print(f"Saving to directory: {output_dir}")
    print(f"Processing {len(videos_data)} videos...")
    
    # Track remaining tasks for reprocessing
    remaining_tasks = []
    for video in videos_data:
        for lang in languages:
            remaining_tasks.append((video, lang))
    
    # Process while we have remaining tasks and adjusting rate as needed
    current_delay = delay
    current_workers = workers
    
    while remaining_tasks:
        # Check if we need to adjust rate limiting due to bans
        if ban_detected:
            current_delay, current_workers = adjust_rate_for_ban_recovery(current_delay, current_workers)
            print(f"Adjusted rate limiting: {current_delay}s delay with {current_workers} workers")
        
        # Take a subset of tasks based on current worker count
        batch_size = min(len(remaining_tasks), 100)  # Process in batches of 100 or fewer
        current_batch = remaining_tasks[:batch_size]
        
        # Process videos with limited concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=current_workers) as executor:
            # Submit tasks for current batch
            future_to_task = {}
            for video, lang in current_batch:
                future = executor.submit(
                    download_transcript, 
                    video, 
                    lang, 
                    output_dir, 
                    use_language_folders, 
                    download_txt, 
                    download_json,
                    current_delay
                )
                future_to_task[future] = (video, lang)
            
            print(f"Processing batch of {len(future_to_task)} tasks with {current_workers} workers...")
            
            # Process results as they complete
            completed_tasks = []
            for i, future in enumerate(concurrent.futures.as_completed(future_to_task)):
                video, lang = future_to_task[future]
                completed_tasks.append((video, lang))
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        if result.get('skipped', False):
                            print(f"[{i+1}/{len(future_to_task)}] Skipped (already exists): {result['title'][:50]}... ({lang})")
                            skipped += 1
                        else:
                            print(f"[{i+1}/{len(future_to_task)}] Downloaded: {result['title'][:50]}... ({lang})")
                            successful += 1
                    else:
                        print(f"[{i+1}/{len(future_to_task)}] Failed for: {result['title'][:50]}... ({lang}) - {result.get('error', 'Unknown error')}")
                        failed += 1
                        
                    # Show progress every 10 tasks
                    if (i + 1) % 10 == 0 or i + 1 == len(future_to_task):
                        print(f"Progress: {i+1}/{len(future_to_task)} tasks processed ({successful} downloaded, {skipped} skipped, {failed} failed)")
                        
                except Exception as e:
                    print(f"[{i+1}/{len(future_to_task)}] Error processing {video['title'][:50]}... ({lang}): {str(e)}")
                    failed += 1
        
        # Remove completed tasks from remaining
        for task in completed_tasks:
            if task in remaining_tasks:
                remaining_tasks.remove(task)
        
        # If we still have tasks but had a ban, we might need to pause
        if remaining_tasks and ban_detected and ban_recovery_time is None:
            wait_time = random.uniform(300, 420)  # 5-7 minutes in seconds
            print(f"\n⚠️ Rate limit detected. Pausing for {wait_time/60:.1f} minutes before continuing...")
            time.sleep(wait_time)
            ban_recovery_time = time.time()  # Mark recovery start time
    
    print(f"\nTranscript download complete for {channel_name}.")
    print(f"Downloaded: {successful}")
    print(f"Skipped (already exist): {skipped}")
    print(f"Failed: {failed}")
    if use_language_folders:
        folder_structure = f"Transcripts organized in language folders under: {output_dir}"
    else:
        folder_structure = f"Transcripts saved in: {output_dir}"
    print(folder_structure)
    
    return successful, skipped, failed

def process_channel(channel_url, languages, download_all, download_txt, download_json, delay, workers):
    """Process a single channel."""
    # Get channel name for directory creation
    channel_name = get_channel_name(channel_url)
    print(f"Channel name: {channel_name}")
    
    # Get video metadata
    videos_data = get_videos_from_channel(channel_url)
    
    if not videos_data:
        print(f"No videos found for {channel_url}. Skipping channel.")
        return 0, 0, 0
    
    # Download transcripts
    return download_transcripts_parallel(
        videos_data, 
        languages, 
        channel_name, 
        download_all, 
        download_txt, 
        download_json,
        delay,
        workers
    )

def main():
    # Parse arguments
    try:
        urls, languages, download_all, download_txt, download_json, delay, workers = parse_arguments()
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        display_help()
        sys.exit(1)
    
    print("YouTube Channel Transcript Downloader")
    print("-" * 40)
    
    if download_all:
        print(f"Processing {len(urls)} channels with ALL available languages")
    else:
        print(f"Processing {len(urls)} channels with languages: {', '.join(languages)}")
    
    file_types = []
    if download_txt:
        file_types.append("TXT")
    if download_json:
        file_types.append("JSON")
    print(f"File types to download: {', '.join(file_types)}")
    print(f"Rate limiting: {delay}s delay between requests, {workers} concurrent workers")
    
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0
    
    # Process each channel
    for i, url in enumerate(urls):
        print(f"\n[Channel {i+1}/{len(urls)}] Processing: {url}")
        print("-" * 60)
        
        try:
            downloaded, skipped, failed = process_channel(
                url, 
                languages, 
                download_all, 
                download_txt, 
                download_json,
                delay,
                workers
            )
            total_downloaded += downloaded
            total_skipped += skipped
            total_failed += failed
        except Exception as e:
            print(f"Error processing channel {url}: {e}")
    
    # Print overall summary
    if len(urls) > 1:
        print("\n" + "=" * 60)
        print("OVERALL SUMMARY")
        print("=" * 60)
        print(f"Total channels processed: {len(urls)}")
        print(f"Total files downloaded: {total_downloaded}")
        print(f"Total files skipped (already exist): {total_skipped}")
        print(f"Total files failed: {total_failed}")
        print(f"Grand total: {total_downloaded + total_skipped + total_failed}")
        print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
