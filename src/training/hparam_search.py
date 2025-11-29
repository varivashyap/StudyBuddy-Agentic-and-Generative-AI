"""
Hyperparameter search for model training and generation.

Supports:
- Grid search
- Bayesian optimization (Optuna)

Tunes:
- Learning rate
- Batch size
- Number of epochs
- Max sequence length
- Temperature, top_p for generation
"""

import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

logger = logging.getLogger(__name__)


class HyperparameterSearch:
    """Hyperparameter search using grid search or Bayesian optimization."""
    
    def __init__(self, output_dir: str = "results/hparams"):
        """
        Initialize hyperparameter search.
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.best_params = None
        self.best_score = float('-inf')
        
        logger.info(f"Hyperparameter search initialized. Output: {output_dir}")
    
    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        objective_fn,
        metric: str = "loss"
    ) -> Dict[str, Any]:
        """
        Perform grid search over hyperparameters.
        
        Args:
            param_grid: Dictionary of parameter names to lists of values
            objective_fn: Function that takes params dict and returns metric value
            metric: Metric to optimize (higher is better)
            
        Returns:
            Best parameters found
        """
        from itertools import product
        
        logger.info("Starting grid search...")
        logger.info(f"Parameter grid: {param_grid}")
        
        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        logger.info(f"Total combinations to try: {len(combinations)}")
        
        results = []
        
        for i, values in enumerate(combinations):
            params = dict(zip(param_names, values))
            logger.info(f"\n[{i+1}/{len(combinations)}] Testing: {params}")
            
            try:
                score = objective_fn(params)
                results.append({
                    'params': params,
                    'score': score
                })
                
                logger.info(f"Score: {score:.4f}")
                
                # Update best
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                    logger.info(f"✓ New best score: {score:.4f}")
                    
            except Exception as e:
                logger.error(f"Error with params {params}: {e}")
                continue
        
        # Save results
        self._save_results(results, "grid_search")
        
        logger.info(f"\n✓ Grid search completed")
        logger.info(f"Best score: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")
        
        return self.best_params
    
    def bayesian_search(
        self,
        param_space: Dict[str, tuple],
        objective_fn,
        n_trials: int = 50,
        metric: str = "loss",
        direction: str = "maximize"
    ) -> Dict[str, Any]:
        """
        Perform Bayesian optimization using Optuna.
        
        Args:
            param_space: Dictionary of parameter names to (min, max) tuples or lists
            objective_fn: Function that takes params dict and returns metric value
            n_trials: Number of trials to run
            metric: Metric to optimize
            direction: "maximize" or "minimize"
            
        Returns:
            Best parameters found
        """
        logger.info("Starting Bayesian optimization with Optuna...")
        logger.info(f"Parameter space: {param_space}")
        logger.info(f"Number of trials: {n_trials}")
        
        def optuna_objective(trial):
            """Optuna objective function."""
            params = {}
            
            for param_name, param_config in param_space.items():
                if isinstance(param_config, tuple) and len(param_config) == 2:
                    # Continuous parameter
                    min_val, max_val = param_config
                    if isinstance(min_val, float) or isinstance(max_val, float):
                        params[param_name] = trial.suggest_float(param_name, min_val, max_val)
                    else:
                        params[param_name] = trial.suggest_int(param_name, min_val, max_val)
                elif isinstance(param_config, list):
                    # Categorical parameter
                    params[param_name] = trial.suggest_categorical(param_name, param_config)
                else:
                    raise ValueError(f"Invalid parameter config for {param_name}: {param_config}")
            
            logger.info(f"Trial {trial.number}: {params}")
            
            try:
                score = objective_fn(params)
                logger.info(f"Trial {trial.number} score: {score:.4f}")
                return score
            except Exception as e:
                logger.error(f"Trial {trial.number} failed: {e}")
                raise optuna.TrialPruned()
        
        # Create study
        study = optuna.create_study(
            direction=direction,
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10)
        )
        
        # Optimize
        study.optimize(optuna_objective, n_trials=n_trials, show_progress_bar=True)
        
        # Get best results
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        # Save results
        results = [{
            'params': trial.params,
            'score': trial.value
        } for trial in study.trials if trial.value is not None]
        
        self._save_results(results, "bayesian_search")
        
        logger.info(f"\n✓ Bayesian optimization completed")
        logger.info(f"Best score: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")

        return self.best_params

    def _save_results(self, results: List[Dict], search_type: str):
        """Save search results to files."""
        # Save all results as JSON
        results_file = self.output_dir / f"{search_type}_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {results_file}")

        # Save best params as YAML
        if self.best_params:
            best_file = self.output_dir / "best.yaml"
            with open(best_file, 'w') as f:
                yaml.dump({
                    'best_score': float(self.best_score),
                    'best_params': self.best_params,
                    'search_type': search_type
                }, f, default_flow_style=False)
            logger.info(f"Best parameters saved to {best_file}")

    def tune_training_params(
        self,
        train_fn,
        eval_fn,
        search_type: str = "bayesian",
        n_trials: int = 20
    ) -> Dict[str, Any]:
        """
        Tune training hyperparameters.

        Args:
            train_fn: Function that trains model with given params
            eval_fn: Function that evaluates model and returns score
            search_type: "grid" or "bayesian"
            n_trials: Number of trials (for Bayesian search)

        Returns:
            Best parameters
        """
        # Define parameter space for training
        if search_type == "grid":
            param_grid = {
                'learning_rate': [1e-4, 2e-4, 5e-4],
                'batch_size': [2, 4, 8],
                'num_epochs': [2, 3, 5],
                'max_seq_length': [1024, 2048],
            }

            def objective(params):
                train_fn(params)
                return eval_fn()

            return self.grid_search(param_grid, objective)

        else:  # bayesian
            param_space = {
                'learning_rate': (1e-5, 1e-3),
                'batch_size': [2, 4, 8, 16],
                'num_epochs': (2, 10),
                'max_seq_length': [512, 1024, 2048, 4096],
                'lora_r': (8, 64),
                'lora_alpha': (16, 128),
            }

            def objective(params):
                train_fn(params)
                return eval_fn()

            return self.bayesian_search(param_space, objective, n_trials=n_trials)

    def tune_generation_params(
        self,
        generate_fn,
        eval_fn,
        search_type: str = "bayesian",
        n_trials: int = 30
    ) -> Dict[str, Any]:
        """
        Tune generation hyperparameters.

        Args:
            generate_fn: Function that generates output with given params
            eval_fn: Function that evaluates generation quality
            search_type: "grid" or "bayesian"
            n_trials: Number of trials (for Bayesian search)

        Returns:
            Best parameters
        """
        # Define parameter space for generation
        if search_type == "grid":
            param_grid = {
                'temperature': [0.0, 0.1, 0.2, 0.3, 0.5],
                'top_p': [0.8, 0.9, 0.95, 1.0],
                'max_tokens': [150, 200, 300, 500],
            }

            def objective(params):
                outputs = generate_fn(params)
                return eval_fn(outputs)

            return self.grid_search(param_grid, objective)

        else:  # bayesian
            param_space = {
                'temperature': (0.0, 1.0),
                'top_p': (0.7, 1.0),
                'max_tokens': (100, 1000),
                'top_k': (10, 100),
            }

            def objective(params):
                outputs = generate_fn(params)
                return eval_fn(outputs)

            return self.bayesian_search(param_space, objective, n_trials=n_trials)

