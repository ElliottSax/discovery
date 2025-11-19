"""Model registry for managing trained models."""

import os
import pickle
import joblib
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime
import logging
from app.core.ml_config import ml_settings

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Local model registry for caching and managing trained models.

    Complements MLFlow by providing fast local access to models.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize model registry.

        Args:
            cache_dir: Directory to cache models (default from settings)
        """
        self.cache_dir = Path(cache_dir or ml_settings.MODEL_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict] = {}

        logger.info(f"Model registry initialized at {self.cache_dir}")

    def save_model(
        self,
        model: Any,
        name: str,
        version: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save a model to the registry.

        Args:
            model: Model object to save
            name: Model name
            version: Model version (default: timestamp)
            metadata: Additional metadata

        Returns:
            Path to saved model
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        model_path = self.cache_dir / f"{name}_v{version}.pkl"

        try:
            # Save model
            if hasattr(model, 'save'):
                # Model has custom save method (e.g., Keras)
                model.save(str(model_path))
            else:
                # Use joblib for sklearn-like models
                joblib.dump(model, model_path)

            # Save metadata
            meta = {
                "name": name,
                "version": version,
                "saved_at": datetime.now().isoformat(),
                "model_type": type(model).__name__,
                "size_bytes": model_path.stat().st_size,
            }
            if metadata:
                meta.update(metadata)

            metadata_path = model_path.with_suffix('.meta.pkl')
            with open(metadata_path, 'wb') as f:
                pickle.dump(meta, f)

            # Cache in memory
            self.models[f"{name}:{version}"] = model
            self.model_metadata[f"{name}:{version}"] = meta

            logger.info(f"Saved model {name} v{version} to {model_path}")
            return str(model_path)

        except Exception as e:
            logger.error(f"Failed to save model {name}: {e}")
            raise

    def load_model(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[Any]:
        """
        Load a model from the registry.

        Args:
            name: Model name
            version: Model version (default: latest)

        Returns:
            Loaded model or None
        """
        # Check memory cache first
        cache_key = f"{name}:{version}" if version else None

        if cache_key and cache_key in self.models:
            logger.debug(f"Loaded {name} from memory cache")
            return self.models[cache_key]

        # Find model file
        if version:
            model_path = self.cache_dir / f"{name}_v{version}.pkl"
        else:
            # Get latest version
            model_files = list(self.cache_dir.glob(f"{name}_v*.pkl"))
            if not model_files:
                logger.warning(f"No model found for {name}")
                return None

            model_path = sorted(model_files, key=lambda p: p.stat().st_mtime)[-1]
            version = model_path.stem.split('_v')[1]

        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            return None

        try:
            # Load model
            model = joblib.load(model_path)

            # Load metadata
            metadata_path = model_path.with_suffix('.meta.pkl')
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    meta = pickle.load(f)
                self.model_metadata[f"{name}:{version}"] = meta

            # Cache in memory
            self.models[f"{name}:{version}"] = model

            logger.info(f"Loaded model {name} v{version}")
            return model

        except Exception as e:
            logger.error(f"Failed to load model {name}: {e}")
            return None

    def list_models(self, name: Optional[str] = None) -> list[Dict]:
        """
        List all models in the registry.

        Args:
            name: Optional name filter

        Returns:
            List of model metadata dictionaries
        """
        models = []

        pattern = f"{name}_v*.pkl" if name else "*_v*.pkl"
        model_files = sorted(
            self.cache_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for model_path in model_files:
            metadata_path = model_path.with_suffix('.meta.pkl')

            if metadata_path.exists():
                try:
                    with open(metadata_path, 'rb') as f:
                        meta = pickle.load(f)
                    models.append(meta)
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {model_path}: {e}")

        return models

    def delete_model(self, name: str, version: str) -> bool:
        """
        Delete a model from the registry.

        Args:
            name: Model name
            version: Model version

        Returns:
            True if successful
        """
        model_path = self.cache_dir / f"{name}_v{version}.pkl"
        metadata_path = model_path.with_suffix('.meta.pkl')

        try:
            if model_path.exists():
                model_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()

            # Remove from memory cache
            cache_key = f"{name}:{version}"
            if cache_key in self.models:
                del self.models[cache_key]
            if cache_key in self.model_metadata:
                del self.model_metadata[cache_key]

            logger.info(f"Deleted model {name} v{version}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete model {name} v{version}: {e}")
            return False

    def get_latest_version(self, name: str) -> Optional[str]:
        """
        Get the latest version of a model.

        Args:
            name: Model name

        Returns:
            Latest version string or None
        """
        model_files = list(self.cache_dir.glob(f"{name}_v*.pkl"))
        if not model_files:
            return None

        latest = sorted(model_files, key=lambda p: p.stat().st_mtime)[-1]
        version = latest.stem.split('_v')[1]

        return version

    def cleanup_old_versions(
        self,
        name: str,
        keep_n: int = 3
    ) -> int:
        """
        Clean up old model versions, keeping only the N most recent.

        Args:
            name: Model name
            keep_n: Number of versions to keep

        Returns:
            Number of versions deleted
        """
        model_files = sorted(
            self.cache_dir.glob(f"{name}_v*.pkl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        deleted = 0
        for model_path in model_files[keep_n:]:
            version = model_path.stem.split('_v')[1]
            if self.delete_model(name, version):
                deleted += 1

        logger.info(f"Cleaned up {deleted} old versions of {name}")
        return deleted

    def get_model_info(self, name: str, version: Optional[str] = None) -> Optional[Dict]:
        """
        Get metadata for a model.

        Args:
            name: Model name
            version: Model version (default: latest)

        Returns:
            Metadata dictionary or None
        """
        if version is None:
            version = self.get_latest_version(name)

        if version is None:
            return None

        cache_key = f"{name}:{version}"

        # Check memory cache
        if cache_key in self.model_metadata:
            return self.model_metadata[cache_key]

        # Load from disk
        metadata_path = self.cache_dir / f"{name}_v{version}.meta.pkl"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'rb') as f:
                    meta = pickle.load(f)
                self.model_metadata[cache_key] = meta
                return meta
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")

        return None
