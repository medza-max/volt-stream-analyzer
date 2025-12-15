"""
IPTV Playlist Analyzer - Step 2: Link Checking Added
Now detects dead/working channels with async HTTP checks
"""

import re
import asyncio
import aiohttp
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from datetime import datetime

class PlaylistAnalyzer:
    """
    Analyzes M3U/M3U8 playlists and provides health reports
    """
    
    def __init__(self):
        self.channels = []
        self.total_channels = 0
        self.working_channels = 0
        self.dead_channels = 0
        self.checked_channels = []
        
    async def check_link(self, url: str, timeout: int = 5) -> Dict:
        """
        Check if a stream URL is working
        
        Args:
            url: Stream URL to check
            timeout: Request timeout in seconds
            
        Returns:
            Dict with status and response time
        """
        try:
            async with aiohttp.ClientSession() as session:
                start_time = datetime.now()
                async with session.head(url, timeout=timeout, allow_redirects=True) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    is_working = response.status in [200, 301, 302, 403]  # 403 sometimes means it's live but needs auth
                    
                    return {
                        'url': url,
                        'working': is_working,
                        'status_code': response.status,
                        'response_time': round(response_time, 2)
                    }
        except asyncio.TimeoutError:
            return {
                'url': url,
                'working': False,
                'status_code': 0,
                'error': 'Timeout',
                'response_time': timeout
            }
        except Exception as e:
            return {
                'url': url,
                'working': False,
                'status_code': 0,
                'error': str(e)[:50],  # Truncate long errors
                'response_time': 0
            }
    
    async def check_all_links(self, max_concurrent: int = 20) -> List[Dict]:
        """
        Check all channel links concurrently
        
        Args:
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List of check results
        """
        print(f"\n🔍 Checking {len(self.channels)} links...")
        print(f"⏳ This may take a moment...\n")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_with_limit(channel):
            async with semaphore:
                result = await self.check_link(channel['url'])
                # Merge result with channel info
                return {**channel, **result}
        
        # Check all links concurrently
        tasks = [check_with_limit(channel) for channel in self.channels]
        self.checked_channels = await asyncio.gather(*tasks)
        
        # Count working/dead
        self.working_channels = sum(1 for ch in self.checked_channels if ch.get('working', False))
        self.dead_channels = len(self.checked_channels) - self.working_channels
        
        return self.checked_channels
        
    def parse_m3u(self, file_path: str = None, content: str = None) -> Dict:
        """
        Parse M3U file or content
        
        Args:
            file_path: Path to M3U file
            content: M3U content as string
            
        Returns:
            Dictionary with parsed data
        """
        if file_path:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        if not content:
            return {"error": "No content provided"}
        
        # Parse the M3U content
        lines = content.strip().split('\n')
        
        current_channel = {}
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and M3U header
            if not line or line == '#EXTM3U':
                continue
            
            # Parse channel info line
            if line.startswith('#EXTINF:'):
                # Extract channel name and attributes
                # Format: #EXTINF:-1 tvg-id="..." tvg-name="..." group-title="...",Channel Name
                
                # Get everything after #EXTINF:
                info = line[8:]
                
                # Split by comma to separate attributes from name
                parts = info.split(',', 1)
                
                if len(parts) == 2:
                    attributes = parts[0]
                    channel_name = parts[1].strip()
                    
                    # Extract group-title (category)
                    group_match = re.search(r'group-title="([^"]*)"', attributes)
                    group = group_match.group(1) if group_match else "Uncategorized"
                    
                    # Extract tvg-logo
                    logo_match = re.search(r'tvg-logo="([^"]*)"', attributes)
                    logo = logo_match.group(1) if logo_match else ""
                    
                    current_channel = {
                        'name': channel_name,
                        'group': group,
                        'logo': logo,
                        'attributes': attributes
                    }
                    
            # Parse URL line
            elif line.startswith('http://') or line.startswith('https://'):
                if current_channel:
                    current_channel['url'] = line
                    self.channels.append(current_channel)
                    current_channel = {}
        
        self.total_channels = len(self.channels)
        
        return self.get_basic_stats()
    
    def get_basic_stats(self) -> Dict:
        """
        Get basic statistics about the playlist
        """
        # Count categories
        categories = {}
        for channel in self.channels:
            group = channel.get('group', 'Uncategorized')
            categories[group] = categories.get(group, 0) + 1
        
        # Sort categories by count
        sorted_categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'total_channels': self.total_channels,
            'categories': sorted_categories,
            'top_5_categories': dict(list(sorted_categories.items())[:5])
        }
    
    def get_detailed_report(self) -> Dict:
        """
        Get detailed report with link checking results
        """
        stats = self.get_basic_stats()
        
        # Calculate health percentage
        health_percentage = 0
        if self.total_channels > 0:
            health_percentage = round((self.working_channels / self.total_channels) * 100, 1)
        
        report = {
            'summary': {
                'total_channels': stats['total_channels'],
                'total_categories': len(stats['categories']),
                'working_channels': self.working_channels,
                'dead_channels': self.dead_channels,
                'health_percentage': health_percentage,
                'checked': len(self.checked_channels) > 0
            },
            'categories': stats['categories'],
            'channels_sample': self.channels[:10]  # First 10 channels as sample
        }
        
        # Add dead channels list if we checked links
        if self.checked_channels:
            dead_list = [
                {
                    'name': ch['name'],
                    'url': ch['url'][:60] + '...' if len(ch['url']) > 60 else ch['url'],
                    'error': ch.get('error', 'No response')
                }
                for ch in self.checked_channels 
                if not ch.get('working', False)
            ]
            report['dead_channels_list'] = dead_list[:10]  # First 10 dead channels
        
        return report


async def analyze_playlist(file_path: str, check_links: bool = True) -> Dict:
    """
    Main function to analyze a playlist
    
    Args:
        file_path: Path to M3U file
        check_links: Whether to check if links are working (default: True)
        
    Returns:
        Analysis report
    """
    analyzer = PlaylistAnalyzer()
    stats = analyzer.parse_m3u(file_path=file_path)
    
    # Check links if requested
    if check_links and analyzer.total_channels > 0:
        await analyzer.check_all_links()
    
    return analyzer.get_detailed_report()


def analyze_playlist_sync(file_path: str, check_links: bool = True) -> Dict:
    """
    Synchronous wrapper for analyze_playlist
    
    Args:
        file_path: Path to M3U file
        check_links: Whether to check if links are working (default: True)
        
    Returns:
        Analysis report
    """
    return asyncio.run(analyze_playlist(file_path, check_links))


if __name__ == "__main__":
    # Example usage
    print("IPTV Playlist Analyzer - Step 2: Link Checking")
    print("=" * 50)
    print("\nReady to analyze playlists with link checking!")
    print("\nUsage:")
    print("  from playlist_analyzer import analyze_playlist_sync")
    print("  report = analyze_playlist_sync('your_playlist.m3u')")
    print("  # or without link checking:")
    print("  report = analyze_playlist_sync('your_playlist.m3u', check_links=False)")
