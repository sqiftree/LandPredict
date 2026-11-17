"""Audit factual source snapshots; matching transcription is not primary validation."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if not __debug__:
        raise RuntimeError('Jalankan audit tanpa python -O.')
    path = ROOT / 'data/harga_tanah_2020.csv'
    rows = list(csv.DictReader(path.open(encoding='utf-8')))
    snapshot = ROOT / 'data/sumber/lampiran_uns_index.txt'
    source = {}
    region = None
    for line in snapshot.read_text().splitlines():
        if not line.startswith('L'):
            continue
        cells = [c.strip() for c in line.split(': ', 1)[1].split('|') if c.strip()]
        if cells[0].startswith(('Kota ', 'Kabupaten ')):
            region = cells.pop(0)
        key = region, cells[0]
        if key in source:
            raise ValueError(f'Duplicate source key: {key}')
        source[key] = {
            'jumlah_fasum_regional': int(cells[3]),
            'jumlah_penduduk': int(cells[5]),
            'harga_tanah_rata_rata_rp_m2': int(cells[4].replace('Rp ', '').replace('.', '').split(',')[0]),
        }
    keys = [(r['kab_kota'], r['kecamatan']) for r in rows]
    assert len(keys) == len(set(keys)) == len(source) == 127
    assert set(keys) == set(source)
    checks = []
    for row, key in zip(rows, keys):
        for field, expected in source[key].items():
            checks.append(dict(kab_kota=key[0], kecamatan=key[1], kolom=field,
                               csv=int(row[field]), indeks_lampiran=expected,
                               cocok=int(row[field]) == expected))
    # Aziz et al. (2023), Table 3, printed p.149; '-' counted as zero.
    journal = {'Kota Surakarta': 25, 'Kabupaten Boyolali': 11,
               'Kabupaten Sukoharjo': 11, 'Kabupaten Karanganyar': 12,
               'Kabupaten Wonogiri': 8, 'Kabupaten Sragen': 11,
               'Kabupaten Klaten': 15}
    totals = [dict(kab_kota=k, fasum_csv=sum(int(r['jumlah_fasum_regional']) for r in rows if r['kab_kota'] == k),
                   fasum_artikel=v) for k, v in journal.items()]
    for row in totals:
        row['selisih_csv_minus_artikel'] = row['fasum_csv'] - row['fasum_artikel']
    # Table 1, p.145: urban + rural populations (a different source table).
    journal_population = {'Kota Surakarta': 576412, 'Kabupaten Boyolali': 1062713,
                          'Kabupaten Sukoharjo': 907587, 'Kabupaten Karanganyar': 931963,
                          'Kabupaten Wonogiri': 1043177, 'Kabupaten Sragen': 976951,
                          'Kabupaten Klaten': 1260506}
    populations = [dict(kab_kota=k, penduduk_csv=sum(int(r['jumlah_penduduk']) for r in rows if r['kab_kota'] == k),
                       penduduk_artikel=v) for k, v in journal_population.items()]
    for row in populations:
        row['selisih_csv_minus_artikel'] = row['penduduk_csv'] - row['penduduk_artikel']
    folder = ROOT / 'artifacts/data_audit'
    folder.mkdir(parents=True, exist_ok=True)
    for name, values in [('perbandingan_lampiran.csv', checks), ('perbandingan_fasum.csv', totals),
                         ('perbandingan_penduduk.csv', populations)]:
        with (folder / name).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(values)
    result = dict(tanggal_audit='2026-11-17', jumlah_kunci=len(keys),
                  sel_numerik_dibandingkan=len(checks), sel_cocok=sum(r['cocok'] for r in checks),
                  wilayah_fasum_berbeda=sum(r['selisih_csv_minus_artikel'] != 0 for r in totals),
                  wilayah_penduduk_berbeda=sum(r['selisih_csv_minus_artikel'] != 0 for r in populations),
                  jenis_bukti='Ekstraksi indeks publik Lampiran A; PDF asli belum diperoleh',
                  status='Transkripsi cocok; validitas primer dan perbedaan fasum belum terselesaikan',
                  sha256_csv=hashlib.sha256(path.read_bytes()).hexdigest(),
                  sha256_snapshot=hashlib.sha256(snapshot.read_bytes()).hexdigest())
    (folder / 'audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    assert all(r['cocok'] for r in checks), 'Transcription mismatch'


if __name__ == '__main__':
    main()
