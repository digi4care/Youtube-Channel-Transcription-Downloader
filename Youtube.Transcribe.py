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
class DownloadConfig:
    """Configuration class containing all application settings"""
    
    # Rate limiting settings
    base_delay: float = 1.5
    max_workers: int = 3
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    jitter_percentage: float = 0.2
    ban_recovery_time: tuple = (300, 420)
    
    # File handling settings
    output_dir: str = "./downloads"
    use_language_folders: bool = True
    download_formats: List[str] = field(default_factory=lambda: ["txt", "json"])
    sanitize_filenames: bool = True
    
    # API settings
    api_timeout: int = 600
    batch_size: int = 100
    max_videos_per_channel: int = 0
    
    # UI settings
    show_progress: bool = True
    clear_screen: bool = True
    show_errors: bool = True
    color_scheme: str = "default"
    
    # Advanced settings
    enable_cache: bool = True
    cache_dir: str = "./cache"
    cache_expiry_hours: int = 24
    log_level: str = "INFO"
    log_file: str = ""
    
    # Rate limiting strategy
    rate_strategy: str = "balanced"
    strategy_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "conservative": 3.0,
        "balanced": 1.0,
        "aggressive": 0.5
    })
    
    # Performance settings
    memory_usage: str = "medium"
    network_speed: str = "medium"
    cpu_cores: int = 0
    
    @classmethod
    def from_toml(cls, config_path: str = "config.toml") -> 'DownloadConfig':
        """Load configuration from TOML file"""
        try:
            with open(config_path, 'r') as f:
                config_data = toml.load(f)
            
            # Flatten nested TOML structure for dataclass
            flattened = {}
            for section, values in config_data.items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        # Skip the multipliers section - handle it separately
                        if section == 'rate_limiting_strategies' and key == 'multipliers':
                            continue
                        flattened[key] = value
                else:
                    flattened[section] = values
            
            # Handle special nested structures
            if 'rate_limiting_strategies' in config_data:
                strategies = config_data['rate_limiting_strategies']
                if 'strategy' in strategies:
                    flattened['rate_strategy'] = strategies['strategy']
                if 'multipliers' in strategies:
                    flattened['strategy_multipliers'] = strategies['multipliers']
            
            # Remove the conflicting 'strategy' key if it exists
            if 'strategy' in flattened:
                del flattened['strategy']
            
            return cls(**flattened)
        except FileNotFoundError:
            logging.warning(f"Config file {config_path} not found, using defaults")
            return cls()
        except Exception as e:
            logging.error(f"Error loading config: {e}, using defaults")
            return cls()
    
    def apply_rate_strategy(self):
        """Apply the selected rate limiting strategy"""
        multiplier = self.strategy_multipliers.get(self.rate_strategy, 1.0)
        self.base_delay *= multiplier
        self.max_workers = max(1, int(self.max_workers / multiplier))
    
    def update_from_args(self, args: argparse.Namespace):
        """Update configuration from command line arguments"""
        if hasattr(args, 'delay') and args.delay:
            self.base_delay = args.delay
        if hasattr(args, 'workers') and args.workers:
            self.max_workers = args.workers
        if hasattr(args, 'txt') and args.txt:
            self.download_formats = ["txt"]
        if hasattr(args, 'json') and args.json:
            self.download_formats = ["json"]


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
    
    def get_channel_name(self, channel_url: str) -> str:
        """Get channel name using yt-dlp"""
        logging.info("Retrieving channel name...")
        
        spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner_idx = 0
        process = None

        try:
            command = [
                "yt-dlp",
                "--skip-download",
                "--print",
                "%(channel)s",
                "--playlist-items",
                "1",
                channel_url,
            ]

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
            command = [
                "yt-dlp",
                "--flat-playlist",
                "--print",
                "%(id)s %(title)s",
                channel_url,
            ]

            logging.debug(f"Running command: {' '.join(command)}")

            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.active_processes.append(process)

            stdout, stderr = process.communicate(timeout=self.config.api_timeout)
            self.active_processes.remove(process)

            if not stdout.strip():
                logging.error("No video data returned. Check the channel URL.")
                return []

            videos_data = []
            lines = stdout.strip().split("\n")

            if self.config.max_videos_per_channel > 0:
                lines = lines[:self.config.max_videos_per_channel]

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
    
    def get_available_languages(self, video_id: str) -> List[str]:
        """Get available transcript languages for a video"""
        try:
            with tqdm(
                total=1,
                desc=f"{Fore.CYAN}Checking available languages{Style.RESET_ALL}",
                bar_format="{desc}: {bar}| {elapsed}",
                colour="cyan",
            ) as pbar:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                languages = []

                for transcript in transcript_list:
                    lang_code = transcript.language_code
                    languages.append(lang_code)

                pbar.update(1)
            return languages
        except Exception as e:
            logging.error(f"Error getting available languages for video {video_id}: {e}")
            return []
    
    def download_transcript(self, video_id: str, language: str) -> Dict:
        """Download a single transcript"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            return {
                "success": True,
                "transcript": transcript,
                "language": language
            }
        except _errors.NoTranscriptFound:
            return {
                "success": False,
                "error": "No transcript available",
                "retry": False
            }
        except _errors.TranscriptsDisabled:
            return {
                "success": False,
                "error": "Transcripts disabled for this video",
                "retry": False
            }
        except _errors.VideoUnavailable:
            return {
                "success": False,
                "error": "Video unavailable",
                "retry": False
            }
        except _errors.RequestBlocked:
            return {
                "success": False,
                "error": "Request blocked - possible rate limit",
                "retry": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "retry": True
            }
    
    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid characters from filenames"""
        if self.config.sanitize_filenames:
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
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_info["title"])
        
        # Determine file paths
        if use_language_folders:
            base_dir = os.path.join(output_dir, language)
        else:
            base_dir = output_dir
        
        os.makedirs(base_dir, exist_ok=True)
        
        # Save TXT format
        if "txt" in self.config.download_formats:
            txt_path = os.path.join(base_dir, f"{safe_title}_{language}.txt")
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
        if "json" in self.config.download_formats:
            if use_language_folders:
                json_base_dir = os.path.join(base_dir, "json")
            else:
                json_base_dir = os.path.join(output_dir, "json")
            
            os.makedirs(json_base_dir, exist_ok=True)
            json_path = os.path.join(json_base_dir, f"{safe_title}_{language}.json")
            
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
        jitter = self.config.base_delay * self.config.jitter_percentage * (random.random() * 2 - 1)
        sleep_time = self.config.base_delay + jitter
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
        if self.config.show_progress:
            self.display_logo()
        
        print(f"{Fore.CYAN}=" * 80)
        print(f"{Fore.YELLOW}USAGE INSTRUCTIONS")
        print(f"{Fore.CYAN}=" * 80)
        print("\nThis script downloads transcripts for videos on YouTube channels or individual videos.")
        print("It creates a separate folder for each channel and organizes files into subdirectories.")
        print(f"{Fore.YELLOW}Downloads are processed with rate limiting to avoid YouTube IP bans.")
        print("Files that already exist will be skipped, allowing you to resume or update channels.")

        print(f"\n{Fore.GREEN}USAGE:")
        print("  python Youtube.Transcribe.v2.py [options] <channel_or_video_url(s)>")

        print(f"\n{Fore.GREEN}CONFIGURATION:")
        print("  --create-config     Create default config.toml file")
        print("  --show-config       Show current configuration")
        print("  Edit config.toml to customize settings")

        print(f"\n{Fore.GREEN}EXAMPLES:")
        print(f"{Fore.CYAN}  # Download transcript for a single YouTube video")
        print("  python Youtube.Transcribe.v2.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -en")
        print(f"{Fore.CYAN}  # Download English transcripts from a channel")
        print("  python Youtube.Transcribe.v2.py https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw -en")
        print(f"{Fore.CYAN}  # Download multiple languages")
        print("  python Youtube.Transcribe.v2.py https://youtube.com/c/channel1 -en -es -fr")
        print(f"{Fore.CYAN}  # Download all available languages")
        print("  python Youtube.Transcribe.v2.py https://youtube.com/c/channel1 -all")

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
        self._setup_logging()
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter("%(message)s"))
        
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        logger.addHandler(handler)
        
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
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
    
    def download_transcripts_batch(self, videos: List[Dict], languages: List[str],
                                  channel_name: str, download_all: bool, 
                                  formats: List[str]) -> Tuple[int, int, int]:
        """Download transcripts in batches"""
        # Create output directory
        output_dir = os.path.join(self.config.output_dir, channel_name)
        os.makedirs(output_dir, exist_ok=True)
        
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
            available_langs = self.youtube_api.get_available_languages(first_video)
            if available_langs:
                languages = available_langs
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
            batch_size = min(len(remaining_tasks), self.config.batch_size)
            current_batch = remaining_tasks[:batch_size]
            
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_workers
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
        
        for attempt in range(self.config.max_retries):
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
                if attempt < self.config.max_retries - 1:
                    sleep_time = self.config.base_delay * (self.config.retry_backoff_factor ** attempt)
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
        """Create a default configuration file"""
        config = DownloadConfig()
        try:
            with open(config_path, 'w') as f:
                toml.dump({
                    "rate_limiting": {
                        "base_delay": config.base_delay,
                        "max_workers": config.max_workers,
                        "max_retries": config.max_retries,
                        "retry_backoff_factor": config.retry_backoff_factor,
                        "jitter_percentage": config.jitter_percentage,
                        "ban_recovery_time": list(config.ban_recovery_time)
                    },
                    "file_handling": {
                        "output_dir": config.output_dir,
                        "use_language_folders": config.use_language_folders,
                        "download_formats": config.download_formats,
                        "sanitize_filenames": config.sanitize_filenames
                    },
                    "api_settings": {
                        "api_timeout": config.api_timeout,
                        "batch_size": config.batch_size,
                        "max_videos_per_channel": config.max_videos_per_channel
                    },
                    "ui_settings": {
                        "show_progress": config.show_progress,
                        "clear_screen": config.clear_screen,
                        "show_errors": config.show_errors,
                        "color_scheme": config.color_scheme
                    },
                    "advanced": {
                        "enable_cache": config.enable_cache,
                        "cache_dir": config.cache_dir,
                        "cache_expiry_hours": config.cache_expiry_hours,
                        "log_level": config.log_level,
                        "log_file": config.log_file
                    },
                    "rate_limiting_strategies": {
                        "strategy": config.rate_strategy,
                        "multipliers": config.strategy_multipliers
                    },
                    "performance": {
                        "memory_usage": config.memory_usage,
                        "network_speed": config.network_speed,
                        "cpu_cores": config.cpu_cores
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
        print(f"Rate Limiting: {config.base_delay}s delay, {config.max_workers} workers")
        print(f"Strategy: {config.rate_strategy}")
        print(f"Output: {config.output_dir}")
        print(f"Formats: {', '.join(config.download_formats)}")
        print(f"Language folders: {config.use_language_folders}")
        print(f"Log level: {config.log_level}")
        print("="*60)


def load_config_with_overrides(config_path: str = "config.toml") -> DownloadConfig:
    """Load config from TOML, then override with environment variables"""
    config = DownloadConfig.from_toml(config_path)
    
    # Override with environment variables
    env_overrides = {
        'YTD_DELAY': ('base_delay', float),
        'YTD_WORKERS': ('max_workers', int),
        'YTD_OUTPUT_DIR': ('output_dir', str),
        'YTD_LOG_LEVEL': ('log_level', str),
        'YTD_RATE_STRATEGY': ('rate_strategy', str),
    }
    
    for env_var, (config_key, type_func) in env_overrides.items():
        if env_var in os.environ:
            try:
                value = type_func(os.environ[env_var])
                setattr(config, config_key, value)
                logging.info(f"Overridden {config_key} from environment: {value}")
            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid {env_var} value: {e}")
    
    return config


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="YouTube Channel Transcript Downloader v2.0", 
        add_help=False
    )
    parser.add_argument("-f", "--file", help="File containing channel URLs")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")
    parser.add_argument("--create-config", action="store_true", help="Create default config file")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    parser.add_argument("-all", action="store_true", help="Download all available languages")
    parser.add_argument("-txt", action="store_true", help="Download only TXT files")
    parser.add_argument("-json", action="store_true", help="Download only JSON files")
    parser.add_argument("-delay", type=float, help="Delay between API requests in seconds")
    parser.add_argument("-workers", type=int, help="Number of concurrent downloads")

    # Parse known args first
    args, remaining = parser.parse_known_args()

    if args.help or len(sys.argv) <= 1:
        return args

    # Parse URLs and languages from remaining args
    args.urls = []
    args.languages = []

    for arg in remaining:
        if arg.startswith("-"):
            if arg.startswith("-delay") or arg.startswith("-workers"):
                continue
            elif arg == "-all":
                args.all = True
            elif arg == "-txt":
                args.txt = True
            elif arg == "-json":
                args.json = True
            else:
                args.languages.append(arg[1:])
        elif arg.startswith(("http://", "https://", "www.")):
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
    
    # Load configuration
    config = load_config_with_overrides()
    
    # Update config from CLI args
    config.update_from_args(args)
    
    # Apply rate limiting strategy
    config.apply_rate_strategy()
    
    # Clear screen if configured
    if config.clear_screen:
        os.system("cls" if os.name == "nt" else "clear")
    
    # Initialize downloader
    downloader = YouTubeTranscriptDownloader(config)
    
    # Show help if requested
    if args.help or len(sys.argv) <= 1:
        downloader.progress_reporter.display_help()
        return
    
    # Parse URLs from file if specified
    urls = []
    if args.file:
        if not os.path.exists(args.file):
            logging.error(f"File not found: {args.file}")
            sys.exit(1)
        
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read().replace(",", "\n")
                file_urls = [url.strip() for url in content.split("\n") if url.strip()]
                urls.extend(file_urls)
        except Exception as e:
            logging.error(f"Error reading file {args.file}: {str(e)}")
            sys.exit(1)
    
    # Add URLs from command line
    if hasattr(args, 'urls') and args.urls:
        urls.extend(args.urls)
    
    # Ensure we have URLs
    if not urls:
        logging.error("No channel URLs provided. Use -h for help.")
        sys.exit(1)
    
    # Get languages
    languages = []
    if hasattr(args, 'languages') and args.languages:
        languages = args.languages
    elif not args.all:
        languages = [get_system_language()]
    
    # Get formats
    formats = config.download_formats
    if args.txt:
        formats = ["txt"]
    elif args.json:
        formats = ["json"]
    
    # Display session configuration
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}SESSION CONFIGURATION{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    
    if args.all:
        logging.info(
            f"Processing {Fore.CYAN}{len(urls)}{Style.RESET_ALL} channels with {Fore.GREEN}ALL available languages{Style.RESET_ALL}"
        )
    else:
        logging.info(
            f"Processing {Fore.CYAN}{len(urls)}{Style.RESET_ALL} channels with languages: {Fore.CYAN}{', '.join(languages)}{Style.RESET_ALL}"
        )
    
    logging.info(
        f"File types to download: {Fore.CYAN}{', '.join(formats)}{Style.RESET_ALL}"
    )
    logging.info(
        f"Rate limiting: {Fore.YELLOW}{config.base_delay}s{Style.RESET_ALL} delay, {Fore.YELLOW}{config.max_workers}{Style.RESET_ALL} workers"
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
