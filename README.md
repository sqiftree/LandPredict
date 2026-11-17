# LandPredict — harga tanah kecamatan Solo Raya

Eksperimen reproduktif untuk membandingkan Gaussian GWR, regresi linear, KNN,
dan Decision Tree dalam memprediksi **harga tanah rata-rata 127 kecamatan tahun
2020**, ketika seluruh kabupaten/kota uji dikeluarkan dari pelatihan.

## Hasil dan paper

| Model | MAE (Rp/m²) | RMSE (Rp/m²) |
| --- | ---: | ---: |
| Linear | 739.020 | 1.355.435 |
| KNN | 732.073 | 1.530.233 |
| Decision Tree | 756.462 | 1.449.369 |
| GWR | 802.227 | 1.409.692 |

- [Paper DOCX](docs/Paper%20Harga%20Tanah%20Solo%20Raya.docx)
- [Paper Markdown](docs/Paper%20Harga%20Tanah%20Solo%20Raya.md)
- [Tiga CSV dan audit empat model](artifacts/spasial/)
- [Hasil baseline](artifacts/baseline/)
- [Peta dan diagnostik](artifacts/figures/)
- [Ringkasan eksperimen](HASIL_PAPER.md)

Hasil tersebut hanya memakai **jumlah penduduk dan fasilitas umum regional**.
Kepadatan, aksesibilitas, dan permukaan terbangun masih merupakan rencana.
GWR belum menunjukkan keunggulan konsisten; 15 prediksi GWR dan 17 prediksi Linear
negatif dibiarkan apa adanya agar evaluasi dapat direproduksi.

**Batas interpretasi:** titik mewakili kecamatan, bukan lokasi transaksi. 127 titik
berada di poligon padanannya, tetapi batas historis 2020 belum terverifikasi.
Arsip BIG memiliki penanda fitur 20230928. Definisi harga dan angka transkripsi
masih memerlukan audit kembali ke sumber. Lihat [provenance koordinat](data/SUMBER_KOORDINAT.md).

## Menjalankan eksperimen

Gunakan Python 3.12. Dependensi terikat langsung ada di `requirements.txt`; versi
lingkungan eksekusi lengkap di `artifacts/requirements-resolved.txt`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m tanah run --output hasil/baseline
python -m tanah verify hasil/baseline
python -m tanah run --koordinat data/koordinat.csv --output hasil/spasial
python -m tanah verify hasil/spasial --spasial
```

Di Windows, buat lingkungan dengan `py -3.12 -m venv .venv` dan gunakan
`.venv\Scripts\python.exe` sebagai pengganti `python`.

Koordinat arsip sudah tersedia sehingga menjalankan model tidak memerlukan GDAL.
Untuk menghitung ulang koordinat dari poligon, diperlukan `ogr2ogr` (GDAL dengan
GeoJSON, GPKG, SQLite); Docker menyediakan dependensi sistem tersebut.

## Reproduksi penuh dengan Docker

```bash
docker build -t gwr-solo-raya:local .
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD:/app" -w /app gwr-solo-raya:local python scripts/reproduce.py
```

Pada PowerShell, gunakan `--user 1000:1000` dan `-v "${PWD}:/app"`.
Build image membutuhkan jaringan. Pipeline berjalan tanpa jaringan, memulihkan
GeoJSON dari arsip gzip, menghitung ulang titik, mengaudit poligon, menjalankan
empat model, membandingkan hasil dengan arsip, dan membuat peta serta diagnostik.
Folder `hasil/` dihasilkan ulang; `artifacts/` adalah snapshot hasil yang ditinjau.

Tiap tahap juga dapat dijalankan terpisah:

```bash
python scripts/restore_geometry.py
python -m tanah coordinates data/jawa_tengah_big.geojson --kab wadmkk --kec wadmkc --padanan data/padanan_nama.csv --output data/koordinat.csv
python -m tanah audit
python -m tanah paper
```

Skrip lama `eksperimen_tanah.py`, `siapkan_koordinat.py`, `audit_spasial.py`,
`verifikasi_hasil.py`, dan `siapkan_paper.py` tetap menerima perintah sebelumnya.
Docker Compose juga tersedia untuk eksekusi baseline (`docker compose run --rm eksperimen`).

## Struktur kode

```text
tanah/
  config.py          kontrak dataset dan grid parameter
  data.py            validasi data dan pencocokan koordinat
  models.py          Linear, KNN, Tree dan Gaussian GWR
  selection.py       lipatan wilayah dan validasi internal
  experiment.py      orkestrasi empat model dan CSV keluaran
  verification.py    perhitungan ulang metrik dan pemeriksaan fold
  provenance.py      hash input/kode dan metadata eksekusi
  coordinates.py     titik dalam gabungan poligon menggunakan GDAL
  spatial_audit.py   validasi titik-poligon dan peta audit
  reporting.py       dataset gabungan, GeoJSON dan peta paper
  diagnostics.py     diagnostik galat dan grafik aktual-prediksi
scripts/
  reproduce.py       seluruh pipeline tanpa jaringan
  restore_geometry.py dekompresi arsip BIG dengan verifikasi hash
  check_regression.py kesetaraan hasil sebelum/sesudah refaktor
  build_manuscript.py naskah berbasis CSV dan diagnostik aktual
  render_docx.py      tabel/gambar DOCX dengan sampul dipertahankan
```

## Pengujian

```bash
python -m unittest discover -s tests -v
python scripts/check_regression.py artifacts/baseline hasil/baseline
python scripts/check_regression.py artifacts/spasial hasil/spasial
```

Tes memeriksa pemisahan wilayah latih/uji, standardisasi hanya pada data latih,
penolakan koordinat yang salah, kegagalan singular, serta perlindungan terhadap
CSV lama ketika eksekusi terbaru gagal. Verifikasi dijalankan tanpa `python -O`.

## Memperbarui naskah dari hasil

Setelah pipeline penuh selesai, salin figur yang ditinjau lalu jalankan generator:

```bash
python scripts/publish_artifacts.py
python scripts/build_manuscript.py
```

`publish_artifacts.py` memperbarui snapshot dengan hasil yang sudah diverifikasi;
jalankan hanya setelah meninjau perubahan eksperimen. Generator memakai
`docs/paper_template.md`, menyisipkan tabel hasil dan dua gambar, kemudian membuat
`docs/Paper Harga Tanah Solo Raya.md` dan `.docx`. Sampul berasal dari draf awal;
draf awal tidak ditimpa karena dapat sedang dibuka di Word. Narasi template perlu
ditinjau lagi bila metode atau hasil eksperimen diubah.

## Sumber dan status data

Harga serta kedua prediktor ditranskripsi dari [Lampiran A penelitian Salim Aziz,
UNS](https://digilib.uns.ac.id/dokumen/download/111483/NzEwODU3/Potensi-Struktur-Ruang-Wilayah-Polisentris-Lampiran_Salim-Aziz.pdf).
Kolom `halaman_lampiran` melacak tabel sumber. Geometri dari
[BIG KSP Satu Peta](https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3).
Arsip GeoJSON dikompresi secara lossless dalam `data/jawa_tengah_big.geojson.gz`;
hash ada di `data/geometri_manifest.json`. Arsip GDB HDX pembanding tidak disertakan
karena tidak dipakai pipeline utama; metadata dan catatan keterbatasannya tetap ada.

Tidak ada koordinat tebakan, imputasi harga, interpolasi ke bidang, atau proyeksi
harga ke tahun lain. Paper melaporkan hasil prediksi deskriptif, bukan inferensi kausal.
