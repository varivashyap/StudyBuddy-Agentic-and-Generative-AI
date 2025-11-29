"""Resource recommender for additional learning materials."""

import logging
from typing import List, Dict, Optional
from .client import WebSearchClient
from .search_utils import SearchUtils

logger = logging.getLogger(__name__)


class ResourceRecommender:
    """Recommend additional learning resources based on content."""
    
    def __init__(self, max_results: int = 5):
        """
        Initialize resource recommender.
        
        Args:
            max_results: Maximum results per search
        """
        self.search_client = WebSearchClient(max_results=max_results)
        self.search_utils = SearchUtils()
    
    def recommend_for_topic(self, topic: str, content: str) -> Dict[str, List[Dict]]:
        """
        Recommend resources for a specific topic.
        
        Args:
            topic: Main topic/subject
            content: Content text for context
            
        Returns:
            Dictionary of recommended resources by type
        """
        recommendations = {
            'videos': [],
            'articles': [],
            'practice': [],
            'textbooks': [],
        }
        
        # Extract keywords for better search
        keywords = self.search_utils.extract_keywords(content, top_n=5)
        search_query = f"{topic} {' '.join(keywords[:3])}"
        
        logger.info(f"Finding resources for: {search_query}")
        
        # Search for videos
        video_query = f"{topic} tutorial video"
        videos = self.search_client.search_videos(video_query)
        recommendations['videos'] = videos
        
        # Search for articles/textbooks
        article_query = f"{topic} textbook chapter"
        articles = self.search_client.search(article_query)
        recommendations['articles'] = articles
        
        # Search for practice problems
        practice_query = f"{topic} practice problems exercises"
        practice_results = self.search_client.search(practice_query)
        practice_links = self.search_utils.extract_practice_links(practice_results)
        recommendations['practice'] = practice_links
        
        logger.info(f"✓ Found {len(videos)} videos, {len(articles)} articles, {len(practice_links)} practice resources")
        
        return recommendations
    
    def enrich_quiz_questions(
        self,
        questions: List[Dict],
        source_content: str,
        enable_web: bool = True
    ) -> List[Dict]:
        """
        Enrich quiz questions with web search results.
        
        Args:
            questions: List of generated questions
            source_content: Source content text
            enable_web: Whether to enable web enrichment
            
        Returns:
            Enriched questions with additional context
        """
        if not enable_web:
            return questions
        
        logger.info("Enriching quiz questions with web search...")
        
        # Extract main topics
        entities = self.search_utils.extract_entities(source_content)
        keywords = self.search_utils.extract_keywords(source_content, top_n=5)
        
        enriched_questions = []
        
        for question in questions:
            enriched_q = question.copy()
            
            # Search for related information
            q_text = question.get('question', '')
            if q_text:
                # Search for additional context
                search_results = self.search_client.search(q_text, max_results=3)
                
                if search_results:
                    enriched_q['web_context'] = [
                        {
                            'title': r['title'],
                            'url': r['url'],
                            'snippet': r['snippet']
                        }
                        for r in search_results[:2]
                    ]
            
            enriched_questions.append(enriched_q)
        
        logger.info(f"✓ Enriched {len(enriched_questions)} questions")
        
        return enriched_questions
    
    def suggest_related_topics(self, main_topic: str, num_suggestions: int = 5) -> List[str]:
        """
        Suggest related topics for further study.
        
        Args:
            main_topic: Main topic
            num_suggestions: Number of suggestions to return
            
        Returns:
            List of related topic suggestions
        """
        logger.info(f"Finding related topics for: {main_topic}")
        
        # Search for related topics
        query = f"{main_topic} related topics concepts"
        results = self.search_client.search(query, max_results=10)
        
        # Extract topics from titles and snippets
        related_topics = set()
        
        for result in results:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Extract capitalized phrases (potential topics)
            entities = self.search_utils.extract_entities(title + ' ' + snippet)
            related_topics.update(entities)
        
        # Remove the main topic itself
        related_topics.discard(main_topic)
        
        # Return top suggestions
        suggestions = list(related_topics)[:num_suggestions]
        
        logger.info(f"✓ Found {len(suggestions)} related topics")
        
        return suggestions

