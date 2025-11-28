#!/usr/bin/env python3
"""
YouTube Channel Transcript Downloader - Refactored Version
A SOLID principles-based implementation with external TOML configuration.

Original Author: titusrugabunda (https://github.com/rugabunda)
Forked and Enhanced by: digi4care (https://github.com/digi4care)
"""

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
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple

# Third-party imports
try:
    from youtube_transcript_api import YouTubeTranscriptApi, _errors
    from tqdm import tqdm
    from colorama import Fore, Style, init as colorama_init
    import toml
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages:")
    print("pip install youtube-transcript-api tqdm colorama toml")
    sys.exit(1)

# Initialize colorama for cross-platform colored terminal text
colorama_init(autoreset=True)


@dataclass
class YTDLPOptions:
    """yt-dlp configuration options (passed directly to yt-dlp)"""

    # Output template for video files
    output: str = "%(title)s [%(id)s].%(ext)s"

    # Video filtering
    skip_download: bool = True
    max_downloads: int = 0
    playlist_items: str = ""

    # Download options
    concurrent_fragments: int = 1
    sleep_interval: float = 0.0
    max_sleep_interval: int = 20
    retry_sleep: str = ""

    # Format selection
    format: str = ""
    format_sort: str = ""

    # Output options
    restrict_filenames: bool = False
    no_warnings: bool = False

    # Logging
    verbose: bool = False
    quiet: bool = False

    def to_yt_dlp_flags(self) -> List[str]:
        """Convert options to yt-dlp command line flags"""
        flags = []

        if self.output and self.output != "%(title)s [%(id)s].%(ext)s":
            flags.extend(["--output", self.output])

        if self.skip_download:
            flags.append("--skip-download")

        if self.max_downloads > 0:
            flags.extend(["--max-downloads", str(self.max_downloads)])

        if self.playlist_items:
            flags.extend(["--playlist-items", self.playlist_items])

        if self.concurrent_fragments > 1:
            flags.extend(["--concurrent-fragments", str(self.concurrent_fragments)])

        if self.sleep_interval > 0:
            flags.extend(["--sleep-interval", str(self.sleep_interval)])

        if self.max_sleep_interval != 20:
            flags.extend(["--max-sleep-interval", str(self.max_sleep_interval)])

        if self.retry_sleep:
            flags.extend(["--retry-sleep", self.retry_sleep])

        if self.format:
            flags.extend(["--format", self.format])

        if self.format_sort:
            flags.extend(["--format-sort", self.format_sort])

        if self.restrict_filenames:
            flags.append("--restrict-filenames")

        if self.no_warnings:
            flags.append("--no-warnings")

        if self.verbose:
            flags.append("--verbose")

        if self.quiet:
            flags.append("--quiet")

        return flags


@dataclass
class TranscriptOptions:
    """Transcript-specific configuration options"""

    # Download settings
    download_formats: List[str] = field(default_factory=lambda: ["txt", "json"])
    use_language_folders: bool = True
    sanitize_filenames: bool = True
    output_dir: str = "./downloads"

    # Language handling
    default_language: str = "en"
    auto_detect_language: bool = True
    language_priority: List[str] = field(default_factory=lambda: ["en"])

    # Batch processing
    concurrent_workers: int = 1
    batch_size: int = 100
    max_videos_per_channel: int = 0

    # File organization
    organize_existing: bool = True
    timestamp_prefix_format: str = ""
    overwrite_existing: bool = False
    advanced_filename_sanitize: bool = False  # Use WordPress-style filename sanitization

    # Archive functionality
    enable_archive: bool = True  # Enable/disable archive-based resume functionality


@dataclass
class RateLimiting:
    """Rate limiting for transcript API"""

    base_delay: float = 1.5
    max_workers: int = 1
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    jitter_percentage: float = 0.2
    ban_recovery_time: Tuple[int, int] = (300, 420)
    rate_strategy: str = "balanced"
    strategy_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "conservative": 3.0,
        "balanced": 1.0,
        "aggressive": 0.5
    })

    def apply_strategy(self):
        """Apply the selected rate limiting strategy"""
        multiplier = self.strategy_multipliers.get(self.rate_strategy, 1.0)
        self.base_delay *= multiplier
        self.max_workers = max(1, int(self.max_workers / multiplier))


@dataclass
class APISettings:
    """YouTube Transcript API settings"""

    api_timeout: int = 600
    enable_cache: bool = True
    cache_dir: str = "./cache"
    cache_expiry_hours: int = 24


@dataclass
class UISettings:
    """UI and display settings"""

    show_progress: bool = True
    clear_screen: bool = True
    show_errors: bool = True
    color_scheme: str = "default"


@dataclass
class LoggingSettings:
    """Logging configuration"""

    level: str = "INFO"
    file: str = ""
    log_ytdlp_commands: bool = True
    command_log_file: str = "ytdlp_commands.log"


@dataclass
class PerformanceSettings:
    """Performance tuning"""

    memory_usage: str = "medium"
    network_speed: str = "medium"
    cpu_cores: int = 0


