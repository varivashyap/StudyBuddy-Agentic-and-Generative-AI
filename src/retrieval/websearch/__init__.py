"""Web search module for question enrichment and resource recommendations."""

from .client import WebSearchClient
from .search_utils import SearchUtils
from .resource_recommender import ResourceRecommender

__all__ = ['WebSearchClient', 'SearchUtils', 'ResourceRecommender']

