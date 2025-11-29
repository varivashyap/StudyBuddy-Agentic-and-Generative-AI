#!/usr/bin/env python3
"""
Evaluate improvements from finetuning or prompt engineering.

This script compares before/after results and generates comprehensive metrics.
"""

import json
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.improvement_metrics import ImprovementMetrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_results(before_dir: str, after_dir: str):
    """Load before and after results."""
    before_dir = Path(before_dir)
    after_dir = Path(after_dir)
    
    results = {
        'before': {},
        'after': {}
    }
    
    # Load summaries
    before_summary = before_dir / "summary.json"
    after_summary = after_dir / "summary.json"
    
    if before_summary.exists() and after_summary.exists():
        with open(before_summary) as f:
            results['before']['summary'] = json.load(f)
        with open(after_summary) as f:
            results['after']['summary'] = json.load(f)
        logger.info("✓ Loaded summary results")
    
    # Load flashcards
    before_flashcards = before_dir / "flashcards.json"
    after_flashcards = after_dir / "flashcards.json"
    
    if before_flashcards.exists() and after_flashcards.exists():
        with open(before_flashcards) as f:
            results['before']['flashcards'] = json.load(f)
        with open(after_flashcards) as f:
            results['after']['flashcards'] = json.load(f)
        logger.info("✓ Loaded flashcard results")
    
    # Load quiz questions
    before_quiz = before_dir / "questions.json"
    after_quiz = after_dir / "questions.json"
    
    if before_quiz.exists() and after_quiz.exists():
        with open(before_quiz) as f:
            results['before']['quiz'] = json.load(f)
        with open(after_quiz) as f:
            results['after']['quiz'] = json.load(f)
        logger.info("✓ Loaded quiz results")
    
    return results


def evaluate_summaries(metrics: ImprovementMetrics, before: dict, after: dict, source: str):
    """Evaluate summary improvements."""
    logger.info("\n=== Evaluating Summaries ===")
    
    before_summary = before.get('summary', '')
    after_summary = after.get('summary', '')
    
    if not before_summary or not after_summary:
        logger.warning("Missing summary data")
        return None
    
    # For demo, use the after summary as reference (in real use, you'd have gold standard)
    # In practice, you'd have human-written reference summaries
    reference = after_summary  # Replace with actual reference
    
    before_metrics = metrics.evaluate_summary(before_summary, reference, source)
    after_metrics = metrics.evaluate_summary(after_summary, reference, source)
    
    logger.info(f"Before - ROUGE-L: {before_metrics.get('rouge_l', 0):.3f}, BERTScore: {before_metrics.get('bert_score_f1', 0):.3f}")
    logger.info(f"After  - ROUGE-L: {after_metrics.get('rouge_l', 0):.3f}, BERTScore: {after_metrics.get('bert_score_f1', 0):.3f}")
    
    return {
        'before': before_metrics,
        'after': after_metrics
    }


def evaluate_flashcards(metrics: ImprovementMetrics, before: dict, after: dict, source: str):
    """Evaluate flashcard improvements."""
    logger.info("\n=== Evaluating Flashcards ===")
    
    before_cards = before.get('flashcards', [])
    after_cards = after.get('flashcards', [])
    
    if not before_cards or not after_cards:
        logger.warning("Missing flashcard data")
        return None
    
    before_metrics = metrics.evaluate_flashcards(before_cards, source)
    after_metrics = metrics.evaluate_flashcards(after_cards, source)
    
    logger.info(f"Before - Coverage: {before_metrics.get('coverage', 0):.3f}, Redundancy: {before_metrics.get('redundancy', 0):.3f}")
    logger.info(f"After  - Coverage: {after_metrics.get('coverage', 0):.3f}, Redundancy: {after_metrics.get('redundancy', 0):.3f}")
    
    return {
        'before': before_metrics,
        'after': after_metrics
    }


def evaluate_quiz(metrics: ImprovementMetrics, before: dict, after: dict, source: str):
    """Evaluate quiz improvements."""
    logger.info("\n=== Evaluating Quiz Questions ===")
    
    before_questions = before.get('questions', [])
    after_questions = after.get('questions', [])
    
    if not before_questions or not after_questions:
        logger.warning("Missing quiz data")
        return None
    
    before_metrics = metrics.evaluate_quiz(before_questions, source)
    after_metrics = metrics.evaluate_quiz(after_questions, source)
    
    logger.info(f"Before - Factuality: {before_metrics.get('factuality', 0):.3f}, Relevance: {before_metrics.get('relevance', 0):.3f}")
    logger.info(f"After  - Factuality: {after_metrics.get('factuality', 0):.3f}, Relevance: {after_metrics.get('relevance', 0):.3f}")
    
    return {
        'before': before_metrics,
        'after': after_metrics
    }


def main():
    """Main evaluation function."""
    logger.info("=" * 70)
    logger.info("Evaluation: Before vs After Comparison")
    logger.info("=" * 70)
    
    # Paths
    before_dir = "results/testing_before"
    after_dir = "results/testing"
    source_text_path = "data/preprocessed/sample_lecture_asr.txt"
    
    # Load source text
    if Path(source_text_path).exists():
        with open(source_text_path) as f:
            source_text = f.read()
    else:
        logger.warning(f"Source text not found: {source_text_path}")
        source_text = ""
    
    # Load results
    results = load_results(before_dir, after_dir)
    
    # Initialize metrics
    metrics = ImprovementMetrics()
    
    # Evaluate each task
    all_metrics = {}
    
    if 'summary' in results['before'] and 'summary' in results['after']:
        all_metrics['summary'] = evaluate_summaries(
            metrics,
            results['before']['summary'],
            results['after']['summary'],
            source_text
        )
    
    if 'flashcards' in results['before'] and 'flashcards' in results['after']:
        all_metrics['flashcards'] = evaluate_flashcards(
            metrics,
            results['before']['flashcards'],
            results['after']['flashcards'],
            source_text
        )
    
    if 'quiz' in results['before'] and 'quiz' in results['after']:
        all_metrics['quiz'] = evaluate_quiz(
            metrics,
            results['before']['quiz'],
            results['after']['quiz'],
            source_text
        )
    
    # Save comprehensive report
    output_dir = Path("results/metrics")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / "improvement_report.json"
    with open(report_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"\n✓ Evaluation complete! Report saved to: {report_path}")
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    for task, task_metrics in all_metrics.items():
        if task_metrics:
            logger.info(f"\n{task.upper()}:")
            logger.info(f"  Metrics available: {list(task_metrics.get('before', {}).keys())}")


if __name__ == "__main__":
    main()