@dataclass
class DownloadConfig:
    """Complete configuration for YouTube Transcript Downloader"""

    yt_dlp: YTDLPOptions = field(default_factory=YTDLPOptions)
    transcripts: TranscriptOptions = field(default_factory=TranscriptOptions)
    rate_limiting: RateLimiting = field(default_factory=RateLimiting)
    api_settings: APISettings = field(default_factory=APISettings)
    ui: UISettings = field(default_factory=UISettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)

    def load_from_toml(self, config_path: str = "config.toml"):
        """Load configuration from TOML file"""
        try:
            with open(config_path, 'r') as f:
                config_data = toml.load(f)

            # Load yt-dlp options
            if 'yt_dlp' in config_data and 'options' in config_data['yt_dlp']:
                for key, value in config_data['yt_dlp']['options'].items():
                    if hasattr(self.yt_dlp, key):
                        setattr(self.yt_dlp, key, value)

            # Load transcript options
            if 'transcripts' in config_data:
                for key, value in config_data['transcripts'].items():
                    if hasattr(self.transcripts, key):
                        setattr(self.transcripts, key, value)

            # Load rate limiting
            if 'rate_limiting' in config_data:
                for key, value in config_data['rate_limiting'].items():
                    if key == 'ban_recovery_time' and isinstance(value, list):
                        value = tuple(value)
                    if hasattr(self.rate_limiting, key):
                        setattr(self.rate_limiting, key, value)

                # Handle strategy multipliers
                if 'strategy_multipliers' in config_data['rate_limiting']:
                    self.rate_limiting.strategy_multipliers = config_data['rate_limiting']['strategy_multipliers']

            # Load API settings
            if 'api_settings' in config_data or 'api' in config_data:
                api_section = config_data.get('api_settings', config_data.get('api', {}))
                for key, value in api_section.items():
                    if hasattr(self.api_settings, key):
                        setattr(self.api_settings, key, value)

            # Load UI settings
            if 'ui_settings' in config_data or 'ui' in config_data:
                ui_section = config_data.get('ui_settings', config_data.get('ui', {}))
                for key, value in ui_section.items():
                    if hasattr(self.ui, key):
                        setattr(self.ui, key, value)

            # Load logging settings
            if 'logging' in config_data:
                for key, value in config_data['logging'].items():
                    if hasattr(self.logging, key):
                        setattr(self.logging, key, value)

            # Load performance settings
            if 'performance' in config_data:
                for key, value in config_data['performance'].items():
                    if hasattr(self.performance, key):
                        setattr(self.performance, key, value)

            # Apply rate limiting strategy
            self.rate_limiting.apply_strategy()

        except FileNotFoundError:
            logging.warning(f"Config file {config_path} not found, using defaults")
        except Exception as e:
            logging.error(f"Error loading config: {e}, using defaults")

    def update_from_args(self, args: argparse.Namespace):
        """Update configuration from command line arguments"""

        # yt-dlp options
        if hasattr(args, 'output_template') and args.output_template:
            self.yt_dlp.output = args.output_template

        if hasattr(args, 'skip_download') and args.skip_download:
            self.yt_dlp.skip_download = args.skip_download

        if hasattr(args, 'format') and args.format:
            self.yt_dlp.format = args.format

        if hasattr(args, 'format_sort') and args.format_sort:
            self.yt_dlp.format_sort = args.format_sort

        if hasattr(args, 'sleep_interval') and args.sleep_interval:
            self.yt_dlp.sleep_interval = args.sleep_interval

        if hasattr(args, 'verbose') and args.verbose:
            self.yt_dlp.verbose = args.verbose

        if hasattr(args, 'quiet') and args.quiet:
            self.yt_dlp.quiet = args.quiet

        # Transcript options
        if hasattr(args, 'transcript_format') and args.transcript_format:
            self.transcripts.download_formats = [args.transcript_format]

        if hasattr(args, 'concurrent_workers') and args.concurrent_workers:
            self.transcripts.concurrent_workers = args.concurrent_workers

        if hasattr(args, 'batch_size') and args.batch_size:
            self.transcripts.batch_size = args.batch_size

        if hasattr(args, 'default_language') and args.default_language:
            self.transcripts.default_language = args.default_language

        if hasattr(args, 'overwrite_existing') and args.overwrite_existing:
            self.transcripts.overwrite_existing = args.overwrite_existing

        if hasattr(args, 'organize_existing') and not args.organize_existing:
            self.transcripts.organize_existing = args.organize_existing

        if hasattr(args, 'advanced_filename_sanitize') and args.advanced_filename_sanitize:
            self.transcripts.advanced_filename_sanitize = args.advanced_filename_sanitize

        # Standard flags
        if hasattr(args, 'txt') and args.txt:
            self.transcripts.download_formats = ["txt"]

        if hasattr(args, 'json') and args.json:
            self.transcripts.download_formats = ["json"]

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages"""
    
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.WHITE,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
            if record.levelno == logging.INFO:
                record.msg = f"{Fore.WHITE}{record.msg}{Style.RESET_ALL}"
            elif record.levelno == logging.WARNING:
                record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
            elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
                record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        return super().format(record)


class YouTubeAPIAdapter:
    """Handles all YouTube API operations (Single Responsibility Principle)"""

    def __init__(self, config: DownloadConfig):
        self.config = config
        self.active_processes = []

    def _log_ytdlp_command(self, command: List[str], url: str, purpose: str = ""):
        """Log yt-dlp command for debugging"""
        if self.config.logging.log_ytdlp_commands:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cmd_str = " ".join(command)
            log_entry = f"""
[{timestamp}] Executing yt-dlp ({purpose}):
  Command: {cmd_str}
  URL: {url}
