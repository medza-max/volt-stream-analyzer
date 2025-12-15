"""
Test script for playlist analyzer with link checking
"""

import asyncio
from playlist_analyzer import PlaylistAnalyzer, analyze_playlist_sync

# Sample M3U with mix of working and broken links
SAMPLE_M3U_WITH_REAL_URLS = """#EXTM3U
#EXTINF:-1 tvg-name="Working Test Stream 1" group-title="Test",Working Test Stream 1
https://www.w3schools.com/html/mov_bbb.mp4
#EXTINF:-1 tvg-name="Working Test Stream 2" group-title="Test",Working Test Stream 2
https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4
#EXTINF:-1 tvg-name="Dead Link 1" group-title="Test",Dead Link 1
http://dead-link-example-12345.com/stream.m3u8
#EXTINF:-1 tvg-name="Dead Link 2" group-title="Test",Dead Link 2
http://another-dead-link-99999.com/live/stream.ts
#EXTINF:-1 tvg-name="Timeout Link" group-title="Test",Timeout Link
http://192.168.999.999:8080/stream.m3u8
"""

def print_separator(char="=", length=70):
    """Print a separator line"""
    print(char * length)

def print_health_bar(percentage, width=30):
    """Print a visual health bar"""
    filled = int((percentage / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    
    # Color coding
    if percentage >= 80:
        status = "🟢 EXCELLENT"
    elif percentage >= 60:
        status = "🟡 GOOD"
    elif percentage >= 40:
        status = "🟠 FAIR"
    else:
        status = "🔴 POOR"
    
    return f"{bar} {percentage}% {status}"

def test_with_link_checking():
    """Test playlist analyzer with link checking"""
    print("\n🚀 IPTV Playlist Analyzer - Link Checking Test")
    print_separator()
    
    # Create test file
    test_file = '/home/claude/iptv-analyzer/test_playlist.m3u'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(SAMPLE_M3U_WITH_REAL_URLS)
    
    print("\n✅ Created test playlist with mixed working/dead links")
    print("⏳ Starting analysis with link checking...\n")
    
    # Analyze with link checking
    report = analyze_playlist_sync(test_file, check_links=True)
    
    # Display results
    print_separator()
    print("📊 PLAYLIST HEALTH REPORT")
    print_separator()
    
    summary = report['summary']
    
    print(f"\n📺 CHANNELS:")
    print(f"   Total: {summary['total_channels']}")
    print(f"   ✅ Working: {summary['working_channels']}")
    print(f"   ❌ Dead: {summary['dead_channels']}")
    
    print(f"\n💚 HEALTH STATUS:")
    print(f"   {print_health_bar(summary['health_percentage'])}")
    
    print(f"\n📁 CATEGORIES:")
    for category, count in report['categories'].items():
        print(f"   • {category}: {count} channels")
    
    # Show dead channels if any
    if 'dead_channels_list' in report and report['dead_channels_list']:
        print(f"\n❌ DEAD CHANNELS DETECTED:")
        for i, dead_ch in enumerate(report['dead_channels_list'], 1):
            print(f"   {i}. {dead_ch['name']}")
            print(f"      URL: {dead_ch['url']}")
            print(f"      Error: {dead_ch.get('error', 'No response')}")
            print()
    
    print_separator()
    print("✅ Analysis complete!")
    print_separator()
    
    return report

def test_without_link_checking():
    """Test analyzer without link checking (fast mode)"""
    print("\n\n🏃 Quick Analysis (No Link Checking)")
    print_separator()
    
    test_file = '/home/claude/iptv-analyzer/test_playlist.m3u'
    
    print("\n⚡ Running fast analysis...")
    report = analyze_playlist_sync(test_file, check_links=False)
    
    print(f"\n✅ Fast analysis complete!")
    print(f"   Total Channels: {report['summary']['total_channels']}")
    print(f"   Total Categories: {report['summary']['total_categories']}")
    print(f"\n💡 Link checking was skipped for speed")
    
    return report

def test_performance():
    """Test with larger playlist to show performance"""
    print("\n\n⚡ Performance Test")
    print_separator()
    
    # Create a larger test playlist (50 channels)
    large_m3u = "#EXTM3U\n"
    for i in range(50):
        if i % 5 == 0:  # Every 5th link is dead
            url = f"http://dead-link-{i}.com/stream.m3u8"
        else:
            url = f"https://www.w3schools.com/html/mov_bbb.mp4?id={i}"
        
        large_m3u += f'#EXTINF:-1 tvg-name="Channel {i}" group-title="Test",Channel {i}\n'
        large_m3u += f'{url}\n'
    
    test_file = '/home/claude/iptv-analyzer/large_test.m3u'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(large_m3u)
    
    print(f"\n📺 Created large playlist with 50 channels")
    print(f"⏳ Checking all links concurrently...")
    
    import time
    start = time.time()
    
    report = analyze_playlist_sync(test_file, check_links=True)
    
    duration = time.time() - start
    
    print(f"\n✅ Checked 50 channels in {duration:.2f} seconds")
    print(f"   Average: {duration/50:.3f}s per channel")
    print(f"   Working: {report['summary']['working_channels']}")
    print(f"   Dead: {report['summary']['dead_channels']}")
    print(f"   Health: {report['summary']['health_percentage']}%")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  IPTV PLAYLIST ANALYZER - STEP 2: LINK CHECKING")
    print("=" * 70)
    
    # Test 1: With link checking
    report1 = test_with_link_checking()
    
    # Test 2: Without link checking (fast mode)
    report2 = test_without_link_checking()
    
    # Test 3: Performance test
    # Uncomment to test with 50 channels:
    # test_performance()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 70)
    print("\n💡 Key Features:")
    print("   ✓ Detects dead/working channels")
    print("   ✓ Async concurrent checking (fast)")
    print("   ✓ Health percentage calculation")
    print("   ✓ Detailed error reporting")
    print("\n🎯 Next Step: Add duplicate detection & quality analysis")
    print("=" * 70)
