"""
Model Persistence Framework

Handles saving and loading of trained models with metadata and versioning.
Supports all analysis model types (Fourier, HMM, DTW, Ensemble).
"""

import pickle
import json
import joblib
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class ModelPersistence:
    """
    Handle model saving and loading with metadata and versioning.

    Features:
    - Automatic versioning
    - Metadata tracking
    - Compression support
    - Model validation
    - Hash-based integrity checking
    """

    @staticmethod
    def save_model(
        model: Any,
        path: Path,
        metadata: Optional[Dict] = None,
        compress: bool = True
    ) -> Path:
        """
        Save model with metadata.

        Args:
            model: Model object to save
            path: Save path (without extension)
            metadata: Optional metadata dict
            compress: Whether to compress the model file

        Returns:
            Path to saved model file

        Example:
            >>> detector = FourierCyclicalDetector()
            >>> ModelPersistence.save_model(
            ...     detector,
            ...     Path("models/fourier_v1"),
            ...     metadata={"cycles_detected": 5, "confidence": 0.85}
            ... )
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Determine file extension
        ext = '.pkl.gz' if compress else '.pkl'
        model_path = path.with_suffix(ext)

        # Save model
        try:
            if compress:
                joblib.dump(model, model_path, compress=3)
            else:
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

            logger.info(f"Model saved to {model_path}")

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise

        # Calculate model hash for integrity
        model_hash = ModelPersistence._calculate_file_hash(model_path)

        # Prepare metadata
        if metadata is None:
            metadata = {}

        metadata.update({
            'saved_at': datetime.utcnow().isoformat(),
            'model_type': type(model).__name__,
            'model_path': str(model_path),
            'compressed': compress,
            'file_size_bytes': model_path.stat().st_size,
            'model_hash': model_hash
        })

        # Save metadata
        metadata_path = path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info(f"Metadata saved to {metadata_path}")

        return model_path

    @staticmethod
    def load_model(
        path: Path,
        verify_hash: bool = True
    ) -> Tuple[Any, Dict]:
        """
        Load model with metadata.

        Args:
            path: Path to model file (with or without extension)
            verify_hash: Whether to verify model file integrity

        Returns:
            (model, metadata) tuple

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If hash verification fails

        Example:
            >>> model, metadata = ModelPersistence.load_model(
            ...     Path("models/fourier_v1")
            ... )
            >>> print(f"Loaded {metadata['model_type']}")
        """
        path = Path(path)

        # Find model file (try both compressed and uncompressed)
        if path.suffix in ['.pkl', '.pkl.gz']:
            model_path = path
        else:
            if path.with_suffix('.pkl.gz').exists():
                model_path = path.with_suffix('.pkl.gz')
            elif path.with_suffix('.pkl').exists():
                model_path = path.with_suffix('.pkl')
            else:
                raise FileNotFoundError(f"Model file not found: {path}")

        # Load metadata
        metadata = {}
        metadata_path = path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            logger.warning(f"Metadata file not found: {metadata_path}")

        # Verify hash if requested
        if verify_hash and 'model_hash' in metadata:
            current_hash = ModelPersistence._calculate_file_hash(model_path)
            expected_hash = metadata['model_hash']

            if current_hash != expected_hash:
                raise ValueError(
                    f"Model file integrity check failed!\n"
                    f"Expected hash: {expected_hash}\n"
                    f"Current hash: {current_hash}\n"
                    f"Model file may be corrupted."
                )

            logger.debug("Model integrity verified")

        # Load model
        try:
            if model_path.suffix == '.gz':
                model = joblib.load(model_path)
            else:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)

            logger.info(f"Model loaded from {model_path}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

        # Update metadata with load info
        metadata['loaded_at'] = datetime.utcnow().isoformat()

        return model, metadata

    @staticmethod
    def list_models(directory: Path, model_type: Optional[str] = None) -> list[Dict]:
        """
        List all available models in a directory.

        Args:
            directory: Directory to search
            model_type: Optional filter by model type

        Returns:
            List of model metadata dicts

        Example:
            >>> models = ModelPersistence.list_models(
            ...     Path("models"),
            ...     model_type="FourierCyclicalDetector"
            ... )
            >>> for model in models:
            ...     print(f"{model['saved_at']}: {model['model_path']}")
        """
        directory = Path(directory)

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []

        models = []

        # Find all metadata files
        for metadata_path in directory.glob('**/*.json'):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

                # Filter by model type if specified
                if model_type and metadata.get('model_type') != model_type:
                    continue

                models.append(metadata)

            except Exception as e:
                logger.warning(f"Failed to load metadata from {metadata_path}: {e}")
                continue

        # Sort by saved_at (newest first)
        models.sort(key=lambda x: x.get('saved_at', ''), reverse=True)

        return models

    @staticmethod
    def delete_model(path: Path) -> bool:
        """
        Delete model and its metadata.

        Args:
            path: Path to model file

        Returns:
            True if deletion successful
        """
        path = Path(path)

        deleted = False

        # Delete model file
        for ext in ['.pkl', '.pkl.gz']:
            model_path = path.with_suffix(ext)
            if model_path.exists():
                model_path.unlink()
                logger.info(f"Deleted model: {model_path}")
                deleted = True

        # Delete metadata
        metadata_path = path.with_suffix('.json')
        if metadata_path.exists():
            metadata_path.unlink()
            logger.info(f"Deleted metadata: {metadata_path}")
            deleted = True

        return deleted

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity checking."""
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()


