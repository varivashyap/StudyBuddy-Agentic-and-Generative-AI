"""Utilities for processing and filtering search results."""

import logging
import re
from typing import List, Dict, Set
from collections import Counter

logger = logging.getLogger(__name__)


class SearchUtils:
    """Utilities for search result processing."""
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 10) -> List[str]:
        """
        Extract top keywords from text.
        
        Args:
            text: Input text
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be enhanced with TF-IDF)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'will', 'would', 'could', 'should'}
        words = [w for w in words if w not in stop_words]
        
        # Count frequencies
        word_counts = Counter(words)
        top_keywords = [word for word, count in word_counts.most_common(top_n)]
        
        return top_keywords
    
    @staticmethod
    def extract_entities(text: str) -> Set[str]:
        """
        Extract named entities (simple capitalized words).
        
        Args:
            text: Input text
            
        Returns:
            Set of entities
        """
        # Simple entity extraction (capitalized words)
        entities = set()
        words = text.split()
        
        for word in words:
            word = word.strip('.,!?;:')
            if len(word) > 2 and word[0].isupper():
                entities.add(word)
        
        return entities
    
    @staticmethod
    def filter_duplicates(results: List[Dict], key: str = 'url') -> List[Dict]:
        """
        Filter duplicate results based on a key.
        
        Args:
            results: List of result dictionaries
            key: Key to use for deduplication
            
        Returns:
            Filtered list without duplicates
        """
        seen = set()
        filtered = []
        
        for result in results:
            value = result.get(key, '')
            if value and value not in seen:
                seen.add(value)
                filtered.append(result)
        
        return filtered
    
    @staticmethod
    def rank_by_relevance(results: List[Dict], query: str) -> List[Dict]:
        """
        Rank results by relevance to query.
        
        Args:
            results: List of search results
            query: Original query
            
        Returns:
            Ranked list of results
        """
        query_words = set(query.lower().split())
        
        scored_results = []
        for result in results:
            # Calculate relevance score based on keyword overlap
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            title_words = set(title.split())
            snippet_words = set(snippet.split())
            
            # Score based on overlap
            title_score = len(query_words.intersection(title_words)) * 2  # Title matches weighted more
            snippet_score = len(query_words.intersection(snippet_words))
            
            total_score = title_score + snippet_score
            
            scored_results.append((total_score, result))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [result for score, result in scored_results]
    
    @staticmethod
    def extract_practice_links(results: List[Dict], domains: List[str] = None) -> List[Dict]:
        """
        Extract practice/exercise links from results.
        
        Args:
            results: List of search results
            domains: List of trusted domains for practice problems
            
        Returns:
            Filtered list of practice links
        """
        if domains is None:
            # Default trusted domains for practice problems
            domains = [
                'khanacademy.org',
                'brilliant.org',
                'leetcode.com',
                'hackerrank.com',
                'projecteuler.net',
                'mathway.com',
                'wolframalpha.com',
                'stackoverflow.com',
                'github.com',
            ]
        
        practice_links = []
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # Check if from trusted domain
            is_trusted = any(domain in url for domain in domains)
            
            # Check if contains practice-related keywords
            practice_keywords = ['practice', 'exercise', 'problem', 'quiz', 'test', 'worksheet', 'tutorial']
            has_practice_keyword = any(keyword in title or keyword in snippet for keyword in practice_keywords)
            
            if is_trusted or has_practice_keyword:
                practice_links.append(result)
        
        return practice_links

