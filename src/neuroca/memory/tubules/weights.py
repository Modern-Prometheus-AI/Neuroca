"""
Weights Management for Neural Tubules

This module provides comprehensive functionality for managing, updating, and optimizing
weights within the neural tubules of the NeuroCognitive Architecture (NCA). Weights
represent the strength of connections between neural components and are critical for
information flow and memory formation.

The module implements various weight adjustment algorithms inspired by biological
neural processes including Hebbian learning, homeostatic plasticity, and decay dynamics.
It provides both low-level weight manipulation functions and higher-level weight
management strategies.

Usage Examples:
    # Create a new weight matrix
    weight_matrix = WeightMatrix(dimensions=(100, 100), init_strategy="normal")
    
    # Apply Hebbian learning
    weight_matrix.apply_hebbian_update(pre_activation, post_activation, learning_rate=0.01)
    
    # Normalize weights to prevent explosion
    weight_matrix.normalize(strategy="l2")
    
    # Save weights to persistent storage
    weight_matrix.save("memory_weights_v1.npz")

Classes:
    WeightMatrix: Core class for managing neural connection weights
    WeightInitializer: Factory class for different weight initialization strategies
    WeightOptimizer: Implements various weight optimization algorithms
    WeightConstraint: Enforces constraints on weights (sparsity, range, etc.)

Functions:
    load_weights: Load weights from storage
    save_weights: Save weights to storage
    merge_weight_matrices: Combine multiple weight matrices
"""

import logging
import time
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
from scipy import sparse

from neuroca.core.exceptions import ValidationError, WeightOperationError

# Configure logger
logger = logging.getLogger(__name__)


class InitStrategy(Enum):
    """Enumeration of available weight initialization strategies."""
    ZEROS = "zeros"
    ONES = "ones"
    RANDOM_UNIFORM = "random_uniform"
    RANDOM_NORMAL = "random_normal"
    GLOROT = "glorot"  # Also known as Xavier initialization
    HE = "he"  # He initialization for ReLU networks
    ORTHOGONAL = "orthogonal"
    SPARSE = "sparse"


class NormStrategy(Enum):
    """Enumeration of available weight normalization strategies."""
    L1 = "l1"
    L2 = "l2"
    MAX = "max"
    SOFTMAX = "softmax"
    MINMAX = "minmax"