class ModelRegistry:
    """
    Centralized model registry for managing multiple models.

    Provides:
    - Model versioning
    - Active model management
    - Model comparison
    - Automatic model selection
    """

    def __init__(self, registry_path: Path):
        """
        Initialize model registry.

        Args:
            registry_path: Path to registry directory
        """
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

        self.index_path = self.registry_path / 'registry_index.json'
        self.index = self._load_index()

    def register_model(
        self,
        model: Any,
        name: str,
        version: str,
        metadata: Optional[Dict] = None,
        set_active: bool = True
    ) -> str:
        """
        Register a new model.

        Args:
            model: Model object
            name: Model name (e.g., "fourier_detector")
            version: Version string (e.g., "v1.0.0")
            metadata: Optional metadata
            set_active: Whether to set as active version

        Returns:
            Model ID
        """
        model_id = f"{name}_{version}"
        model_path = self.registry_path / name / version

        # Save model
        metadata = metadata or {}
        metadata.update({
            'model_id': model_id,
            'name': name,
            'version': version
        })

        ModelPersistence.save_model(model, model_path, metadata)

        # Update index
        if name not in self.index:
            self.index[name] = {
                'versions': {},
                'active_version': None
            }

        self.index[name]['versions'][version] = {
            'model_id': model_id,
            'path': str(model_path),
            'registered_at': datetime.utcnow().isoformat(),
            'metadata': metadata
        }

        if set_active:
            self.index[name]['active_version'] = version

        self._save_index()

        logger.info(f"Registered model: {model_id}")

        return model_id

    def get_model(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Tuple[Any, Dict]:
        """
        Get model by name and version.

        Args:
            name: Model name
            version: Version (None = active version)

        Returns:
            (model, metadata) tuple
        """
        if name not in self.index:
            raise ValueError(f"Model '{name}' not found in registry")

        # Use active version if not specified
        if version is None:
            version = self.index[name]['active_version']
            if version is None:
                raise ValueError(f"No active version set for model '{name}'")

        if version not in self.index[name]['versions']:
            raise ValueError(f"Version '{version}' not found for model '{name}'")

        model_path = Path(self.index[name]['versions'][version]['path'])

        return ModelPersistence.load_model(model_path)

    def set_active_version(self, name: str, version: str):
        """Set the active version for a model."""
        if name not in self.index:
            raise ValueError(f"Model '{name}' not found in registry")

        if version not in self.index[name]['versions']:
            raise ValueError(f"Version '{version}' not found for model '{name}'")

        self.index[name]['active_version'] = version
        self._save_index()

        logger.info(f"Set active version for '{name}' to '{version}'")

    def list_models(self) -> Dict:
        """List all registered models."""
        return self.index.copy()

    def _load_index(self) -> Dict:
        """Load registry index from disk."""
        if self.index_path.exists():
            with open(self.index_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """Save registry index to disk."""
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f, indent=2, default=str)