========================================
"""
            with open(self.config.logging.command_log_file, "a") as f:
                f.write(log_entry)

    def get_channel_name(self, channel_url: str) -> str:
        """Get channel name using yt-dlp"""
        logging.info("Retrieving channel name...")

        spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner_idx = 0
        process = None

        try:
            # Build command using config
            command = ["yt-dlp"]

            # Add yt-dlp flags from config
            command.extend(self.config.yt_dlp.to_yt_dlp_flags())

            # Add channel name extraction
            command.extend([
                "--print",
                "%(channel)s",
                "--playlist-items",
                "1",
                channel_url,
            ])

            # Log command
            self._log_ytdlp_command(command, channel_url, "get channel name")

            logging.debug(f"Running command: {' '.join(command)}")
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.active_processes.append(process)

            # Display spinner while waiting
            while process.poll() is None:
                sys.stdout.write(
                    f"\r{Fore.CYAN}Fetching channel info... {spinner[spinner_idx]}{Style.RESET_ALL}"
                )
                sys.stdout.flush()
                spinner_idx = (spinner_idx + 1) % len(spinner)
                time.sleep(0.1)

            stdout, stderr = process.communicate()
            self.active_processes.remove(process)

            # Clear spinner line
            sys.stdout.write("\r" + " " * 50 + "\r")
            sys.stdout.flush()

            channel_name = stdout.strip()

            if not channel_name:
                logging.warning("Couldn't retrieve channel name, using default.")
                return "youtube_channel"

            logging.info(f"Channel name: {Fore.CYAN}{channel_name}{Style.RESET_ALL}")
            return self._sanitize_filename(channel_name)

        except subprocess.TimeoutExpired:
            logging.error("Timeout while fetching channel name")
            self._cleanup_process(process)
            return "youtube_channel"
        except Exception as e:
            logging.error(f"Error fetching channel name: {e}")
            self._cleanup_process(process)
            return "youtube_channel"
    
    def get_videos_from_channel(self, channel_url: str) -> List[Dict]:
        """Get all videos from a YouTube channel"""
        logging.info(f"Fetching videos from: {Fore.CYAN}{channel_url}{Style.RESET_ALL}")
        logging.info("This may take a while for channels with many videos...")

        print(f"{Fore.CYAN}Executing yt-dlp... (please wait){Style.RESET_ALL}")

        try:
            # Build command using config
            command = ["yt-dlp"]

            # Add yt-dlp flags from config
            command.extend(self.config.yt_dlp.to_yt_dlp_flags())

            # Add video extraction
            command.extend([
                "--flat-playlist",
                "--print",
                "%(id)s %(title)s",
                channel_url,
            ])

            # Log command
            self._log_ytdlp_command(command, channel_url, "get videos list")

            logging.debug(f"Running command: {' '.join(command)}")

            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.active_processes.append(process)

            stdout, stderr = process.communicate(timeout=self.config.api_settings.api_timeout)
            self.active_processes.remove(process)

            if not stdout.strip():
                logging.error("No video data returned. Check the channel URL.")
                return []

            videos_data = []
            lines = stdout.strip().split("\n")

            if self.config.transcripts.max_videos_per_channel > 0:
                lines = lines[:self.config.transcripts.max_videos_per_channel]

            print(f"{Fore.GREEN}Found {len(lines)} videos. Processing...{Style.RESET_ALL}")

            for line in lines:
                if line:
                    parts = line.split(maxsplit=1)
                    if len(parts) >= 2:
                        video_id = parts[0]
                        title = parts[1]
                        videos_data.append({"id": video_id, "title": title})
                    else:
                        logging.warning(f"Couldn't parse video data from: {line}")

            logging.info(
                f"Total videos found: {Fore.GREEN}{len(videos_data)}{Style.RESET_ALL}"
            )
            return videos_data

        except subprocess.TimeoutExpired:
            logging.error(
                "Timeout while fetching videos list. Try again or use a different channel."
            )
            self._cleanup_process(process)
            return []
        except Exception as e:
            logging.error(f"Error fetching videos from channel: {e}")
            self._cleanup_process(process)
            if stderr:
                logging.error(f"Error output: {stderr}")
            return []

    def get_playlists_from_channel(self, channel_url: str) -> List[Dict]:
        """Get all playlists from a channel's playlists page"""
        logging.info(f"Fetching playlists from: {Fore.CYAN}{channel_url}{Style.RESET_ALL}")

        try:
            # Build command using config
            command = ["yt-dlp"]
            command.extend(self.config.yt_dlp.to_yt_dlp_flags())

            command.extend([
                "--print",
                "%(playlist_autonumber)s\t%(playlist_title)s\t%(playlist_id)s",
                channel_url,
            ])

            self._log_ytdlp_command(command, channel_url, "get playlists list")

            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.active_processes.append(process)

            stdout, stderr = process.communicate(timeout=self.config.api_settings.api_timeout)
            self.active_processes.remove(process)

            if not stdout.strip():
                logging.error("No playlist data returned.")
                return []

            playlists = []
            lines = stdout.strip().split("\n")

            for line in lines:
                if line:
                    # Parse: playlist_autonumber<TAB>playlist_title<TAB>playlist_id
                    # Use split('\t') to handle titles with spaces reliably
                    parts = line.split('\t')

                    if len(parts) >= 3:
                        playlist_id = parts[2].strip()
                        playlist_title = parts[1].strip()

                        # Validate playlist_id (should be alphanumeric + some chars)
                        if playlist_id and len(playlist_id) > 5:
                            playlists.append({
                                "id": playlist_id,
                                "title": playlist_title
                            })
                            logging.debug(f"Parsed playlist: '{playlist_title}' -> ID: {playlist_id}")
                        else:
                            logging.warning(f"Invalid playlist ID: '{playlist_id}' from line: {line}")
                    else:
                        logging.warning(f"Couldn't parse playlist data from: {line}")

            logging.info(
                f"Total playlists found: {Fore.GREEN}{len(playlists)}{Style.RESET_ALL}"
            )

            # Remove duplicates based on playlist_id
            seen_ids = set()
            unique_playlists = []
            for playlist in playlists:
                if playlist["id"] not in seen_ids:
                    seen_ids.add(playlist["id"])
                    unique_playlists.append(playlist)

            if len(unique_playlists) < len(playlists):
                logging.warning(f"Removed {len(playlists) - len(unique_playlists)} duplicate playlists")

            return unique_playlists

        except subprocess.TimeoutExpired:
            logging.error("Timeout while fetching playlists list.")
            self._cleanup_process(process)
            return []
        except Exception as e:
            logging.error(f"Error fetching playlists: {e}")
            self._cleanup_process(process)
            return []
    
    def get_available_languages_with_quality(self, video_id: str) -> List[Dict]:
        """Get available transcript languages with quality scores"""
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id)
            transcripts = []

            for transcript in transcript_list:
                lang_code = transcript.language_code
                is_manual = not transcript.is_generated
                is_auto = transcript.is_generated

                quality_score = 0
                if is_manual:
                    quality_score = 100
                elif is_auto:
                    quality_score = 50

                transcripts.append({
                    "language_code": lang_code,
                    "quality_score": quality_score,
                    "is_manual": is_manual,
                    "is_auto": is_auto,
                    "translation_languages": transcript.translation_languages if hasattr(transcript, 'translation_languages') else []
                })

            return transcripts
        except Exception as e:
            logging.error(f"Error getting available languages for video {video_id}: {e}")
            return []

    def download_transcript(self, video_id: str, requested_language: str) -> Dict:
        """Download a single transcript with fallback logic"""
        available_transcripts = self.get_available_languages_with_quality(video_id)

        if not available_transcripts:
            return {
                "success": False,
                "error": "No transcripts available for this video",
                "retry": False
            }

        languages_to_try = [requested_language]

        if requested_language not in [t["language_code"] for t in available_transcripts]:
            if self.config.transcripts.language_priority:
                for lang in self.config.transcripts.language_priority:
                    if lang != requested_language and lang in [t["language_code"] for t in available_transcripts]:
                        languages_to_try.append(lang)

        languages_to_try.append("en")

        for lang in languages_to_try:
            for transcript_info in available_transcripts:
                if transcript_info["language_code"] == lang:
                    if transcript_info["quality_score"] >= 50:
                        try:
                            transcript = YouTubeTranscriptApi().fetch(video_id, languages=[lang])
                            return {
                                "success": True,
                                "transcript": transcript.to_raw_data(),
                                "language": lang,
                                "quality_score": transcript_info["quality_score"],
                                "is_manual": transcript_info["is_manual"],
                                "fallback_used": lang != requested_language
                            }
                        except _errors.NoTranscriptFound:
                            continue
                        except _errors.RequestBlocked:
                            return {
                                "success": False,
                                "error": "YouTube Transcript API rate limited - please wait a few minutes",
                                "retry": True
                            }
                        except Exception as e:
                            return {
                                "success": False,
                                "error": str(e),
                                "retry": True
                            }

        return {
            "success": False,
            "error": f"No transcript available in requested language: {requested_language}",
            "retry": False
        }
    
    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid characters from filenames"""
        if self.config.transcripts.sanitize_filenames:
            return re.sub(r'[\\/*?:"<>|]', "_", name)
        return name
    
    def _cleanup_process(self, process):
        """Clean up subprocess properly"""
        if process:
            try:
                if process.poll() is None:
                    process.terminate()
                if process in self.active_processes:
                    self.active_processes.remove(process)
            except Exception as e:
                logging.error(f"Error cleaning up process: {e}")


class FileManager:
    """Handles all file operations (Single Responsibility Principle)"""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
    
    def get_archive_path(self, channel_dir: str) -> str:
        """Get the path to the archive file for a channel"""
        return os.path.join(channel_dir, ".transcript_archive.txt")
    
    def detect_existing_languages(self, channel_dir: str) -> Set[str]:
        """Detect existing transcript languages in a channel directory"""
        languages = set()

        if not os.path.exists(channel_dir):
            return languages

        # Check for dedicated language folders
        for item in os.listdir(channel_dir):
            item_path = os.path.join(channel_dir, item)
            if (
                os.path.isdir(item_path)
                and re.match(r"^[a-zA-Z\-]{2,10}$", item)
                and item != "json"
            ):
                languages.add(item)

        # If no language folders, check file suffixes
        if not languages:
            for file in os.listdir(channel_dir):
                if file.endswith(".txt"):
                    match = re.search(r"_([a-zA-Z\-]{2,10})\.txt$", file)
                    if match:
                        languages.add(match.group(1))

            # Check JSON files in json folder
            json_dir = os.path.join(channel_dir, "json")
            if os.path.exists(json_dir) and os.path.isdir(json_dir):
                for file in os.listdir(json_dir):
                    if file.endswith(".json"):
                        match = re.search(r"_([a-zA-Z\-]{2,10})\.json$", file)
                        if match:
                            languages.add(match.group(1))

        return languages
    
    def should_use_language_folders(self, existing_languages: Set[str], 
                                   requested_languages: List[str]) -> bool:
        """Determine if we should use language-specific folders"""
        if len(requested_languages) > 1:
            return True
        if len(existing_languages) > 1:
            return True
        if len(requested_languages) == 1 and len(existing_languages) == 1:
            if list(requested_languages)[0] not in existing_languages:
                return True
        if len(requested_languages) == 1 and len(existing_languages) == 0:
            return False
        return True
    
    def organize_files_by_language(self, channel_dir: str, languages: List[str]):
        """Move existing files to language-specific folders"""
        if not os.path.exists(channel_dir):
            return

        logging.info(
            f"{Fore.YELLOW}Reorganizing existing files into language folders...{Style.RESET_ALL}"
        )

        # Create language directories
        for lang in languages:
            lang_dir = os.path.join(channel_dir, lang)
            os.makedirs(lang_dir, exist_ok=True)
            json_dir = os.path.join(lang_dir, "json")
            os.makedirs(json_dir, exist_ok=True)

        # Move files
        files_to_move = []
        
        # Move TXT files
        for file in os.listdir(channel_dir):
            if file.endswith(".txt"):
                for lang in languages:
                    if f"_{lang}.txt" in file:
                        files_to_move.append((file, lang, "txt"))

        # Move JSON files
        json_dir = os.path.join(channel_dir, "json")
        if os.path.exists(json_dir) and os.path.isdir(json_dir):
            for file in os.listdir(json_dir):
                if file.endswith(".json"):
                    for lang in languages:
                        if f"_{lang}.json" in file:
                            files_to_move.append((file, lang, "json"))

        # Actually move the files
        if files_to_move:
            with tqdm(
                total=len(files_to_move),
                desc=f"{Fore.YELLOW}Moving files{Style.RESET_ALL}",
                colour="yellow",
            ) as pbar:
                for file, lang, file_type in files_to_move:
                    if file_type == "txt":
                        src = os.path.join(channel_dir, file)
                        dst = os.path.join(channel_dir, lang, file)
                    else:
                        src = os.path.join(channel_dir, "json", file)
                        dst = os.path.join(channel_dir, lang, "json", file)

                    if not os.path.exists(dst):
                        try:
                            shutil.move(src, dst)
                            pbar.update(1)
                        except Exception as e:
                            logging.error(f"Error moving file {file}: {e}")
                            pbar.update(1)
                    else:
                        pbar.update(1)

        # Clean up empty json directory
        json_dir = os.path.join(channel_dir, "json")
        if os.path.exists(json_dir) and os.path.isdir(json_dir):
            if not os.listdir(json_dir):
                try:
                    os.rmdir(json_dir)
                except Exception:
                    pass

        logging.info(f"{Fore.GREEN}File reorganization complete{Style.RESET_ALL}")
    
    def save_transcript(self, transcript_data: List[Dict], video_info: Dict,
                       language: str, output_dir: str, use_language_folders: bool) -> Dict:
        """Save transcript to file(s)"""
        results = {"saved_files": [], "skipped_files": []}

        # Sanitize video title
        safe_title = sanitize_filename(video_info["title"], self.config.transcripts.advanced_filename_sanitize)

        # Add timestamp prefix if configured
        timestamp_prefix = ""
        if self.config.transcripts.timestamp_prefix_format:
            timestamp_prefix = datetime.now().strftime(self.config.transcripts.timestamp_prefix_format) + "_"

        # Determine file paths
        if use_language_folders:
            base_dir = os.path.join(output_dir, language)
        else:
            base_dir = output_dir

        os.makedirs(base_dir, exist_ok=True)

        # Save TXT format
        if "txt" in self.config.transcripts.download_formats:
            txt_filename = f"{timestamp_prefix}{safe_title}_{language}.txt"
            txt_path = os.path.join(base_dir, txt_filename)
            if os.path.exists(txt_path):
                results["skipped_files"].append(txt_path)
            else:
                try:
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        for entry in transcript_data:
                            f.write(f"{entry['text']}\n")
                    results["saved_files"].append(txt_path)
                except Exception as e:
                    logging.error(f"Error saving TXT file: {e}")

        # Save JSON format
        if "json" in self.config.transcripts.download_formats:
            if use_language_folders:
                json_base_dir = os.path.join(base_dir, "json")
            else:
                json_base_dir = os.path.join(output_dir, "json")

            os.makedirs(json_base_dir, exist_ok=True)
            json_filename = f"{timestamp_prefix}{safe_title}_{language}.json"
            json_path = os.path.join(json_base_dir, json_filename)
            
            if os.path.exists(json_path):
                results["skipped_files"].append(json_path)
            else:
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(transcript_data, f, ensure_ascii=False, indent=2)
                    results["saved_files"].append(json_path)
                except Exception as e:
                    logging.error(f"Error saving JSON file: {e}")
        
        return results


class ArchiveManager:
    """Handles archive file operations for resume functionality"""

    def __init__(self, config: DownloadConfig):
        self.config = config

    def load_processed_videos(self, archive_path: str) -> Set[str]:
        """Load set of already processed video IDs from archive file"""
        processed_videos = set()

        if not os.path.exists(archive_path):
            logging.debug(f"Archive file does not exist: {archive_path}")
            return processed_videos

        try:
            with open(archive_path, 'r', encoding='utf-8') as f:
                for line in f:
                    video_id = line.strip()
                    if video_id:  # Skip empty lines
                        processed_videos.add(video_id)
            logging.debug(f"Loaded {len(processed_videos)} processed video IDs from archive")
        except Exception as e:
            logging.warning(f"Error reading archive file {archive_path}: {e}")

        return processed_videos

    def add_processed_video(self, archive_path: str, video_id: str):
        """Add a video ID to the archive file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            with open(archive_path, 'a', encoding='utf-8') as f:
                f.write(f"{video_id}\n")
            logging.debug(f"Added video ID {video_id} to archive")
        except Exception as e:
            logging.error(f"Error writing to archive file {archive_path}: {e}")

    def filter_new_videos(self, videos: List[Dict], processed_videos: Set[str]) -> List[Dict]:
        """Filter video list to only include videos not yet processed"""
        new_videos = []
        skipped_count = 0

        for video in videos:
            video_id = video.get("id")
            if video_id and video_id not in processed_videos:
                new_videos.append(video)
            else:
                skipped_count += 1
                logging.debug(f"Skipping already processed video: {video_id}")

        if skipped_count > 0:
            logging.info(f"Skipped {skipped_count} already processed video(s), processing {len(new_videos)} new video(s)")

        return new_videos


