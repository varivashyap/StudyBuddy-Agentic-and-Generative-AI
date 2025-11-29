#!/usr/bin/env python3
"""
Test web search functionality.

This script demonstrates:
1. Basic web search
2. Video search
3. Resource recommendations
4. Quiz question enrichment
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.websearch import WebSearchClient, ResourceRecommender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_search():
    """Test basic web search."""
    logger.info("=" * 70)
    logger.info("Test 1: Basic Web Search")
    logger.info("=" * 70)
    
    client = WebSearchClient()
    
    # Search for a topic
    query = "photosynthesis process in plants"
    logger.info(f"\nSearching for: '{query}'")
    
    results = client.search(query, max_results=5)
    
    logger.info(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        logger.info(f"\n{i}. {result['title']}")
        logger.info(f"   URL: {result['url']}")
        logger.info(f"   Snippet: {result.get('snippet', 'N/A')[:100]}...")
    
    return results


def test_video_search():
    """Test video search."""
    logger.info("\n" + "=" * 70)
    logger.info("Test 2: Video Search")
    logger.info("=" * 70)
    
    client = WebSearchClient()
    
    # Search for educational videos
    query = "photosynthesis explained"
    logger.info(f"\nSearching for videos: '{query}'")
    
    videos = client.search_videos(query, max_results=5)
    
    logger.info(f"\nFound {len(videos)} videos:")
    for i, video in enumerate(videos, 1):
        logger.info(f"\n{i}. {video['title']}")
        logger.info(f"   URL: {video['url']}")
        logger.info(f"   Source: {video.get('source', 'Unknown')}")
    
    return videos


def test_resource_recommender():
    """Test resource recommender."""
    logger.info("\n" + "=" * 70)
    logger.info("Test 3: Resource Recommender")
    logger.info("=" * 70)
    
    recommender = ResourceRecommender()
    
    # Get recommendations for a topic
    topic = "photosynthesis"
    content = """
    Photosynthesis is the process by which plants convert sunlight, CO2, and water 
    into glucose and oxygen. It occurs in chloroplasts and involves light-dependent 
    reactions and the Calvin cycle.
    """
    
    logger.info(f"\nGetting recommendations for: '{topic}'")
    
    resources = recommender.recommend_for_topic(topic, content)
    
    logger.info(f"\nRecommended Resources:")
    logger.info(f"  Videos: {len(resources['videos'])}")
    for video in resources['videos'][:3]:
        logger.info(f"    - {video['title']}")
    
    logger.info(f"\n  Articles: {len(resources['articles'])}")
    for article in resources['articles'][:3]:
        logger.info(f"    - {article['title']}")
    
    logger.info(f"\n  Practice Problems: {len(resources['practice'])}")
    for practice in resources['practice'][:3]:
        logger.info(f"    - {practice['title']}")
    
    return resources


def test_quiz_enrichment():
    """Test quiz question enrichment."""
    logger.info("\n" + "=" * 70)
    logger.info("Test 4: Quiz Question Enrichment")
    logger.info("=" * 70)
    
    recommender = ResourceRecommender()
    
    # Sample quiz questions
    questions = [
        {
            "question": "What are the products of photosynthesis?",
            "answer": "Glucose and oxygen",
            "type": "short_answer"
        },
        {
            "question": "Where does photosynthesis occur in plant cells?",
            "answer": "In chloroplasts",
            "type": "short_answer"
        }
    ]
    
    content = """
    Photosynthesis is the process by which plants convert sunlight, CO2, and water 
    into glucose and oxygen. It occurs in chloroplasts.
    """
    
    logger.info("\nEnriching quiz questions with web resources...")
    
    enriched = recommender.enrich_quiz_questions(questions, content)
    
    logger.info(f"\nEnriched {len(enriched)} questions:")
    for i, q in enumerate(enriched, 1):
        logger.info(f"\n{i}. {q['question']}")
        logger.info(f"   Answer: {q['answer']}")
        
        if 'related_resources' in q:
            resources = q['related_resources']
            logger.info(f"   Related Resources:")
            if resources.get('videos'):
                logger.info(f"     Videos: {len(resources['videos'])}")
            if resources.get('articles'):
                logger.info(f"     Articles: {len(resources['articles'])}")
    
    return enriched


def test_related_topics():
    """Test related topic suggestions."""
    logger.info("\n" + "=" * 70)
    logger.info("Test 5: Related Topic Suggestions")
    logger.info("=" * 70)
    
    recommender = ResourceRecommender()
    
    topic = "photosynthesis"
    logger.info(f"\nFinding related topics for: '{topic}'")
    
    related = recommender.suggest_related_topics(topic)
    
    logger.info(f"\nRelated Topics ({len(related)}):")
    for i, related_topic in enumerate(related, 1):
        logger.info(f"  {i}. {related_topic['topic']}")
        logger.info(f"     Relevance: {related_topic.get('relevance', 'N/A')}")
    
    return related


def main():
    """Run all web search tests."""
    logger.info("=" * 70)
    logger.info("Web Search Feature Tests")
    logger.info("=" * 70)
    
    try:
        # Test 1: Basic search
        test_basic_search()
        
        # Test 2: Video search
        test_video_search()
        
        # Test 3: Resource recommender
        test_resource_recommender()
        
        # Test 4: Quiz enrichment
        test_quiz_enrichment()
        
        # Test 5: Related topics
        test_related_topics()
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ All web search tests completed successfully!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

