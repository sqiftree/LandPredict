"""Load and validate the fixed 127-district, seven-region 2020 dataset."""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import haversine_distances

from .config import FEATURES, KEY, ROOT, TARGET


def load_observations(path: Path = ROOT / 'data/harga_tanah_2020.csv') -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = KEY + FEATURES + [TARGET, 'tahun']
    if not set(required).issubset(frame.columns):
        raise ValueError(f'Kolom wajib: {required}')
    if frame[KEY].isna().any().any() or any(frame[k].astype(str).str.strip().eq('').any() for k in KEY):
        raise ValueError('Kunci wilayah tidak boleh kosong.')
    if len(frame) != 127 or frame.duplicated(KEY).any() or frame.kab_kota.nunique() != 7:
        raise ValueError('Diperlukan 127 kunci unik dalam tujuh kabupaten/kota.')
    if not frame.tahun.eq(2020).all() or not np.isfinite(frame[FEATURES + [TARGET]]).all().all():
        raise ValueError('Tahun atau nilai input tidak valid.')
    return frame


def attach_coordinates(frame: pd.DataFrame, path: Path) -> tuple[pd.DataFrame, np.ndarray]:
    coords = pd.read_csv(path)
    required = KEY + ['lat', 'lon']
    if not set(required).issubset(coords.columns):
        raise ValueError(f'Kolom koordinat wajib: {required}')
    if len(coords) != 127 or coords[KEY].isna().any().any() or coords.duplicated(KEY).any():
        raise ValueError('Diperlukan 127 koordinat unik.')
    if set(map(tuple, coords[KEY].values)) != set(map(tuple, frame[KEY].values)):
        raise ValueError('Kunci koordinat tidak sama dengan dataset harga.')
    merged = frame.merge(coords[required], on=KEY, how='left', validate='one_to_one')
    if not (merged.lat.between(-90, 90) & merged.lon.between(-180, 180)).all():
        raise ValueError('Koordinat tidak lengkap atau di luar rentang.')
    distances = 6371.0088 * haversine_distances(np.radians(merged[['lat', 'lon']]))
    return merged, distances
