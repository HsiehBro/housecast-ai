import os
import json
import logging
import platform
import shutil
import joblib
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _link_or_copy(src, dst):
    """Create symlink on Unix, copy on Windows (symlink requires admin)."""
    if os.path.exists(dst):
        os.remove(dst)
    if platform.system() == "Windows":
        shutil.copy2(src, dst)
    else:
        os.symlink(src, dst)


class ModelVersionManager:
    def __init__(self, models_dir: str = "ml/models"):
        self.models_dir = models_dir
        self.versions_dir = os.path.join(models_dir, "versions")
        self.metadata_file = os.path.join(models_dir, "model_metadata.json")
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure model directories exist"""
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.versions_dir, exist_ok=True)

    def save_model_with_version(self, model: Any, model_type: str = "xgboost",
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save model with versioning"""
        if metadata is None:
            metadata = {}

        # Generate version info
        version_info = {
            "version": self._get_next_version(),
            "model_type": model_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "model_hash": self._calculate_model_hash(model)
        }

        # Save model with version name
        model_filename = f"house_price_v{version_info['version']}.pkl"
        model_path = os.path.join(self.versions_dir, model_filename)

        # Save the model
        joblib.dump(model, model_path)

        # Update metadata
        self._update_metadata(version_info)

        # Create current symlink/copy
        current_path = os.path.join(self.models_dir, "house_price.pkl")
        _link_or_copy(model_path, current_path)

        return version_info["version"]

    def _get_next_version(self) -> int:
        """Get next version number"""
        if not os.path.exists(self.metadata_file):
            return 1

        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                versions = metadata.get("versions", [])
                if versions:
                    return versions[-1]["version"] + 1
                return 1
        except Exception:
            return 1

    def _calculate_model_hash(self, model: Any) -> str:
        """Calculate hash of the model"""
        model_bytes = joblib.dumps(model)
        return hashlib.md5(model_bytes).hexdigest()

    def _update_metadata(self, version_info: Dict[str, Any]):
        """Update model metadata file"""
        metadata = {"versions": []}

        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
            except Exception:
                pass

        metadata["versions"].append(version_info)

        # Keep only last 10 versions
        if len(metadata["versions"]) > 10:
            metadata["versions"] = metadata["versions"][-10:]

        # Sort by version
        metadata["versions"].sort(key=lambda x: x["version"])

        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def get_current_version(self) -> Optional[Dict[str, Any]]:
        """Get current model version info"""
        if not os.path.exists(self.metadata_file):
            return None

        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                versions = metadata.get("versions", [])
                if versions:
                    return versions[-1]
        except Exception:
            pass

        return None

    def get_version_info(self, version: int) -> Optional[Dict[str, Any]]:
        """Get specific version info"""
        if not os.path.exists(self.metadata_file):
            return None

        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                for version_info in metadata.get("versions", []):
                    if version_info["version"] == version:
                        return version_info
        except Exception:
            pass

        return None

    def list_versions(self) -> list:
        """List all available versions"""
        if not os.path.exists(self.metadata_file):
            return []

        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                return metadata.get("versions", [])
        except Exception:
            return []

    def rollback_to_version(self, version: int) -> bool:
        """Rollback to specific version"""
        version_info = self.get_version_info(version)
        if not version_info:
            return False

        model_filename = f"house_price_v{version}.pkl"
        model_path = os.path.join(self.versions_dir, model_filename)

        if not os.path.exists(model_path):
            return False

        # Update current symlink/copy
        current_path = os.path.join(self.models_dir, "house_price.pkl")
        _link_or_copy(model_path, current_path)

        return True

    def delete_version(self, version: int) -> bool:
        """Delete a specific version"""
        version_info = self.get_version_info(version)
        if not version_info:
            return False

        model_filename = f"house_price_v{version}.pkl"
        model_path = os.path.join(self.versions_dir, model_filename)

        if os.path.exists(model_path):
            os.remove(model_path)

        # Update metadata
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)

                # Remove version from list
                metadata["versions"] = [v for v in metadata.get("versions", [])
                                     if v["version"] != version]

                with open(self.metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

                return True
            except Exception:
                logger.warning("Failed to update metadata after deleting version %s", version)

        return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get overall model information"""
        current_version = self.get_current_version()
        versions = self.list_versions()

        return {
            "current_version": current_version["version"] if current_version else None,
            "total_versions": len(versions),
            "latest_version": versions[-1]["version"] if versions else None,
            "oldest_version": versions[0]["version"] if versions else None,
            "versions": versions
        }

# Global instance
version_manager = ModelVersionManager()
