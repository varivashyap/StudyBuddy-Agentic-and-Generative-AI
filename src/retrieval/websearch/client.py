"""
Web search client using DuckDuckGo (free, no API key required).
"""

import logging
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class WebSearchClient:
    """Web search client using DuckDuckGo."""
    
    def __init__(self, max_results: int = 5, timeout: int = 10):
        """
        Initialize web search client.
        
        Args:
            max_results: Maximum number of results to return
            timeout: Timeout for search requests in seconds
        """
        self.max_results = max_results
        self.timeout = timeout
        
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS()
            logger.info("✓ DuckDuckGo search client initialized")
        except ImportError:
            logger.error("duckduckgo-search not installed. Install with: pip install duckduckgo-search")
            self.ddgs = None
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Override default max results
            
        Returns:
            List of search results with title, url, snippet
        """
        if not self.ddgs:
            logger.error("Search client not initialized")
            return []
        
        max_results = max_results or self.max_results
        
        try:
            logger.info(f"Searching: {query}")
            
            results = []
            for result in self.ddgs.text(query, max_results=max_results):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                })
            
            logger.info(f"✓ Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_videos(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Search for videos (YouTube, etc.).
        
        Args:
            query: Search query
            max_results: Override default max results
            
        Returns:
            List of video results
        """
        if not self.ddgs:
            logger.error("Search client not initialized")
            return []
        
        max_results = max_results or self.max_results
        
        try:
            logger.info(f"Searching videos: {query}")
            
            results = []
            for result in self.ddgs.videos(query, max_results=max_results):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('content', ''),
                    'duration': result.get('duration', ''),
                    'publisher': result.get('publisher', ''),
                })
            
            logger.info(f"✓ Found {len(results)} video results")
            return results
            
        except Exception as e:
            logger.error(f"Video search failed: {e}")
            return []
    
    def search_news(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            max_results: Override default max results
            
        Returns:
            List of news results
        """
        if not self.ddgs:
            logger.error("Search client not initialized")
            return []
        
        max_results = max_results or self.max_results
        
        try:
            logger.info(f"Searching news: {query}")
            
            results = []
            for result in self.ddgs.news(query, max_results=max_results):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('body', ''),
                    'date': result.get('date', ''),
                    'source': result.get('source', ''),
                })
            
            logger.info(f"✓ Found {len(results)} news results")
            return results
            
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return []

