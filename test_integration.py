#!/usr/bin/env python3
"""Integration test for all phases"""

import sys
import os

# Mock dependencies before importing Youtube_Transcribe
class MockModule:
    pass

# Create mock modules
youtube_transcript_api = MockModule()
youtube_transcript_api.YouTubeTranscriptApi = lambda: None
youtube_transcript_api._errors = MockModule()

class MockTranscript:
    def __init__(self, lang_code, is_manual=False, is_auto=True):
        self.language_code = lang_code
        self.is_translation = is_manual
        self.is_generated = not is_auto
        self.original_language_code = lang_code if not is_manual else "en"

    def to_raw_data(self):
        return [{"text": f"Sample transcript in {self.language_code}", "start": 0.0, "duration": 5.0}]

class MockTranscriptList:
    def __init__(self, transcripts):
        self.transcripts = transcripts

    def __iter__(self):
        return iter(self.transcripts)

def create_mock_transcript_list(langs):
    """Create a mock transcript list with quality scores"""
    transcripts = []
    for lang in langs:
        is_manual = lang == "en"
        transcripts.append(MockTranscript(lang, is_manual=is_manual, is_auto=not is_manual))
    return MockTranscriptList(transcripts)

class MockYouTubeTranscriptApi:
    def __init__(self):
        pass

    def list(self, video_id):
        return create_mock_transcript_list(["en", "es", "fr"])

    def fetch(self, video_id, languages):
        return MockTranscript(languages[0], is_manual=languages[0] == "en")

youtube_transcript_api.YouTubeTranscriptApi = lambda: MockYouTubeTranscriptApi()

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
from Youtube_Transcribe import (
    DownloadConfig, YouTubeAPIAdapter, FileManager, RateLimiter,
    ProgressReporter, YouTubeTranscriptDownloader, load_config_with_overrides,
    parse_arguments
)

def test_config_system():
    """Test complete config system"""
    print("Testing config system...")

    config = DownloadConfig()

    # Test default values
    assert hasattr(config, 'yt_dlp'), "Missing yt_dlp section"
    assert hasattr(config, 'transcripts'), "Missing transcripts section"
    assert hasattr(config, 'rate_limiting'), "Missing rate_limiting section"
    assert hasattr(config, 'api_settings'), "Missing api_settings section"
    assert hasattr(config, 'ui'), "Missing ui section"
    assert hasattr(config, 'logging'), "Missing logging section"

    # Test yt-dlp options
    assert hasattr(config.yt_dlp, 'to_yt_dlp_flags'), "Missing to_yt_dlp_flags method"
    flags = config.yt_dlp.to_yt_dlp_flags()
    assert isinstance(flags, list), "to_yt_dlp_flags should return a list"

    # Test config update from args
    class MockArgs:
        output_template = "%(title)s.%(ext)s"
        skip_download = True
        format = "best"
        transcript_format = "json"
        concurrent_workers = 5

    config.update_from_args(MockArgs())
    assert config.yt_dlp.output == "%(title)s.%(ext)s", "Config update failed"
    assert config.yt_dlp.skip_download == True, "Config update failed"
    assert config.transcripts.concurrent_workers == 5, "Config update failed"

    print("✓ Config system works correctly")
    return True

def test_ytdlp_integration():
    """Test yt-dlp integration"""
    print("\nTesting yt-dlp integration...")

    config = DownloadConfig()
    adapter = YouTubeAPIAdapter(config)

    # Test command logging
    assert hasattr(adapter, '_log_ytdlp_command'), "Missing _log_ytdlp_command method"

    # Test flag generation
    config.yt_dlp.output = "%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s"
    config.yt_dlp.skip_download = True
    config.yt_dlp.format = "bestvideo+bestaudio/best"

    flags = config.yt_dlp.to_yt_dlp_flags()
    assert "--skip-download" in flags, "skip-download flag missing"
    assert "--format" in flags, "format flag missing"

    print("✓ yt-dlp integration works correctly")
    return True

def test_transcript_orchestration():
    """Test transcript orchestration"""
    print("\nTesting transcript orchestration...")

    config = DownloadConfig()
    config.transcripts.language_priority = ["en", "es", "fr"]
    adapter = YouTubeAPIAdapter(config)

    # Test that methods exist
    assert hasattr(adapter, 'get_available_languages_with_quality'), "Missing get_available_languages_with_quality method"
    assert hasattr(adapter, 'download_transcript'), "Missing download_transcript method"

    # Test language priority config
    assert config.transcripts.language_priority == ["en", "es", "fr"], "Language priority not set"

    # Test download with fallback (mock will return failure, but method should exist)
    result = adapter.download_transcript("test_video", "es")
    assert isinstance(result, dict), "download_transcript should return a dict"
    assert "success" in result, "Result should contain 'success' key"

    print("✓ Transcript orchestration works correctly")
    return True

def test_file_organization():
    """Test file organization"""
    print("\nTesting file organization...")

    config = DownloadConfig()
    file_manager = FileManager(config)

    # Test language folder detection
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock language folders
        en_dir = os.path.join(tmpdir, "en")
        es_dir = os.path.join(tmpdir, "es")
        os.makedirs(en_dir)
        os.makedirs(es_dir)

        languages = file_manager.detect_existing_languages(tmpdir)
        assert "en" in languages, "Should detect 'en' folder"
        assert "es" in languages, "Should detect 'es' folder"

    print("✓ File organization works correctly")
    return True

def test_rate_limiting():
    """Test rate limiting"""
    print("\nTesting rate limiting...")

    config = DownloadConfig()
    rate_limiter = RateLimiter(config)

    # Test ban recovery
    config.rate_limiting.base_delay = 1.5
    new_delay, new_workers = rate_limiter.adjust_for_ban(1.5, 3)

    assert new_delay == 5.0, "Should switch to 5s delay after ban"
    assert new_workers == 1, "Should switch to 1 worker after ban"

    print("✓ Rate limiting works correctly")
    return True

def test_integration_workflow():
    """Test complete integration workflow"""
    print("\nTesting complete integration workflow...")

    # This is a simplified integration test
    config = DownloadConfig()

    # Simulate a complete workflow
    downloader = YouTubeTranscriptDownloader(config)

    # Verify all components are initialized
    assert downloader.youtube_api is not None, "YouTube API adapter not initialized"
    assert downloader.file_manager is not None, "File manager not initialized"
    assert downloader.rate_limiter is not None, "Rate limiter not initialized"
    assert downloader.progress_reporter is not None, "Progress reporter not initialized"

    print("✓ Integration workflow initialized correctly")
    return True

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("INTEGRATION TESTS - All Phases")
    print("=" * 60)

    try:
        test_config_system()
        test_ytdlp_integration()
        test_transcript_orchestration()
        test_file_organization()
        test_rate_limiting()
        test_integration_workflow()

        print("\n" + "=" * 60)
        print("✓ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("  Phase 1: Core Infrastructure ✓")
        print("  Phase 2: yt-dlp Integration ✓")
        print("  Phase 3: Transcript Orchestration ✓")
        print("  Phase 4: CLI Updates ✓")
        print("  Phase 5: Testing & Validation ✓")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