class RateLimiter:
    """Handles rate limiting and ban recovery (Single Responsibility Principle)"""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        self.original_delay = None
        self.original_workers = None
        self.ban_detected = False
        self.ban_recovery_time = None
    
    def apply_delay(self):
        """Apply controlled delay with jitter"""
        jitter = self.config.rate_limiting.base_delay * self.config.rate_limiting.jitter_percentage * (random.random() * 2 - 1)
        sleep_time = self.config.rate_limiting.base_delay + jitter
        time.sleep(sleep_time)
    
    def adjust_for_ban(self, current_delay: float, current_workers: int) -> Tuple[float, int]:
        """Adjust settings when ban is detected"""
        if self.original_delay is None:
            self.original_delay = current_delay
            self.original_workers = current_workers

        if not self.ban_detected:
            self.ban_detected = True
            print(
                f"\n{Fore.RED}⚠️  YouTube rate limit/ban detected! Switching to recovery mode...{Style.RESET_ALL}"
            )
            print(
                f"{Fore.YELLOW}Original settings: delay={self.original_delay}s, workers={self.original_workers}{Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN}Switching to slow mode: delay=5s, workers=1{Style.RESET_ALL}"
            )
            return 5.0, 1

        if self.ban_recovery_time is None:
            self.ban_recovery_time = time.time()
            print(
                f"\n{Fore.GREEN}✓ Ban appears to be lifted, starting recovery period...{Style.RESET_ALL}"
            )
            print(
                f"{Fore.YELLOW}Continuing slow mode for 5-7 minutes: delay=5s, workers=1{Style.RESET_ALL}"
            )
            return 5.0, 1

        minutes_since_recovery = (time.time() - self.ban_recovery_time) / 60
        if minutes_since_recovery < random.uniform(5, 7):
            return 5.0, 1

        # Past recovery period - calculate half speed from original
        new_delay = self.original_delay * 2
        new_workers = max(1, self.original_workers // 2)

        self.original_delay = new_delay
        self.original_workers = new_workers
        self.ban_detected = False
        self.ban_recovery_time = None

        print(
            f"\n{Fore.GREEN}✓ Recovery period complete. Switching to half speed:{Style.RESET_ALL}"
        )
        print(
            f"{Fore.YELLOW}New settings: delay={new_delay}s, workers={new_workers}{Style.RESET_ALL}"
        )

        return new_delay, new_workers
    
    def is_in_recovery(self) -> bool:
        """Check if still in recovery period"""
        return self.ban_detected and self.ban_recovery_time is not None


class ProgressReporter:
    """Handles all progress reporting and UI (Single Responsibility Principle)"""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
    
    def display_logo(self):
        """Display application logo"""
        logo = rf"""
{Fore.CYAN}╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
{Fore.CYAN}┃ {Fore.YELLOW}__   __          _____      _            _____                          {Fore.CYAN}┃
{Fore.CYAN}┃ {Fore.YELLOW}\ \ / /__  _   _|_   _|   _| |__   ___  |_   _| __ __ _ _ __  ___  ___  {Fore.CYAN}┃
{Fore.CYAN}┃ {Fore.YELLOW} \ V / _ \| | | | | || | | | '_ \ / _ \   | || '__/ _` | '_ \/ __|/ __| {Fore.CYAN}┃
{Fore.CYAN}┃ {Fore.YELLOW}  | | (_) | |_| | | || |_| | |_) |  __/   | || | | (_| | | | \__ \ (__  {Fore.CYAN}┃
{Fore.CYAN}┃ {Fore.YELLOW}  |_|\___/ \__,_| |_| \__,_|_.__/ \___|   |_||_|  \__,_|_| |_|___/\___| {Fore.CYAN}┃
{Fore.CYAN}┃                                                                         {Fore.CYAN}┃
{Fore.CYAN}┃ {Fore.GREEN}Channel Transcript Downloader                                    v2.0.0 {Fore.CYAN}┃
{Fore.CYAN}╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
{Style.RESET_ALL}"""
        print(logo)
    
    def display_help(self):
        """Display help information"""
        if self.config.ui.show_progress:
            self.display_logo()
        
        print(f"{Fore.CYAN}=" * 80)
        print(f"{Fore.YELLOW}USAGE INSTRUCTIONS")
        print(f"{Fore.CYAN}=" * 80)
        print("\nThis script downloads transcripts for videos on YouTube channels or individual videos.")
        print("It creates a separate folder for each channel and organizes files into subdirectories.")
        print(f"{Fore.YELLOW}Downloads are processed with rate limiting to avoid YouTube IP bans.")
        print("Files that already exist will be skipped, allowing you to resume or update channels.")

        print(f"\n{Fore.GREEN}USAGE:")
        print("  python Youtube_Transcribe.py [options] <channel_or_video_url(s)>")
        print("  Or with uv: uv run python Youtube_Transcribe.py [options] <url(s)>")

        print(f"\n{Fore.GREEN}CONFIGURATION:")
        print("  --create-config     Create default config.toml file")
        print("  --show-config       Show current configuration")
        print("  Edit config.toml to customize settings")

        print(f"\n{Fore.GREEN}EXAMPLES:")
        print(f"{Fore.CYAN}  # Download transcript for a single YouTube video")
        print("  uv run python Youtube_Transcribe.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -en")
        print(f"{Fore.CYAN}  # Download English transcripts from a channel")
        print("  uv run python Youtube_Transcribe.py https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw -en")
        print(f"{Fore.CYAN}  # Download multiple languages")
        print("  uv run python Youtube_Transcribe.py https://youtube.com/c/channel1 -en -es -fr")
        print(f"{Fore.CYAN}  # Download all available languages")
        print("  uv run python Youtube_Transcribe.py https://youtube.com/c/channel1 -all")

        print(f"\n{Fore.GREEN}REQUIREMENTS:")
        print("  - python 3.6+")
        print("  - youtube_transcript_api (pip install youtube-transcript-api)")
        print("  - yt-dlp (pip install yt-dlp)")
        print("  - colorama (pip install colorama)")
        print("  - tqdm (pip install tqdm)")
        print("  - toml (pip install toml)")
        print(f"{Fore.CYAN}=" * 80)
    
    def show_progress(self, current: int, total: int, status: str = ""):
        """Show progress bar"""
        if self.config.show_progress:
            # Progress is handled by tqdm in the main class
            pass
    
    def display_summary(self, stats: Dict):
        """Display download summary"""
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}OVERALL SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total channels processed: {stats.get('channels', 0)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Total files downloaded: {stats.get('downloaded', 0)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}↺ Total files skipped (already exist): {stats.get('skipped', 0)}{Style.RESET_ALL}")
        print(f"{Fore.RED}✗ Total files failed: {stats.get('failed', 0)}{Style.RESET_ALL}")

        total = stats.get('downloaded', 0) + stats.get('skipped', 0) + stats.get('failed', 0)
        if total > 0:
            dl_percent = int((stats.get('downloaded', 0) / total) * 100)
            skip_percent = int((stats.get('skipped', 0) / total) * 100)
            fail_percent = int((stats.get('failed', 0) / total) * 100)

            remainder = 100 - (dl_percent + skip_percent + fail_percent)
            dl_percent += remainder

            print("\nResults distribution:")
            bar_width = 50
            dl_width = int(bar_width * dl_percent / 100)
            skip_width = int(bar_width * skip_percent / 100)
            fail_width = bar_width - dl_width - skip_width

            print(
                f"[{Fore.GREEN}{dl_width * '■'}{Fore.CYAN}{skip_width * '■'}{Fore.RED}{fail_width * '■'}{Style.RESET_ALL}]"
            )
            print(
                f"{Fore.GREEN}■ Downloaded ({dl_percent}%){Style.RESET_ALL} {Fore.CYAN}■ Skipped ({skip_percent}%){Style.RESET_ALL} {Fore.RED}■ Failed ({fail_percent}%){Style.RESET_ALL}"
            )

        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")


class YouTubeTranscriptDownloader:
    """Main orchestrator class following SOLID principles"""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        self.youtube_api = YouTubeAPIAdapter(config)
        self.file_manager = FileManager(config)
        self.rate_limiter = RateLimiter(config)
        self.progress_reporter = ProgressReporter(config)
        self.archive_manager = ArchiveManager(config)
        self._setup_logging()
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter("%(message)s"))

        logger = logging.getLogger()
        logger.setLevel(getattr(logging, self.config.logging.level.upper()))
        logger.addHandler(handler)

        if self.config.logging.file:
            file_handler = logging.FileHandler(self.config.logging.file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            print(f"\n{Fore.YELLOW}Script termination requested. Cleaning up...{Style.RESET_ALL}")
            for process in self.youtube_api.active_processes:
                try:
                    if process.poll() is None:
                        process.terminate()
                except Exception as e:
                    print(f"{Fore.RED}Error terminating process: {e}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Cleanup complete. Exiting.{Style.RESET_ALL}")
            os._exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, "SIGTSTP"):
            signal.signal(signal.SIGTSTP, signal_handler)
    
    def process_channels(self, urls: List[str], languages: List[str], 
                        download_all: bool, formats: List[str]) -> Dict:
        """Process multiple channels"""
        total_stats = {"channels": len(urls), "downloaded": 0, "skipped": 0, "failed": 0}
        
        for i, url in enumerate(urls):
            print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}CHANNEL {i + 1}/{len(urls)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            logging.info(f"Processing: {Fore.CYAN}{url}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

            try:
                downloaded, skipped, failed = self.process_single_channel(
                    url, languages, download_all, formats
                )
                total_stats["downloaded"] += downloaded
                total_stats["skipped"] += skipped
                total_stats["failed"] += failed
            except Exception as e:
                logging.error(f"Error processing channel {url}: {e}")
                total_stats["failed"] += 1

        return total_stats
    
    def process_single_channel(self, channel_url: str, languages: List[str],
                              download_all: bool, formats: List[str]) -> Tuple[int, int, int]:
        """Process a single channel"""
        # Check if this is a playlists URL
        if "/playlists" in channel_url:
            return self._process_playlists_url(channel_url, languages, download_all, formats)

        # Get channel name
        channel_name = self.youtube_api.get_channel_name(channel_url)

        # Get video metadata
        videos_data = self.youtube_api.get_videos_from_channel(channel_url)

        if not videos_data:
            logging.warning(f"No videos found for {channel_url}. Skipping channel.")
            return 0, 0, 0

        # Download transcripts
        return self.download_transcripts_batch(videos_data, languages, channel_name,
                                              download_all, formats)

    def _process_playlists_url(self, channel_url: str, languages: List[str],
                              download_all: bool, formats: List[str]) -> Tuple[int, int, int]:
        """Process playlists URL - get all playlists and process each individually"""
        logging.info(f"{Fore.YELLOW}Detected playlists URL - activating playlist mode{Style.RESET_ALL}")

        # Get playlists from channel
        playlists = self.youtube_api.get_playlists_from_channel(channel_url)

        if not playlists:
            logging.warning(f"No playlists found for {channel_url}")
            return 0, 0, 0

        # Get channel name
        base_url = channel_url.replace("/playlists", "")
        channel_name = self.youtube_api.get_channel_name(base_url)

        total_downloaded = 0
        total_skipped = 0
        total_failed = 0

        # Process each playlist individually
        for i, playlist in enumerate(playlists):
            playlist_id = playlist["id"]
            playlist_title = sanitize_folder_name(playlist["title"])
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"

            print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}PLAYLIST {i + 1}/{len(playlists)}: {playlist_title}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            logging.info(f"Processing playlist: {Fore.CYAN}{playlist_title}{Style.RESET_ALL}")

            # Use folder structure: ChannelName/PlaylistName/
            folder_name = playlist_title
            videos_data = self.youtube_api.get_videos_from_channel(playlist_url)

            if not videos_data:
                logging.warning(f"No videos found in playlist '{playlist_title}'. Skipping.")
                continue

            # Download transcripts
            downloaded, skipped, failed = self.download_transcripts_batch(
                videos_data, languages, f"{channel_name}/{folder_name}",
                download_all, formats
            )

            total_downloaded += downloaded
            total_skipped += skipped
            total_failed += failed

        return total_downloaded, total_skipped, total_failed
    
    def download_transcripts_batch(self, videos: List[Dict], languages: List[str],
                                  channel_name: str, download_all: bool,
                                  formats: List[str]) -> Tuple[int, int, int]:
        """Download transcripts in batches"""
        # Create output directory
        output_dir = os.path.join(self.config.transcripts.output_dir, channel_name)
        os.makedirs(output_dir, exist_ok=True)

        # Archive functionality - only if enabled
        if self.config.transcripts.enable_archive:
            archive_path = self.file_manager.get_archive_path(output_dir)
            processed_videos = self.archive_manager.load_processed_videos(archive_path)
            videos = self.archive_manager.filter_new_videos(videos, processed_videos)
            
            if not videos:
                logging.info(f"All {len(processed_videos)} videos in {channel_name} already processed. Skipping channel.")
                return 0, len(processed_videos), 0
        
        # Detect existing languages
        existing_languages = self.file_manager.detect_existing_languages(output_dir)
        
        # Determine folder structure
        use_language_folders = self.file_manager.should_use_language_folders(
            existing_languages, languages
        )
        
        if use_language_folders:
            self.file_manager.organize_files_by_language(output_dir, languages)
        
        # If downloading all languages, get available languages
        if download_all and videos:
            first_video = videos[0]["id"]
            available_transcripts = self.youtube_api.get_available_languages_with_quality(first_video)
            if available_transcripts:
                languages = [t["language_code"] for t in available_transcripts]
                use_language_folders = True
                self.file_manager.organize_files_by_language(output_dir, languages)
        
        successful = 0
        failed = 0
        skipped = 0
        
        # Create task list
        remaining_tasks = []
        for video in videos:
            for lang in languages:
                remaining_tasks.append((video, lang))
        
        # Process tasks
        total_tasks = len(remaining_tasks)
        progress_bar = tqdm(
            total=total_tasks,
            desc=f"{Fore.LIGHTBLACK_EX}Overall progress{Style.RESET_ALL}",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            colour="cyan",
        )
        
        while remaining_tasks:
            batch_size = min(len(remaining_tasks), self.config.transcripts.batch_size)
            current_batch = remaining_tasks[:batch_size]

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.rate_limiting.max_workers
            ) as executor:
                future_to_task = {}
                for video, lang in current_batch:
                    future = executor.submit(
                        self._download_single_transcript,
                        video, lang, output_dir, use_language_folders
                    )
                    future_to_task[future] = (video, lang)
                
                completed_tasks = []
                for future in concurrent.futures.as_completed(future_to_task):
                    video, lang = future_to_task[future]
                    completed_tasks.append((video, lang))
                    
                    try:
                        result = future.result()
                        if result["success"]:
                            if result.get("skipped", False):
                                skipped += 1
                            else:
                                successful += 1
                                # Archive functionality: add to archive if enabled and successful
                                if self.config.transcripts.enable_archive:
                                    archive_path = self.file_manager.get_archive_path(output_dir)
                                    self.archive_manager.add_processed_video(archive_path, video["id"])
                        else:
                            failed += 1
                    except Exception:
                        failed += 1
                    
                    progress_bar.update(1)
                    progress_bar.set_postfix({
                        "✓": successful, "↺": skipped, "✗": failed
                    })
            
            # Remove completed tasks
            for task in completed_tasks:
                if task in remaining_tasks:
                    remaining_tasks.remove(task)
        
        progress_bar.close()
        
        # Print summary
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}DOWNLOAD SUMMARY FOR: {channel_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Downloaded: {successful}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}↺ Skipped (already exist): {skipped}{Style.RESET_ALL}")
        print(f"{Fore.RED}✗ Failed: {failed}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")
        
        return successful, skipped, failed
    
    def _download_single_transcript(self, video: Dict, language: str, 
                                   output_dir: str, use_language_folders: bool) -> Dict:
        """Download a single transcript with retry logic"""
        video_id = video["id"]
        
        for attempt in range(self.config.rate_limiting.max_retries):
            # Apply rate limiting
            self.rate_limiter.apply_delay()

            # Download transcript
            result = self.youtube_api.download_transcript(video_id, language)

            if result["success"]:
                # Save to file
                save_result = self.file_manager.save_transcript(
                    result["transcript"], video, language, output_dir, use_language_folders
                )

                if save_result["saved_files"]:
                    title_display = video["title"][:40] + "..." if len(video["title"]) > 40 else video["title"]
                    print(f"[{Fore.GREEN}OK{Style.RESET_ALL}  ] {title_display} ({language})")
                    return {"success": True, "skipped": False}
                else:
                    return {"success": True, "skipped": True}
            elif not result.get("retry", False):
                # Non-retryable error
                title_display = video["title"][:40] + "..." if len(video["title"]) > 40 else video["title"]
                print(f"[{Fore.YELLOW}MISS{Style.RESET_ALL}] {title_display} ({language}) - {result['error']}")
                return {"success": False, "skipped": False}
            else:
                # Retryable error
                if attempt < self.config.rate_limiting.max_retries - 1:
                    sleep_time = self.config.rate_limiting.base_delay * (self.config.rate_limiting.retry_backoff_factor ** attempt)
                    time.sleep(sleep_time)
                else:
                    title_display = video["title"][:40] + "..." if len(video["title"]) > 40 else video["title"]
                    print(f"[{Fore.RED}FAIL{Style.RESET_ALL}] {title_display} ({language}) - {result['error']}")
                    return {"success": False, "skipped": False}

        return {"success": False, "skipped": False}


