"""
Quantitative evaluation metrics for comparing before/after improvements.

Metrics:
- Summary: ROUGE-L, BERTScore, cosine similarity
- Flashcards: Coverage, redundancy, semantic precision/recall
- Quizzes: Factuality (NLI), difficulty consistency, relevance
"""

import logging
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class ImprovementMetrics:
    """Evaluate improvements from finetuning/prompt-tuning."""
    
    def __init__(self, output_dir: str = "results/metrics"):
        """
        Initialize improvement metrics.
        
        Args:
            output_dir: Directory to save metric results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load models for evaluation
        self._load_models()
        
        logger.info(f"Improvement metrics initialized. Output: {output_dir}")
    
    def _load_models(self):
        """Load models needed for evaluation."""
        try:
            # BERTScore
            from bert_score import BERTScorer
            self.bert_scorer = BERTScorer(lang="en", rescale_with_baseline=True)
            logger.info("✓ BERTScore model loaded")
        except ImportError:
            logger.warning("BERTScore not available. Install with: pip install bert-score")
            self.bert_scorer = None
        
        try:
            # Sentence embeddings for similarity
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✓ Embedding model loaded")
        except ImportError:
            logger.warning("sentence-transformers not available")
            self.embedding_model = None
        
        try:
            # NLI model for factuality
            from transformers import pipeline
            self.nli_model = pipeline("text-classification", model="microsoft/deberta-base-mnli")
            logger.info("✓ NLI model loaded")
        except ImportError:
            logger.warning("NLI model not available")
            self.nli_model = None
    
    def evaluate_summary(
        self,
        generated: str,
        reference: str,
        source: str
    ) -> Dict[str, float]:
        """
        Evaluate summary quality.
        
        Args:
            generated: Generated summary
            reference: Reference/gold summary
            source: Source text
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # ROUGE-L
        try:
            from rouge_score import rouge_scorer
            scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
            rouge_scores = scorer.score(reference, generated)
            metrics['rouge_l'] = rouge_scores['rougeL'].fmeasure
        except ImportError:
            logger.warning("rouge-score not available. Install with: pip install rouge-score")
            metrics['rouge_l'] = 0.0
        
        # BERTScore
        if self.bert_scorer:
            P, R, F1 = self.bert_scorer.score([generated], [reference])
            metrics['bert_score_f1'] = F1.item()
            metrics['bert_score_precision'] = P.item()
            metrics['bert_score_recall'] = R.item()
        else:
            metrics['bert_score_f1'] = 0.0
        
        # Cosine similarity with reference
        if self.embedding_model:
            gen_emb = self.embedding_model.encode([generated])[0]
            ref_emb = self.embedding_model.encode([reference])[0]
            similarity = np.dot(gen_emb, ref_emb) / (np.linalg.norm(gen_emb) * np.linalg.norm(ref_emb))
            metrics['cosine_similarity'] = float(similarity)
        else:
            metrics['cosine_similarity'] = 0.0
        
        # Length ratio
        metrics['length_ratio'] = len(generated.split()) / max(len(reference.split()), 1)
        
        logger.info(f"Summary metrics: ROUGE-L={metrics['rouge_l']:.3f}, BERTScore={metrics['bert_score_f1']:.3f}")
        
        return metrics
    
    def evaluate_flashcards(
        self,
        generated: List[Dict],
        reference: List[Dict],
        source: str
    ) -> Dict[str, float]:
        """
        Evaluate flashcard quality.
        
        Args:
            generated: Generated flashcards
            reference: Reference/gold flashcards
            source: Source text
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # Extract key concepts from source
        source_concepts = self._extract_concepts(source)
        gen_concepts = self._extract_flashcard_concepts(generated)
        ref_concepts = self._extract_flashcard_concepts(reference)
        
        # Coverage score (% of source concepts covered)
        if source_concepts:
            covered = len(gen_concepts.intersection(source_concepts))
            metrics['coverage'] = covered / len(source_concepts)
        else:
            metrics['coverage'] = 0.0
        
        # Redundancy score (lower is better)
        if gen_concepts:
            unique_concepts = len(set(gen_concepts))
            total_concepts = len(list(gen_concepts))
            metrics['redundancy'] = 1.0 - (unique_concepts / total_concepts)
        else:
            metrics['redundancy'] = 0.0
        
        # Semantic precision/recall vs reference
        if self.embedding_model and ref_concepts:
            precision, recall = self._compute_semantic_precision_recall(gen_concepts, ref_concepts)
            metrics['semantic_precision'] = precision
            metrics['semantic_recall'] = recall
            metrics['semantic_f1'] = 2 * precision * recall / (precision + recall + 1e-10)
        else:
            metrics['semantic_precision'] = 0.0
            metrics['semantic_recall'] = 0.0
            metrics['semantic_f1'] = 0.0
        
        logger.info(f"Flashcard metrics: Coverage={metrics['coverage']:.3f}, F1={metrics['semantic_f1']:.3f}")

        return metrics

    def evaluate_quiz(
        self,
        generated: List[Dict],
        reference: List[Dict],
        source: str
    ) -> Dict[str, float]:
        """
        Evaluate quiz question quality.

        Args:
            generated: Generated questions
            reference: Reference/gold questions
            source: Source text

        Returns:
            Dictionary of metrics
        """
        metrics = {}

        # Factuality score using NLI
        if self.nli_model:
            factuality_scores = []
            for q in generated:
                question_text = q.get('question', '')
                answer_text = q.get('answer', '')
                if question_text and answer_text:
                    # Check if answer is entailed by source
                    result = self.nli_model(f"{source} [SEP] {answer_text}")
                    entailment_score = next((r['score'] for r in result if r['label'] == 'ENTAILMENT'), 0.0)
                    factuality_scores.append(entailment_score)

            metrics['factuality'] = np.mean(factuality_scores) if factuality_scores else 0.0
        else:
            metrics['factuality'] = 0.0

        # Difficulty consistency (entropy-based)
        difficulties = [q.get('difficulty', 'medium') for q in generated]
        difficulty_counts = Counter(difficulties)
        total = len(difficulties)
        if total > 0:
            probs = [count / total for count in difficulty_counts.values()]
            entropy = -sum(p * np.log(p + 1e-10) for p in probs)
            # Normalize entropy (max entropy for 3 categories is log(3))
            metrics['difficulty_consistency'] = entropy / np.log(3)
        else:
            metrics['difficulty_consistency'] = 0.0

        # Relevance (embedding similarity with source)
        if self.embedding_model:
            source_emb = self.embedding_model.encode([source])[0]
            relevance_scores = []
            for q in generated:
                q_text = q.get('question', '')
                if q_text:
                    q_emb = self.embedding_model.encode([q_text])[0]
                    similarity = np.dot(q_emb, source_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(source_emb))
                    relevance_scores.append(similarity)

            metrics['relevance'] = np.mean(relevance_scores) if relevance_scores else 0.0
        else:
            metrics['relevance'] = 0.0

        logger.info(f"Quiz metrics: Factuality={metrics['factuality']:.3f}, Relevance={metrics['relevance']:.3f}")

        return metrics

    def _extract_concepts(self, text: str) -> set:
        """Extract key concepts from text (simple noun phrase extraction)."""
        # Simple approach: extract capitalized words and common nouns
        words = text.split()
        concepts = set()
        for word in words:
            word = word.strip('.,!?;:')
            if len(word) > 3 and (word[0].isupper() or word.lower() in ['process', 'system', 'method', 'theory']):
                concepts.add(word.lower())
        return concepts

    def _extract_flashcard_concepts(self, flashcards: List[Dict]) -> set:
        """Extract concepts from flashcards."""
        concepts = set()
        for card in flashcards:
            front = card.get('front', '')
            back = card.get('back', '')
            concepts.update(self._extract_concepts(front + ' ' + back))
        return concepts

    def _compute_semantic_precision_recall(
        self,
        generated_concepts: set,
        reference_concepts: set
    ) -> Tuple[float, float]:
        """Compute semantic precision and recall using embeddings."""
        if not self.embedding_model or not generated_concepts or not reference_concepts:
            return 0.0, 0.0

        gen_list = list(generated_concepts)
        ref_list = list(reference_concepts)

        gen_embs = self.embedding_model.encode(gen_list)
        ref_embs = self.embedding_model.encode(ref_list)

        # Compute similarity matrix
        similarity_matrix = np.dot(gen_embs, ref_embs.T)

        # Precision: for each generated concept, find max similarity with reference
        precision_scores = np.max(similarity_matrix, axis=1)
        precision = np.mean(precision_scores)

        # Recall: for each reference concept, find max similarity with generated
        recall_scores = np.max(similarity_matrix, axis=0)
        recall = np.mean(recall_scores)

        return float(precision), float(recall)

    def compare_before_after(
        self,
        before_results: Dict[str, Any],
        after_results: Dict[str, Any],
        task_type: str
    ) -> Dict[str, Any]:
        """
        Compare before and after results.

        Args:
            before_results: Results before improvement
            after_results: Results after improvement
            task_type: Type of task (summary, flashcard, quiz)

        Returns:
            Comparison metrics
        """
        comparison = {
            'task_type': task_type,
            'before': before_results,
            'after': after_results,
            'improvement': {}
        }

        # Calculate improvement for each metric
        for metric_name in before_results.keys():
            before_val = before_results[metric_name]
            after_val = after_results[metric_name]

            if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                improvement = after_val - before_val
                improvement_pct = (improvement / (abs(before_val) + 1e-10)) * 100
                comparison['improvement'][metric_name] = {
                    'absolute': improvement,
                    'percentage': improvement_pct
                }

        return comparison

    def generate_improvement_report(
        self,
        summary_comparison: Dict,
        flashcard_comparison: Dict,
        quiz_comparison: Dict
    ) -> Dict[str, Any]:
        """
        Generate comprehensive improvement report.

        Args:
            summary_comparison: Summary comparison results
            flashcard_comparison: Flashcard comparison results
            quiz_comparison: Quiz comparison results

        Returns:
            Complete improvement report
        """
        # Calculate overall gain (average of key metrics)
        summary_gain = summary_comparison['after'].get('bert_score_f1', 0) - summary_comparison['before'].get('bert_score_f1', 0)
        flashcard_gain = flashcard_comparison['after'].get('semantic_f1', 0) - flashcard_comparison['before'].get('semantic_f1', 0)
        quiz_gain = quiz_comparison['after'].get('factuality', 0) - quiz_comparison['before'].get('factuality', 0)

        overall_gain = (summary_gain + flashcard_gain + quiz_gain) / 3

        report = {
            'summary': summary_comparison,
            'flashcards': flashcard_comparison,
            'quiz': quiz_comparison,
            'overall_gain': float(overall_gain)
        }

        # Save report
        report_file = self.output_dir / "improvement_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✓ Improvement report saved to {report_file}")
        logger.info(f"Overall gain: {overall_gain:.4f}")

        return report

