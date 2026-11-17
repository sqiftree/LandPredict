"""Extract only factual Appendix A rows from the user-supplied PDF (pypdf 5.9.0)."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r'^(.+?)\s+([\d,]+)\s+([\d,]+)\s+(\d+)\s+Rp\s+([\d.]+),00\s+(\d+)\s+([\d,]+)\s*$')


def extract(pdf):
    from pypdf import PdfReader
    import pypdf
    reader = PdfReader(pdf)
    rows, region = [], None
    pages = []
    for number, page in enumerate(reader.pages[:4], 1):
        text = page.extract_text()
        footer = re.findall(r'^([AB]-\d+)\s*$', text, re.MULTILINE)
        if len(footer) != 1:
            raise ValueError(f'Ambiguous footer on PDF page {number}')
        appendix_a = text.split('Lampiran B.')[0]
        before = len(rows)
        for line in appendix_a.splitlines():
            line = line.strip()
            if line.startswith(('Kota Surakarta', 'Kabupaten ')):
                region = line
            match = ROW.fullmatch(line)
            if not match:
                if 'Rp ' in line:
                    raise ValueError(f'Unparsed price row: {line}')
                continue
            name, area, built, facilities, price, population, density = match.groups()
            if region is None:
                raise ValueError('Missing region')
            rows.append(dict(tahun=2020, kab_kota=region, kecamatan=name,
                             jumlah_fasum_regional=int(facilities), jumlah_penduduk=int(population),
                             harga_tanah_rata_rata_rp_m2=int(price.replace('.', '')),
                             halaman_pdf=number, nomor_cetak=footer[0],
                             luas_kecamatan_teks=area, luas_terbangun_teks=built,
                             kepadatan_terbangun_teks=density))
        pages.append(dict(halaman_pdf=number, nomor_cetak=footer[0], baris=len(rows)-before))
    if len(rows) != 127 or len({(r['kab_kota'], r['kecamatan']) for r in rows}) != 127:
        raise ValueError('Expected 127 unique observations')
    destination = ROOT / 'data/sumber/lampiran_a_pdf.csv'
    with destination.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    manifest = dict(file_lokal=str(pdf.relative_to(ROOT)),
                    asal_berkas='Disediakan pengguna pada 2026-11-17; bukan unduhan langsung sesi audit',
                    url_rujukan='https://digilib.uns.ac.id/dokumen/download/111483/NzEwODU3/Potensi-Struktur-Ruang-Wilayah-Polisentris-Lampiran_Salim-Aziz.pdf',
                    sha256_pdf=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    sha256_ekstraksi=hashlib.sha256(destination.read_bytes()).hexdigest(),
                    jumlah_halaman_pdf=len(reader.pages), halaman_tabel=pages,
                    extractor=f'pypdf {pypdf.__version__}; extract_text default (Form XObjects)',
                    cakupan='Hanya Lampiran A, 127 baris; bagian biografi dan wawancara tidak diekspor')
    (ROOT / 'data/sumber/lampiran_a_pdf_manifest.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', nargs='?', type=Path, default=ROOT / 'docs/Lampiran_Salim Aziz.pdf')
    extract(parser.parse_args().pdf.resolve())