class ConfigManager:
    """Helper class for configuration management"""
    
    @staticmethod
    def create_default_config(config_path: str = "config.toml"):
        """Create a default configuration file with new structure"""
        try:
            with open(config_path, 'w') as f:
                toml.dump({
                    "yt_dlp": {
                        "options": {
                            "output": "%(title)s [%(id)s].%(ext)s",
                            "skip_download": True,
                            "max_downloads": 0,
                            "playlist_items": "",
                            "concurrent_fragments": 1,
                            "sleep_interval": 0.0,
                            "max_sleep_interval": 20,
                            "retry_sleep": "",
                            "format": "",
                            "format_sort": "",
                            "restrict_filenames": False,
                            "no_warnings": False,
                            "verbose": False,
                            "quiet": False
                        }
                    },
                    "transcripts": {
                        "download_formats": ["txt", "json"],
                        "use_language_folders": True,
                        "sanitize_filenames": True,
                        "default_language": "en",
                        "auto_detect_language": True,
                        "language_priority": ["en"],
                        "concurrent_workers": 1,
                        "batch_size": 100,
                        "max_videos_per_channel": 0,
                        "organize_existing": True,
                        "timestamp_prefix_format": "",
                        "overwrite_existing": False,
                        "advanced_filename_sanitize": False
                    },
                    "rate_limiting": {
                        "base_delay": 1.5,
                        "max_workers": 1,
                        "max_retries": 3,
                        "retry_backoff_factor": 2.0,
                        "jitter_percentage": 0.2,
                        "ban_recovery_time": [300, 420],
                        "rate_strategy": "balanced",
                        "strategy_multipliers": {
                            "conservative": 3.0,
                            "balanced": 1.0,
                            "aggressive": 0.5
                        }
                    },
                    "api_settings": {
                        "api_timeout": 600,
                        "enable_cache": True,
                        "cache_dir": "./cache",
                        "cache_expiry_hours": 24
                    },
                    "ui": {
                        "show_progress": True,
                        "clear_screen": True,
                        "show_errors": True,
                        "color_scheme": "default"
                    },
                    "logging": {
                        "level": "INFO",
                        "file": "",
                        "log_ytdlp_commands": True,
                        "command_log_file": "ytdlp_commands.log"
                    },
                    "performance": {
                        "memory_usage": "medium",
                        "network_speed": "medium",
                        "cpu_cores": 0
                    }
                }, f)
            print(f"Created default configuration file: {config_path}")
        except Exception as e:
            print(f"Error creating config file: {e}")
    
    @staticmethod
    def show_current_config(config: DownloadConfig):
        """Display current configuration"""
        print("\n" + "="*60)
        print("CURRENT CONFIGURATION")
        print("="*60)

        print(f"\n{Fore.YELLOW}yt-dlp Options:{Style.RESET_ALL}")
        print(f"  Output template: {config.yt_dlp.output}")
        print(f"  Skip download: {config.yt_dlp.skip_download}")
        if config.yt_dlp.format:
            print(f"  Format: {config.yt_dlp.format}")
        if config.yt_dlp.sleep_interval > 0:
            print(f"  Sleep interval: {config.yt_dlp.sleep_interval}s")

        print(f"\n{Fore.YELLOW}Transcript Options:{Style.RESET_ALL}")
        print(f"  Formats: {', '.join(config.transcripts.download_formats)}")
        print(f"  Default language: {config.transcripts.default_language}")
        print(f"  Auto-detect language: {config.transcripts.auto_detect_language}")
        print(f"  Concurrent workers: {config.transcripts.concurrent_workers}")
        print(f"  Batch size: {config.transcripts.batch_size}")
        print(f"  Use language folders: {config.transcripts.use_language_folders}")
        print(f"  Organize existing: {config.transcripts.organize_existing}")

        print(f"\n{Fore.YELLOW}Rate Limiting:{Style.RESET_ALL}")
        print(f"  Base delay: {config.rate_limiting.base_delay}s")
        print(f"  Max workers: {config.rate_limiting.max_workers}")
        print(f"  Strategy: {config.rate_limiting.rate_strategy}")

        print(f"\n{Fore.YELLOW}API Settings:{Style.RESET_ALL}")
        print(f"  API timeout: {config.api_settings.api_timeout}s")
        print(f"  Cache enabled: {config.api_settings.enable_cache}")
        if config.api_settings.enable_cache:
            print(f"  Cache directory: {config.api_settings.cache_dir}")

        print(f"\n{Fore.YELLOW}Logging:{Style.RESET_ALL}")
        print(f"  Level: {config.logging.level}")
        print(f"  Log file: {config.logging.file or '(console)'}")
        print(f"  Log yt-dlp commands: {config.logging.log_ytdlp_commands}")
        if config.logging.log_ytdlp_commands:
            print(f"  Command log file: {config.logging.command_log_file}")

        print("="*60)


