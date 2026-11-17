"""Audit factual source snapshots; matching transcription is not primary validation."""
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(root):
    if not __debug__:
        raise RuntimeError('Jalankan audit tanpa python -O.')
    path = root / 'data/harga_tanah_2020.csv'
    with path.open(encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    snapshot = root / 'data/sumber/lampiran_a_pdf.csv'
    manifest = json.loads((root / 'data/sumber/lampiran_a_pdf_manifest.json').read_text())
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == manifest['sha256_ekstraksi']
    pdf = root / manifest['file_lokal']
    if pdf.exists():
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == manifest['sha256_pdf']
    with snapshot.open(encoding='utf-8') as stream:
        extracted = list(csv.DictReader(stream))
    locations = {(r['kab_kota'], r['kecamatan']): r for r in extracted}
    fields = ['jumlah_fasum_regional', 'jumlah_penduduk', 'harga_tanah_rata_rata_rp_m2']
    source = {key: {field: int(row[field]) for field in fields} for key, row in locations.items()}
    assert len(extracted) == len(locations) == 127
    keys = [(r['kab_kota'], r['kecamatan']) for r in rows]
    assert len(keys) == len(set(keys)) == len(source) == 127
    assert set(keys) == set(source)
    checks = []
    for row, key in zip(rows, keys):
        for field, expected in source[key].items():
            checks.append(dict(kab_kota=key[0], kecamatan=key[1], kolom=field,
                               csv=int(row[field]), pdf_lampiran=expected,
                               cocok=int(row[field]) == expected))
    page_checks, corrected = [], []
    for row, key in zip(rows, keys):
        location = locations[key]
        page_checks.append(dict(kab_kota=key[0], kecamatan=key[1],
                                halaman_csv_lama=row['halaman_lampiran'],
                                halaman_pdf=int(location['halaman_pdf']), nomor_cetak=location['nomor_cetak'],
                                cocok=row['halaman_lampiran'] == location['nomor_cetak']))
        corrected.append({**row, 'halaman_lampiran': location['nomor_cetak'],
                          'halaman_pdf': int(location['halaman_pdf']),
                          'halaman_csv_lama': row['halaman_lampiran']})
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
    assert all(r['cocok'] for r in checks), 'Transcription mismatch'
    folder = root / 'artifacts/data_audit'
    folder.mkdir(parents=True, exist_ok=True)
    for name, values in [('perbandingan_lampiran.csv', checks), ('perbandingan_fasum.csv', totals),
                         ('perbandingan_penduduk.csv', populations), ('perbandingan_halaman.csv', page_checks),
                         ('dataset_2020_rujukan_terverifikasi.csv', corrected)]:
        with (folder / name).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(values)
    result = dict(tanggal_audit=datetime.now(ZoneInfo('Asia/Bangkok')).date().isoformat(),
                  status_kode='passed_transcription', pdf_lokal_diperiksa=pdf.exists(),
                  pemeriksaan_visual_terakhir='2026-11-17', jumlah_kunci=len(keys),
                  sel_numerik_dibandingkan=len(checks), sel_cocok=sum(r['cocok'] for r in checks),
                  wilayah_fasum_berbeda=sum(r['selisih_csv_minus_artikel'] != 0 for r in totals),
                  wilayah_penduduk_berbeda=sum(r['selisih_csv_minus_artikel'] != 0 for r in populations),
                  jenis_bukti='Perbandingan dengan ekstraksi PDF yang diarsipkan; pemeriksaan visual merupakan catatan audit sebelumnya',
                  rujukan_halaman_lama_berbeda=sum(not r['cocok'] for r in page_checks),
                  sha256_pdf=manifest['sha256_pdf'],
                  status=f"{sum(r['cocok'] for r in checks)}/{len(checks)} nilai cocok dengan ekstraksi PDF; {sum(not r['cocok'] for r in page_checks)} rujukan halaman lama berbeda; validitas primer dan perbedaan antarsumber belum terselesaikan",
                  sha256_csv=hashlib.sha256(path.read_bytes()).hexdigest(),
                  sha256_snapshot=hashlib.sha256(snapshot.read_bytes()).hexdigest())
    (folder / 'audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main(root=ROOT):
    """Fail closed: a failed recheck must not leave a successful audit status."""
    folder = root / 'artifacts/data_audit'
    folder.mkdir(parents=True, exist_ok=True)
    audit = folder / 'audit.json'
    audit.write_text(json.dumps({'status_kode': 'running'}))
    try:
        _run(root)
    except Exception as exc:
        audit.write_text(json.dumps({'status_kode': 'failed',
                                    'tanggal_audit': datetime.now(ZoneInfo('Asia/Bangkok')).date().isoformat(),
                                    'error': f'{type(exc).__name__}: {exc}'}, indent=2) + '\n')
        raise


if __name__ == '__main__':
    main()