class WeightInitializer:
    """
    Factory class for initializing weight matrices using various strategies.
    
    This class provides multiple initialization methods based on established
    neural network practices, adapted for the tubule memory system.
    """
    
    @staticmethod
    def initialize(shape: tuple[int, ...], strategy: Union[str, InitStrategy], 
                   **kwargs) -> np.ndarray:
        """
        Initialize a weight matrix using the specified strategy.
        
        Args:
            shape: Dimensions of the weight matrix
            strategy: Initialization strategy to use
            **kwargs: Additional parameters specific to the chosen strategy
                - scale: Scale factor for random distributions
                - mean: Mean for normal distribution
                - sparsity: Sparsity factor for sparse initialization
                - seed: Random seed for reproducibility
        
        Returns:
            Initialized weight matrix as numpy array
        
        Raises:
            ValidationError: If invalid parameters are provided
            ValueError: If an unknown strategy is specified
        """
        if isinstance(strategy, str):
            try:
                strategy = InitStrategy(strategy)
            except ValueError:
                valid_strategies = [s.value for s in InitStrategy]
                raise ValueError(f"Unknown initialization strategy: {strategy}. "
                                f"Valid options are: {valid_strategies}")
        
        # Extract common parameters with defaults
        scale = kwargs.get('scale', 0.01)
        mean = kwargs.get('mean', 0.0)
        seed = kwargs.get('seed', None)
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize based on strategy
        if strategy == InitStrategy.ZEROS:
            return np.zeros(shape)
        
        elif strategy == InitStrategy.ONES:
            return np.ones(shape)
        
        elif strategy == InitStrategy.RANDOM_UNIFORM:
            low = kwargs.get('low', -scale)
            high = kwargs.get('high', scale)
            return np.random.uniform(low=low, high=high, size=shape)
        
        elif strategy == InitStrategy.RANDOM_NORMAL:
            return np.random.normal(loc=mean, scale=scale, size=shape)
        
        elif strategy == InitStrategy.GLOROT:
            # Glorot/Xavier initialization
            fan_in = shape[0] if len(shape) >= 1 else 1
            fan_out = shape[1] if len(shape) >= 2 else 1
            limit = np.sqrt(6 / (fan_in + fan_out))
            return np.random.uniform(-limit, limit, shape)
        
        elif strategy == InitStrategy.HE:
            # He initialization
            fan_in = shape[0] if len(shape) >= 1 else 1
            std = np.sqrt(2 / fan_in)
            return np.random.normal(0, std, shape)
        
        elif strategy == InitStrategy.ORTHOGONAL:
            # Orthogonal initialization (only for 2D matrices)
            if len(shape) != 2:
                raise ValidationError("Orthogonal initialization requires a 2D matrix")
            
            flat_shape = (shape[0], np.prod(shape[1:]))
            a = np.random.normal(0.0, 1.0, flat_shape)
            u, _, v = np.linalg.svd(a, full_matrices=False)
            q = u if u.shape == flat_shape else v
            q = q.reshape(shape)
            return scale * q
        
        elif strategy == InitStrategy.SPARSE:
            # Sparse initialization
            sparsity = kwargs.get('sparsity', 0.9)
            if not 0 <= sparsity < 1:
                raise ValidationError("Sparsity must be between 0 and 1")
                
            weights = np.random.normal(0, scale, shape)
            mask = np.random.binomial(1, 1-sparsity, shape)
            return weights * mask
        
        else:
            valid_strategies = [s.value for s in InitStrategy]
            raise ValueError(f"Unknown initialization strategy: {strategy}. "
                           f"Valid options are: {valid_strategies}")


class WeightConstraint:
    """
    Applies constraints to weight matrices to enforce desired properties.
    
    These constraints help maintain stability, prevent exploding/vanishing gradients,
    and enforce specific properties like sparsity or non-negativity.
    """
    
    @staticmethod
    def apply_constraint(weights: np.ndarray, constraint_type: str, **kwargs) -> np.ndarray:
        """
        Apply a constraint to the weight matrix.
        
        Args:
            weights: The weight matrix to constrain
            constraint_type: Type of constraint to apply
            **kwargs: Additional parameters for the constraint
        
        Returns:
            Constrained weight matrix
        
        Raises:
            ValueError: If an unknown constraint type is specified
        """
        if constraint_type == "non_negative":
            return np.maximum(weights, 0)
        
        elif constraint_type == "unit_norm":
            axis = kwargs.get('axis', None)
            norm = np.linalg.norm(weights, axis=axis, keepdims=True)
            # Avoid division by zero
            norm = np.maximum(norm, np.finfo(weights.dtype).eps)
            return weights / norm
        
        elif constraint_type == "max_norm":
            max_value = kwargs.get('max_value', 1.0)
            axis = kwargs.get('axis', None)
            norm = np.linalg.norm(weights, axis=axis, keepdims=True)
            desired_norm = np.minimum(norm, max_value)
            # Avoid division by zero
            norm = np.maximum(norm, np.finfo(weights.dtype).eps)
            return weights * (desired_norm / norm)
        
        elif constraint_type == "min_max":
            min_value = kwargs.get('min_value', 0.0)
            max_value = kwargs.get('max_value', 1.0)
            return np.clip(weights, min_value, max_value)
        
        elif constraint_type == "sparsity":
            sparsity = kwargs.get('sparsity', 0.9)
            if not 0 <= sparsity < 1:
                raise ValidationError("Sparsity must be between 0 and 1")
            
            # Keep only the top (1-sparsity)% of weights by magnitude
            k = int(np.round((1 - sparsity) * weights.size))
            if k == 0:
                return np.zeros_like(weights)
                
            flat_weights = weights.flatten()
            threshold = np.sort(np.abs(flat_weights))[-k]
            mask = np.abs(weights) >= threshold
            return weights * mask
        
        else:
            raise ValueError(f"Unknown constraint type: {constraint_type}")