def load_config_with_overrides(config_path: str = "config.toml") -> DownloadConfig:
    """Load config with priority: CLI args > env vars > config.toml > defaults"""
    config = DownloadConfig()

    # Load from config.toml
    config.load_from_toml(config_path)

    # Override with environment variables
    env_overrides = {
        # yt-dlp options
        'YTD_OUTPUT': ('yt_dlp.output', str),
        'YTD_SKIP_DOWNLOAD': ('yt_dlp.skip_download', lambda x: x.lower() == 'true'),
        'YTD_SLEEP_INTERVAL': ('yt_dlp.sleep_interval', float),

        # Transcript options
        'YTD_CONCURRENT_WORKERS': ('transcripts.concurrent_workers', int),
        'YTD_BATCH_SIZE': ('transcripts.batch_size', int),
        'YTD_DEFAULT_LANGUAGE': ('transcripts.default_language', str),

        # Rate limiting
        'YTD_BASE_DELAY': ('rate_limiting.base_delay', float),
        'YTD_MAX_WORKERS': ('rate_limiting.max_workers', int),
        'YTD_RATE_STRATEGY': ('rate_limiting.rate_strategy', str),

        # Logging
        'YTD_LOG_LEVEL': ('logging.level', str),
        'YTD_LOG_FILE': ('logging.file', str),
        'YTD_LOG_YTDLP_COMMANDS': ('logging.log_ytdlp_commands', lambda x: x.lower() == 'true'),
    }

    for env_var, (config_path, type_func) in env_overrides.items():
        if env_var in os.environ:
            try:
                value = type_func(os.environ[env_var])
                # Navigate to nested attribute
                parts = config_path.split('.')
                obj = config
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
                logging.info(f"Overridden {config_path} from environment: {value}")
            except (ValueError, TypeError, AttributeError) as e:
                logging.warning(f"Invalid {env_var} value: {e}")

    # Re-apply rate limiting strategy after env var overrides
    config.rate_limiting.apply_strategy()

    return config


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="YouTube Channel Transcript Downloader v2.0 - yt-dlp + transcript orchestration",
        add_help=False
    )

    # Application flags
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")
    parser.add_argument("--create-config", action="store_true", help="Create default config.toml file")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")

    # yt-dlp flags (passthrough)
    parser.add_argument("--output-template", help="Override yt-dlp output template")
    parser.add_argument("--skip-download", action="store_true", help="Skip video download (transcripts only)")
    parser.add_argument("--format", help="Video format selector for yt-dlp")
    parser.add_argument("--format-sort", help="Format sort order for yt-dlp")
    parser.add_argument("--sleep-interval", type=float, help="Seconds to sleep between requests (yt-dlp)")
    parser.add_argument("--verbose", action="store_true", help="Verbose yt-dlp output")
    parser.add_argument("--quiet", action="store_true", help="Quiet yt-dlp output")

    # Transcript-specific flags
    parser.add_argument("--transcript-format", choices=["txt", "json", "srt", "vtt"],
                       help="Transcript format to download")
    parser.add_argument("--concurrent-workers", type=int,
                       help="Number of concurrent transcript downloads")
    parser.add_argument("--batch-size", type=int,
                       help="Number of videos to process per batch")
    parser.add_argument("--default-language", help="Default transcript language code")
    parser.add_argument("--overwrite-existing", action="store_true",
                       help="Overwrite existing transcript files")
    parser.add_argument("--no-organize", action="store_true",
                       help="Disable file organization")
    parser.add_argument("--advanced-filename-sanitize", action="store_true",
                       help="Use WordPress-style advanced filename sanitization")

    # Standard flags
    parser.add_argument("-t", "--transcript", dest="languages", action="append",
                       help="Transcript language code (can be repeated)")
    parser.add_argument("-all", action="store_true", help="Download all available languages")
    parser.add_argument("-txt", action="store_true", help="Download only TXT format")
    parser.add_argument("-json", action="store_true", help="Download only JSON format")

    # Parse known args first
    args, remaining = parser.parse_known_args()

    if args.help or len(sys.argv) <= 1:
        return args

    # Parse URLs from remaining args
    args.urls = []

    for arg in remaining:
        if arg.startswith(("http://", "https://", "www.")):
            args.urls.append(arg)

    return args


