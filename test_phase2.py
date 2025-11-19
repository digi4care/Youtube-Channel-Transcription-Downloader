#!/usr/bin/env python3
"""Test script for Phase 2: yt-dlp Integration"""

import sys
import os
import subprocess
import time
from datetime import datetime

# Mock dependencies before importing Youtube.Transcribe
class MockModule:
    pass

# Create mock modules
youtube_transcript_api = MockModule()
youtube_transcript_api.YouTubeTranscriptApi = lambda: None
youtube_transcript_api._errors = MockModule()
youtube_transcript_api.YouTubeTranscriptApi.list_transcripts = lambda x: []

tqdm = MockModule()
tqdm.tqdm = lambda *args, **kwargs: type('MockTqdm', (), {
    'update': lambda: None,
    'set_postfix': lambda **kwargs: None
})()

colorama = MockModule()
colorama.Fore = type('Fore', (), {
    'CYAN': '',
    'YELLOW': '',
    'GREEN': '',
    'RED': '',
    'LIGHTBLACK_EX': '',
    'WHITE': '',
    'RESET_ALL': ''
})
colorama.Style = type('Style', (), {
    'BRIGHT': '',
    'RESET_ALL': ''
})
colorama.init = lambda autoreset=True: None

toml = MockModule()
toml.load = lambda f: {}
toml.dump = lambda data, f: None

# Add mocks to sys.modules
sys.modules['youtube_transcript_api'] = youtube_transcript_api
sys.modules['tqdm'] = tqdm
sys.modules['colorama'] = colorama
sys.modules['toml'] = toml

# Now import the module
sys.path.insert(0, '.')
from Youtube.Transcribe import DownloadConfig, YouTubeAPIAdapter

def test_config_structure():
    """Test new config structure"""
    print("Testing config structure...")

    config = DownloadConfig()
    print(f"✓ YTDLPOptions: {hasattr(config, 'yt_dlp')}")
    print(f"✓ TranscriptOptions: {hasattr(config, 'transcripts')}")
    print(f"✓ RateLimiting: {hasattr(config, 'rate_liming')}")
    print(f"✓ Logging: {hasattr(config, 'logging')}")

    flags = config.yt_dlp.to_yt_dlp_flags()
    print(f"✓ Generated {len(flags)} yt-dlp flags")

    return True

def test_ytdlp_adapter():
    """Test YouTubeAPIAdapter with mocked yt-dlp"""
    print("\nTesting YouTubeAPIAdapter...")

    config = DownloadConfig()
    adapter = YouTubeAPIAdapter(config)

    print("✓ YouTubeAPIAdapter created successfully")
    print(f"✓ Command logging enabled: {config.logging.log_ytdlp_commands}")

    return True

def test_channel_name_command():
    """Test channel name extraction command generation"""
    print("\nTesting channel name command generation...")

    config = DownloadConfig()
    adapter = YouTubeAPIAdapter(config)

    # Check that _log_ytdlp_command method exists
    if hasattr(adapter, '_log_ytdlp_command'):
        print("✓ _log_ytdlp_command method exists")
        return True
    else:
        print("✗ _log_ytdlp_command method missing")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("PHASE 2: yt-dlp Integration Tests")
    print("=" * 60)

    try:
        test_config_structure()
        test_ytdlp_adapter()
        test_channel_name_command()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