class WeightMatrix:
    """
    Core class for managing neural connection weights in tubules.
    
    This class provides comprehensive functionality for initializing, updating,
    normalizing, and constraining weight matrices, as well as persistence operations.
    It supports both dense and sparse representations for memory efficiency.
    """
    
    def __init__(self, 
                 dimensions: tuple[int, ...], 
                 init_strategy: Union[str, InitStrategy] = "zeros",
                 use_sparse: bool = False,
                 name: Optional[str] = None,
                 **init_kwargs):
        """
        Initialize a new weight matrix.
        
        Args:
            dimensions: Shape of the weight matrix
            init_strategy: Strategy for initializing weights
            use_sparse: Whether to use sparse matrix representation
            name: Optional name for the weight matrix (for logging/debugging)
            **init_kwargs: Additional parameters for initialization
        
        Raises:
            ValidationError: If invalid parameters are provided
        """
        self.dimensions = dimensions
        self.name = name or f"weights_{int(time.time())}"
        self.use_sparse = use_sparse
        self.creation_time = time.time()
        self.last_update_time = self.creation_time
        self.update_count = 0
        
        # Initialize weights
        logger.debug(f"Initializing weight matrix '{self.name}' with shape {dimensions} "
                    f"using strategy '{init_strategy}'")
        
        try:
            dense_weights = WeightInitializer.initialize(
                dimensions, init_strategy, **init_kwargs)
            
            if use_sparse:
                self.weights = sparse.csr_matrix(dense_weights)
            else:
                self.weights = dense_weights
                
        except Exception as e:
            logger.error(f"Failed to initialize weights: {str(e)}")
            raise ValidationError(f"Weight initialization failed: {str(e)}") from e
        
        # Metadata for tracking weight statistics
        self._update_metadata()
        logger.info(f"Created weight matrix '{self.name}' with shape {dimensions}")
    
    def _update_metadata(self):
        """Update internal metadata about the weight matrix."""
        if self.use_sparse:
            self.sparsity = 1.0 - (self.weights.nnz / np.prod(self.dimensions))
            self.min_value = self.weights.data.min() if self.weights.nnz > 0 else 0
            self.max_value = self.weights.data.max() if self.weights.nnz > 0 else 0
            self.mean_value = self.weights.data.mean() if self.weights.nnz > 0 else 0
            self.std_value = self.weights.data.std() if self.weights.nnz > 0 else 0
        else:
            self.sparsity = np.mean(self.weights == 0)
            self.min_value = np.min(self.weights)
            self.max_value = np.max(self.weights)
            self.mean_value = np.mean(self.weights)
            self.std_value = np.std(self.weights)
        
        self.last_update_time = time.time()
    
    def get_dense(self) -> np.ndarray:
        """
        Get a dense representation of the weights.
        
        Returns:
            Dense numpy array of weights
        """
        if self.use_sparse:
            return self.weights.toarray()
        return self.weights
    
    def get_sparse(self) -> sparse.csr_matrix:
        """
        Get a sparse representation of the weights.
        
        Returns:
            Sparse matrix of weights
        """
        if not self.use_sparse:
            return sparse.csr_matrix(self.weights)
        return self.weights
    
    def normalize(self, strategy: Union[str, NormStrategy] = "l2", axis: Optional[int] = None) -> None:
        """
        Normalize the weight matrix using the specified strategy.
        
        Args:
            strategy: Normalization strategy to use
            axis: Axis along which to normalize (None for global normalization)
        
        Raises:
            ValueError: If an unknown normalization strategy is specified
        """
        if isinstance(strategy, str):
            try:
                strategy = NormStrategy(strategy)
            except ValueError:
                valid_strategies = [s.value for s in NormStrategy]
                raise ValueError(f"Unknown normalization strategy: {strategy}. "
                               f"Valid options are: {valid_strategies}")
        
        # Convert to dense for normalization operations
        dense_weights = self.get_dense()
        
        # Apply normalization
        if strategy == NormStrategy.L1:
            norm = np.sum(np.abs(dense_weights), axis=axis, keepdims=True)
            # Avoid division by zero
            norm = np.maximum(norm, np.finfo(dense_weights.dtype).eps)
            dense_weights = dense_weights / norm
            
        elif strategy == NormStrategy.L2:
            norm = np.sqrt(np.sum(np.square(dense_weights), axis=axis, keepdims=True))
            # Avoid division by zero
            norm = np.maximum(norm, np.finfo(dense_weights.dtype).eps)
            dense_weights = dense_weights / norm
            
        elif strategy == NormStrategy.MAX:
            norm = np.max(np.abs(dense_weights), axis=axis, keepdims=True)
            # Avoid division by zero
            norm = np.maximum(norm, np.finfo(dense_weights.dtype).eps)
            dense_weights = dense_weights / norm
            
        elif strategy == NormStrategy.SOFTMAX:
            if axis is None:
                # Global softmax
                exp_weights = np.exp(dense_weights - np.max(dense_weights))
                dense_weights = exp_weights / np.sum(exp_weights)
            else:
                # Softmax along specified axis
                max_weights = np.max(dense_weights, axis=axis, keepdims=True)
                exp_weights = np.exp(dense_weights - max_weights)
                sum_weights = np.sum(exp_weights, axis=axis, keepdims=True)
                dense_weights = exp_weights / sum_weights
                
        elif strategy == NormStrategy.MINMAX:
            min_val = np.min(dense_weights, axis=axis, keepdims=True)
            max_val = np.max(dense_weights, axis=axis, keepdims=True)
            range_val = max_val - min_val
            # Avoid division by zero
            range_val = np.maximum(range_val, np.finfo(dense_weights.dtype).eps)
            dense_weights = (dense_weights - min_val) / range_val
            
        else:
            valid_strategies = [s.value for s in NormStrategy]
            raise ValueError(f"Unknown normalization strategy: {strategy}. "
                           f"Valid options are: {valid_strategies}")
        
        # Update weights with normalized values
        if self.use_sparse:
            self.weights = sparse.csr_matrix(dense_weights)
        else:
            self.weights = dense_weights
        
        self.update_count += 1
        self._update_metadata()
        logger.debug(f"Normalized weights '{self.name}' using {strategy.value} strategy")
    
    def apply_constraint(self, constraint_type: str, **kwargs) -> None:
        """
        Apply a constraint to the weight matrix.
        
        Args:
            constraint_type: Type of constraint to apply
            **kwargs: Additional parameters for the constraint
        """
        try:
            dense_weights = self.get_dense()
            constrained_weights = WeightConstraint.apply_constraint(
                dense_weights, constraint_type, **kwargs)
            
            if self.use_sparse:
                self.weights = sparse.csr_matrix(constrained_weights)
            else:
                self.weights = constrained_weights
                
            self.update_count += 1
            self._update_metadata()
            logger.debug(f"Applied {constraint_type} constraint to weights '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to apply constraint: {str(e)}")
            raise WeightOperationError(f"Constraint application failed: {str(e)}") from e
    
    def apply_hebbian_update(self, 
                            pre_activation: np.ndarray, 
                            post_activation: np.ndarray,
                            learning_rate: float = 0.01,
                            decay_rate: float = 0.0) -> None:
        """
        Apply Hebbian learning update to the weight matrix.
        
        Implements the principle "neurons that fire together, wire together" by
        strengthening connections between co-active neurons.
        
        Args:
            pre_activation: Activation values of pre-synaptic neurons
            post_activation: Activation values of post-synaptic neurons
            learning_rate: Rate of weight updates
            decay_rate: Weight decay factor for regularization
        
        Raises:
            ValidationError: If input dimensions don't match weight matrix
        """
        # Validate input dimensions
        if pre_activation.shape[0] != self.dimensions[0]:
            raise ValidationError(
                f"Pre-activation dimension {pre_activation.shape[0]} doesn't match "
                f"weight matrix first dimension {self.dimensions[0]}")
        
        if post_activation.shape[0] != self.dimensions[1]:
            raise ValidationError(
                f"Post-activation dimension {post_activation.shape[0]} doesn't match "
                f"weight matrix second dimension {self.dimensions[1]}")
        
        try:
            # Reshape for outer product
            pre = pre_activation.reshape(-1, 1) if pre_activation.ndim == 1 else pre_activation
            post = post_activation.reshape(1, -1) if post_activation.ndim == 1 else post_activation
            
            # Compute Hebbian update
            delta_w = learning_rate * np.outer(pre, post)
            
            # Apply update with optional weight decay
            if self.use_sparse:
                # For sparse matrices, convert to dense, update, then back to sparse
                dense_weights = self.weights.toarray()
                dense_weights = (1 - decay_rate) * dense_weights + delta_w
                self.weights = sparse.csr_matrix(dense_weights)
            else:
                self.weights = (1 - decay_rate) * self.weights + delta_w
            
            self.update_count += 1
            self._update_metadata()
            logger.debug(f"Applied Hebbian update to weights '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to apply Hebbian update: {str(e)}")
            raise WeightOperationError(f"Hebbian update failed: {str(e)}") from e
    
    def apply_oja_update(self,
                        pre_activation: np.ndarray,
                        post_activation: np.ndarray,
                        learning_rate: float = 0.01) -> None:
        """
        Apply Oja's learning rule update to the weight matrix.
        
        Oja's rule is a modified Hebbian rule that includes a normalization term
        to prevent unbounded weight growth.
        
        Args:
            pre_activation: Activation values of pre-synaptic neurons
            post_activation: Activation values of post-synaptic neurons
            learning_rate: Rate of weight updates
        
        Raises:
            ValidationError: If input dimensions don't match weight matrix
        """
        # Validate input dimensions
        if pre_activation.shape[0] != self.dimensions[0]:
            raise ValidationError(
                f"Pre-activation dimension {pre_activation.shape[0]} doesn't match "
                f"weight matrix first dimension {self.dimensions[0]}")
        
        if post_activation.shape[0] != self.dimensions[1]:
            raise ValidationError(
                f"Post-activation dimension {post_activation.shape[0]} doesn't match "
                f"weight matrix second dimension {self.dimensions[1]}")
        
        try:
            # Reshape for outer product
            pre = pre_activation.reshape(-1, 1) if pre_activation.ndim == 1 else pre_activation
            post = post_activation.reshape(1, -1) if post_activation.ndim == 1 else post_activation
            
            # Get current weights in dense format for the update
            dense_weights = self.get_dense()
            
            # Compute Oja's rule update
            # Δw = η * (y * x - y^2 * w)
            hebbian_term = np.outer(pre, post)
            normalization_term = np.outer(pre, np.square(post)) * dense_weights
            delta_w = learning_rate * (hebbian_term - normalization_term)
            
            # Apply update
            dense_weights += delta_w
            
            # Update weights
            if self.use_sparse:
                self.weights = sparse.csr_matrix(dense_weights)
            else:
                self.weights = dense_weights
            
            self.update_count += 1
            self._update_metadata()
            logger.debug(f"Applied Oja's rule update to weights '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to apply Oja's rule update: {str(e)}")
            raise WeightOperationError(f"Oja's rule update failed: {str(e)}") from e
    
    def apply_decay(self, decay_rate: float = 0.001) -> None:
        """
        Apply exponential decay to all weights.
        
        This simulates the natural forgetting process in biological memory systems.
        
        Args:
            decay_rate: Rate of decay (0 to 1)
        
        Raises:
            ValidationError: If decay_rate is not between 0 and 1
        """
        if not 0 <= decay_rate <= 1:
            raise ValidationError("Decay rate must be between 0 and 1")
        
        try:
            if self.use_sparse:
                # For sparse matrices, we can directly multiply the data array
                self.weights.data *= (1 - decay_rate)
                # Remove zero entries to maintain sparsity
                self.weights.eliminate_zeros()
            else:
                self.weights *= (1 - decay_rate)
            
            self.update_count += 1
            self._update_metadata()
            logger.debug(f"Applied decay with rate {decay_rate} to weights '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to apply decay: {str(e)}")
            raise WeightOperationError(f"Weight decay failed: {str(e)}") from e
    
    def save(self, filepath: Union[str, Path], compress: bool = True) -> None:
        """
        Save the weight matrix to a file.
        
        Args:
            filepath: Path where to save the weights
            compress: Whether to compress the saved file
        
        Raises:
            IOError: If saving fails
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Prepare metadata
            metadata = {
                'name': self.name,
                'dimensions': self.dimensions,
                'use_sparse': self.use_sparse,
                'creation_time': self.creation_time,
                'last_update_time': self.last_update_time,
                'update_count': self.update_count,
                'sparsity': self.sparsity,
                'min_value': float(self.min_value),
                'max_value': float(self.max_value),
                'mean_value': float(self.mean_value),
                'std_value': float(self.std_value)
            }
            
            # Save weights and metadata
            if self.use_sparse:
                sparse.save_npz(filepath, self.weights, compressed=compress)
                # Save metadata separately
                np.savez(f"{filepath}_metadata", **metadata)
            else:
                np.savez_compressed(filepath, weights=self.weights, **metadata) if compress else \
                np.savez(filepath, weights=self.weights, **metadata)
            
            logger.info(f"Saved weight matrix '{self.name}' to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save weights to {filepath}: {str(e)}")
            raise OSError(f"Failed to save weights: {str(e)}") from e
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> 'WeightMatrix':
        """
        Load a weight matrix from a file.
        
        Args:
            filepath: Path to the saved weights file
        
        Returns:
            Loaded WeightMatrix instance
        
        Raises:
            IOError: If loading fails
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise OSError(f"Weight file not found: {filepath}")
        
        try:
            # Check if this is a sparse matrix
            is_sparse = filepath.suffix == '.npz' and not filepath.stem.endswith('_metadata')
            
            if is_sparse:
                # Load sparse matrix
                weights = sparse.load_npz(filepath)
                
                # Load metadata from companion file
                metadata_path = Path(f"{filepath}_metadata.npz")
                if metadata_path.exists():
                    metadata = dict(np.load(metadata_path, allow_pickle=True))
                else:
                    # Create default metadata if not found
                    metadata = {
                        'name': filepath.stem,
                        'dimensions': weights.shape,
                        'use_sparse': True,
                        'creation_time': time.time(),
                        'last_update_time': time.time(),
                        'update_count': 0
                    }
                
                # Create instance
                instance = cls.__new__(cls)
                instance.weights = weights
                instance.dimensions = tuple(metadata.get('dimensions', weights.shape))
                instance.name = metadata.get('name', filepath.stem)
                instance.use_sparse = True
                instance.creation_time = metadata.get('creation_time', time.time())
                instance.last_update_time = metadata.get('last_update_time', time.time())
                instance.update_count = metadata.get('update_count', 0)
                instance._update_metadata()
                
            else:
                # Load dense matrix
                data = np.load(filepath, allow_pickle=True)
                weights = data['weights']
                
                # Create instance
                instance = cls.__new__(cls)
                instance.weights = weights
                instance.dimensions = tuple(data.get('dimensions', weights.shape))
                instance.name = str(data.get('name', filepath.stem))
                instance.use_sparse = bool(data.get('use_sparse', False))
                instance.creation_time = float(data.get('creation_time', time.time()))
                instance.last_update_time = float(data.get('last_update_time', time.time()))
                instance.update_count = int(data.get('update_count', 0))
                instance._update_metadata()
            
            logger.info(f"Loaded weight matrix '{instance.name}' from {filepath}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load weights from {filepath}: {str(e)}")
            raise OSError(f"Failed to load weights: {str(e)}") from e
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get comprehensive statistics about the weight matrix.
        
        Returns:
            Dictionary of weight statistics
        """
        stats = {
            'name': self.name,
            'dimensions': self.dimensions,
            'size': np.prod(self.dimensions),
            'sparsity': self.sparsity,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'mean_value': self.mean_value,
            'std_value': self.std_value,
            'update_count': self.update_count,
            'age_seconds': time.time() - self.creation_time,
            'last_update_seconds_ago': time.time() - self.last_update_time
        }
        
        # Add memory usage information
        if self.use_sparse:
            stats['memory_bytes'] = self.weights.data.nbytes + self.weights.indptr.nbytes + self.weights.indices.nbytes
        else:
            stats['memory_bytes'] = self.weights.nbytes
        
        return stats
    
    def __repr__(self) -> str:
        """String representation of the weight matrix."""
        return (f"WeightMatrix(name='{self.name}', dimensions={self.dimensions}, "
                f"use_sparse={self.use_sparse}, updates={self.update_count})")


def merge_weight_matrices(matrices: list[WeightMatrix], 
                         strategy: str = "average") -> WeightMatrix:
    """
    Merge multiple weight matrices into a single matrix.
    
    Args:
        matrices: List of weight matrices to merge
        strategy: Merging strategy ('average', 'sum', 'max', 'min', 'weighted_average')
    
    Returns:
        New merged weight matrix
    
    Raises:
        ValidationError: If matrices have incompatible dimensions
        ValueError: If an unknown merge strategy is specified
    """
    if not matrices:
        raise ValidationError("No weight matrices provided for merging")
    
    # Check that all matrices have the same dimensions
    first_dims = matrices[0].dimensions
    for i, matrix in enumerate(matrices[1:], 1):
        if matrix.dimensions != first_dims:
            raise ValidationError(
                f"Matrix {i} has dimensions {matrix.dimensions}, "
                f"which is incompatible with {first_dims}")
    
    # Convert all matrices to dense for merging
    dense_matrices = [m.get_dense() for m in matrices]
    
    # Apply merging strategy
    if strategy == "average":
        merged_weights = np.mean(dense_matrices, axis=0)
    
    elif strategy == "sum":
        merged_weights = np.sum(dense_matrices, axis=0)
    
    elif strategy == "max":
        merged_weights = np.maximum.reduce(dense_matrices)
    
    elif strategy == "min":
        merged_weights = np.minimum.reduce(dense_matrices)
    
    elif strategy == "weighted_average":
        # Default to equal weights if not provided
        weights = [1.0 / len(matrices)] * len(matrices)
        merged_weights = np.average(dense_matrices, axis=0, weights=weights)
    
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")
    
    # Create new weight matrix with merged weights
    use_sparse = any(m.use_sparse for m in matrices)
    result = WeightMatrix(
        dimensions=first_dims,
        init_strategy="zeros",  # Will be overwritten
        use_sparse=use_sparse,
        name=f"merged_{strategy}_{int(time.time())}"
    )
    
    # Set the merged weights
    if use_sparse:
        result.weights = sparse.csr_matrix(merged_weights)
    else:
        result.weights = merged_weights
    
    result._update_metadata()
    logger.info(f"Merged {len(matrices)} weight matrices using '{strategy}' strategy")
    
    return result


def load_weights(filepath: Union[str, Path]) -> WeightMatrix:
    """
    Load weights from a file.
    
    This is a convenience wrapper around WeightMatrix.load.
    
    Args:
        filepath: Path to the saved weights file
    
    Returns:
        Loaded WeightMatrix instance
    """
    return WeightMatrix.load(filepath)


def save_weights(weights: WeightMatrix, filepath: Union[str, Path], compress: bool = True) -> None:
    """
    Save weights to a file.
    
    This is a convenience wrapper around WeightMatrix.save.
    
    Args:
        weights: WeightMatrix instance to save
        filepath: Path where to save the weights
        compress: Whether to compress the saved file
    """
    weights.save(filepath, compress=compress)