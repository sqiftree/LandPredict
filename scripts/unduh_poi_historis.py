"""Unduh hanya anggota ZIP POI dari snapshot Geofabrik Indonesia 210101."""
import io
import re
import time
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

URL = 'https://download.geofabrik.de/asia/indonesia-210101-free.shp.zip'
ROOT = Path(__file__).resolve().parents[1]


class RemoteZip(io.RawIOBase):
    def __init__(self):
        with urlopen(Request(URL, headers={'Range': 'bytes=-22'}), timeout=90) as r:
            self.size = int(r.headers['Content-Range'].split('/')[-1])
        self.pos = 0

    def seek(self, offset, whence=0):
        self.pos = [0, self.pos, self.size][whence] + offset
        return self.pos

    def tell(self):
        return self.pos

    def read(self, size=-1):
        end = self.size if size < 0 else min(self.pos + size, self.size)
        if end <= self.pos:
            return b''
        interval = f'{self.pos}-{end-1}'
        for attempt in range(3):
            try:
                with urlopen(Request(URL, headers={'Range': 'bytes=' + interval}), timeout=120) as r:
                    if r.headers.get('Content-Range') != f'bytes {interval}/{self.size}':
                        raise IOError('Server tidak mengembalikan rentang ZIP yang diminta.')
                    data = r.read()
                    if len(data) != end-self.pos:
                        raise IOError('Respons ZIP terpotong.')
                break
            except OSError:
                if attempt == 2:
                    raise
                time.sleep(2)
        self.pos = end
        return data


def main():
    dest = ROOT / 'data/raw/osm_210101'
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RemoteZip()) as archive:
        selected = [m for m in archive.infolist() if re.fullmatch(r'gis_osm_pois(_a)?_free_1\.(dbf|shp|shx)', m.filename)]
        if len(selected) != 6:
            raise ValueError('Arsip POI tidak lengkap.')
        for m in selected:
            path = dest / m.filename
            print(m.filename, m.compress_size, flush=True)
            # One decompression read allows the remote reader to request large byte ranges.
            payload = archive.read(m)
            tmp = path.with_suffix(path.suffix + '.tmp')
            tmp.write_bytes(payload)
            tmp.replace(path)


if __name__ == '__main__':
    main()
