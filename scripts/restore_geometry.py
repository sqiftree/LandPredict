"""Restore the exact archived BIG GeoJSON without network access."""
import gzip
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    archive = ROOT / 'data/jawa_tengah_big.geojson.gz'
    target = ROOT / 'data/jawa_tengah_big.geojson'
    manifest = json.loads((ROOT / 'data/geometri_manifest.json').read_text())
    if target.exists():
        with target.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != manifest['uncompressed_sha256']:
            raise ValueError('GeoJSON lokal berbeda dari arsip; tidak ditimpa secara otomatis.')
        print(f'GeoJSON sudah sesuai hash: {target}')
        return
    temporary = target.with_suffix('.geojson.tmp')
    with gzip.open(archive, 'rb') as source, temporary.open('wb') as destination:
        shutil.copyfileobj(source, destination)
    with temporary.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != manifest['uncompressed_sha256']:
        raise ValueError('Hash hasil dekompresi tidak sesuai manifest.')
    temporary.replace(target)
    print(f'GeoJSON dipulihkan dan hash cocok: {target}')


if __name__ == '__main__':
    main()
