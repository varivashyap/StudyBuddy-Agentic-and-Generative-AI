"""Evaluation metrics for generated content."""

import logging
from typing import List, Dict, Any
import json
from pathlib import Path

from ..config import get_config

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Track and compute evaluation metrics."""
    
    def __init__(self):
        """Initialize evaluation metrics."""
        self.config = get_config()
        self.feedback_enabled = self.config.get("evaluation.feedback.enabled", True)
        self.feedback_file = self.config.get("evaluation.feedback.storage", "data/feedback.jsonl")
        
        # Initialize metrics storage
        self.metrics = {
            "factuality": [],
            "coverage": [],
            "recall_at_k": [],
            "user_ratings": []
        }
    
    def record_factuality(self, score: float, content_type: str):
        """
        Record factuality score.
        
        Args:
            score: Factuality score (0-1)
            content_type: Type of content (summary, flashcard, quiz)
        """
        self.metrics["factuality"].append({
            "score": score,
            "type": content_type
        })
    
    def record_coverage(self, score: float, content_type: str):
        """
        Record coverage score.
        
        Args:
            score: Coverage score (0-1)
            content_type: Type of content
        """
        self.metrics["coverage"].append({
            "score": score,
            "type": content_type
        })
    
    def record_recall_at_k(self, k: int, score: float):
        """
        Record recall@k for retrieval.
        
        Args:
            k: Number of retrieved documents
            score: Recall score (0-1)
        """
        self.metrics["recall_at_k"].append({
            "k": k,
            "score": score
        })
    
    def record_user_feedback(
        self,
        content_id: str,
        content_type: str,
        rating: int,
        comment: str = ""
    ):
        """
        Record user feedback.
        
        Args:
            content_id: Unique identifier for content
            content_type: Type of content
            rating: User rating (e.g., 1-5 or thumbs up/down)
            comment: Optional comment
        """
        feedback = {
            "content_id": content_id,
            "type": content_type,
            "rating": rating,
            "comment": comment
        }
        
        self.metrics["user_ratings"].append(feedback)
        
        # Save to file if enabled
        if self.feedback_enabled:
            self._save_feedback(feedback)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.
        
        Returns:
            Dict with metric summaries
        """
        summary = {}
        
        # Factuality
        if self.metrics["factuality"]:
            scores = [m["score"] for m in self.metrics["factuality"]]
            summary["factuality"] = {
                "mean": sum(scores) / len(scores),
                "count": len(scores)
            }
        
        # Coverage
        if self.metrics["coverage"]:
            scores = [m["score"] for m in self.metrics["coverage"]]
            summary["coverage"] = {
                "mean": sum(scores) / len(scores),
                "count": len(scores)
            }
        
        # Recall@k
        if self.metrics["recall_at_k"]:
            by_k = {}
            for m in self.metrics["recall_at_k"]:
                k = m["k"]
                if k not in by_k:
                    by_k[k] = []
                by_k[k].append(m["score"])
            
            summary["recall_at_k"] = {
                k: sum(scores) / len(scores)
                for k, scores in by_k.items()
            }
        
        # User ratings
        if self.metrics["user_ratings"]:
            ratings = [m["rating"] for m in self.metrics["user_ratings"]]
            summary["user_ratings"] = {
                "mean": sum(ratings) / len(ratings),
                "count": len(ratings)
            }
        
        return summary
    
    def _save_feedback(self, feedback: Dict[str, Any]):
        """Save feedback to JSONL file."""
        try:
            feedback_path = Path(self.feedback_file)
            feedback_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(feedback_path, 'a') as f:
                f.write(json.dumps(feedback) + '\n')
            
            logger.debug(f"Saved feedback to {feedback_path}")
        
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
    
    def load_feedback(self) -> List[Dict[str, Any]]:
        """
        Load all feedback from file.
        
        Returns:
            List of feedback dicts
        """
        feedback_path = Path(self.feedback_file)
        
        if not feedback_path.exists():
            return []
        
        feedback_list = []
        
        try:
            with open(feedback_path, 'r') as f:
                for line in f:
                    feedback_list.append(json.loads(line))
            
            logger.info(f"Loaded {len(feedback_list)} feedback entries")
            return feedback_list
        
        except Exception as e:
            logger.error(f"Failed to load feedback: {e}")
            return []