def get_system_language() -> str:
    """Get the user's system language"""
    try:
        locale.setlocale(locale.LC_ALL, "")
        lang_code = None
        
        try:
            loc = locale.getlocale(locale.LC_MESSAGES)
            if loc and loc[0]:
                lang_code = loc[0].split("_")[0].lower()
        except (AttributeError, ValueError):
            pass

        if not lang_code:
            try:
                encoding = locale.getencoding()
                if encoding and encoding.startswith(
                    ("en", "es", "fr", "de", "it", "ja", "ko", "ru", "zh")
                ):
                    lang_code = encoding[:2]
            except (AttributeError, ValueError):
                pass

        if lang_code:
            logging.info(f"Detected system language: {Fore.CYAN}{lang_code}{Style.RESET_ALL}")
            return lang_code
    except Exception as e:
        logging.warning(f"Could not detect system language: {e}")

    logging.info(f"Defaulting to {Fore.CYAN}English (en){Style.RESET_ALL}")
    return "en"


def sanitize_folder_name(name: str) -> str:
    """Sanitize folder name for filesystem use"""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Truncate to reasonable length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    # Ensure not empty
    if not sanitized:
        sanitized = "Untitled"
    return sanitized


def sanitize_filename(filename: str, advanced_mode: bool = False) -> str:
    """Sanitize filename for filesystem use

    Args:
        filename: Original filename
        advanced_mode: Use WordPress-style advanced sanitization if True

    Returns:
        Sanitized filename safe for filesystem use
    """
    if not advanced_mode:
        # Basic mode: only replace filesystem-dangerous characters
        return re.sub(r'[\\/*?:"<>|]', '_', filename)

    # Advanced mode: WordPress-style sanitization
    filename_raw = filename

    # Remove accents (simplified version - no external unicodedata needed)
    # Basic accent removal for common characters
    accents = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ý': 'y', 'ÿ': 'y',
        'ñ': 'n', 'ç': 'c'
    }
    for accented, plain in accents.items():
        filename = filename.replace(accented, plain)
        filename = filename.replace(accented.upper(), plain.upper())

    # Special characters to remove (WordPress style)
    special_chars = ['?', '[', ']', '/', '\\', '=', '<', '>', ':', ';', ',',
                     "'", '"', '&', '$', '#', '*', '(', ')', '|', '~', '`', '!',
                     '{', '}', '%', '+', '’', '«', '»', '”', '“', chr(0)]

    filename = ''.join(c for c in filename if c not in special_chars)

    # Replace spaces and other chars with dashes
    filename = re.sub(r'[\s\t\r\n]+', '-', filename)
    filename = re.sub(r'[-]+', '-', filename)  # Multiple dashes to single

    # Remove multiple dots
    filename = re.sub(r'\.{2,}', '.', filename)

    # Trim dangerous characters from start/end
    filename = filename.strip('.-_')

    # Handle files without extension
    if '.' not in filename and filename:
        # For files without extension, add a default if it looks like a known type
        # This is simplified - WordPress checks MIME types
        filename = f"{filename}.txt" if not filename.endswith('.txt') else filename

    # Ensure not empty
    if not filename:
        filename = "unnamed-file.txt"

    # Limit length
    if len(filename) > 200:
        name_part, ext_part = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext_part:
            max_name_len = 200 - len(ext_part) - 1  # -1 for dot
            filename = f"{name_part[:max_name_len]}.{ext_part}"
        else:
            filename = filename[:200]

    return filename


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()

    # Handle config commands
    if args.create_config:
        ConfigManager.create_default_config()
        return

    if args.show_config:
        config = load_config_with_overrides()
        ConfigManager.show_current_config(config)
        return

    # Load configuration with priority: CLI > env > config.toml > defaults
    config = load_config_with_overrides()

    # Update config from CLI args (highest priority)
    config.update_from_args(args)

    # Clear screen if configured
    if config.ui.clear_screen:
        os.system("cls" if os.name == "nt" else "clear")

    # Initialize downloader
    downloader = YouTubeTranscriptDownloader(config)

    # Show help if requested
    if args.help or len(sys.argv) <= 1:
        downloader.progress_reporter.display_help()
        return

    # Get URLs from command line
    urls = []
    if hasattr(args, 'urls') and args.urls:
        urls.extend(args.urls)

    # Ensure we have URLs
    if not urls:
        logging.error("No channel URLs provided. Use -h for help.")
        sys.exit(1)

    # Get languages
    languages = []
    if hasattr(args, 'languages') and args.languages:
        # Explicit languages provided via command line - use them directly
        languages = args.languages
        logging.info(f"Using explicitly specified language(s): {Fore.CYAN}{', '.join(languages)}{Style.RESET_ALL}")
    elif not args.all:
        # No explicit languages and not downloading all - auto-detect system language
        if config.transcripts.auto_detect_language:
            detected_lang = get_system_language()
            languages = [detected_lang]
            logging.info(f"Auto-detected language: {Fore.CYAN}{detected_lang}{Style.RESET_ALL}")
        else:
            languages = [config.transcripts.default_language]

    # Get formats
    formats = config.transcripts.download_formats

    # Display session configuration
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}SESSION CONFIGURATION{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

    if args.all:
        logging.info(
            f"Processing {Fore.CYAN}{len(urls)}{Style.RESET_ALL} URLs with {Fore.GREEN}ALL available languages{Style.RESET_ALL}"
        )
    else:
        logging.info(
            f"Processing {Fore.CYAN}{len(urls)}{Style.RESET_ALL} URLs with languages: {Fore.CYAN}{', '.join(languages)}{Style.RESET_ALL}"
        )

    logging.info(
        f"Transcript formats: {Fore.CYAN}{', '.join(formats)}{Style.RESET_ALL}"
    )
    logging.info(
        f"Rate limiting: {Fore.YELLOW}{config.rate_limiting.base_delay}s{Style.RESET_ALL} delay, {Fore.YELLOW}{config.rate_limiting.max_workers}{Style.RESET_ALL} workers"
    )
    logging.info(
        f"yt-dlp output template: {Fore.CYAN}{config.yt_dlp.output}{Style.RESET_ALL}"
    )
    print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

    # Process channels
    try:
        results = downloader.process_channels(urls, languages, args.all, formats)
        downloader.progress_reporter.display_summary(results)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Download interrupted by user.{Style.RESET_ALL}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
