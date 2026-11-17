"""Hashes and execution metadata for reproducible research artifacts."""
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

from .config import FEATURES, ROOT


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def new_audit(coordinates: Path | None, candidates: dict) -> dict:
    return {
        'status': 'running',
        'python': platform.python_version(),
        'versions': {p: version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'scipy', 'threadpoolctl']},
        'data_sha256': sha256(ROOT / 'data/harga_tanah_2020.csv'),
        'coordinates_sha256': sha256(coordinates) if coordinates else None,
        'code_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / 'tanah').glob('*.py'))},
        'features': FEATURES,
        'candidate_parameters': candidates,
        'kernel': 'Gaussian' if coordinates else None,
        'distance_unit': 'km' if coordinates else None,
        'geometry_2020_status': 'unverified_historical_boundaries' if coordinates else None,
        'inner_selection': 'pooled MAE of leave-one-region-out predictions on outer training data',
        'outer_folds': [], 'inner_scores': [], 'singular_failures': [],
    }


def save_audit(folder: Path, audit: dict) -> None:
    temporary = folder / 'audit.json.tmp'
    temporary.write_text(json.dumps(audit, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(folder / 'audit.json')
