# Audit ulang implementasi, dataset, dan klaim paper

Tanggal: 18 November 2026. Versi awal yang diperiksa: `3b0c30d52aa0043a90ad7057a1c12b63749902ce`. Saat mulai, main lokal dan origin/main sama serta working tree bersih. Tidak ditemukan perubahan tracked atau commit tambahan setelah audit PDF sebelumnya; atribusi pekerjaan tertentu kepada Argon tidak dapat ditentukan dari berkas yang identik. Sinkronisasi Git yang sebelumnya terputus sudah selesai sebelum audit ini dimulai.

## Hasil yang diperiksa ulang

| Pemeriksaan | Hasil dan batas maknanya |
| --- | --- |
| PDF Lampiran A | Ekstraksi langsung diulang memakai pypdf 5.9.0; hash PDF dan hash CSV hasil ekstraksi sama dengan catatan sebelumnya. 127 identitas dan 381 nilai cocok. Pemeriksaan visual empat halaman berasal dari sesi 17 November, tidak diklaim sebagai pemeriksaan visual baru. |
| Halaman tabel | 30, 38, 38, 21 baris pada halaman PDF 1–4. Sebanyak 21 label A-4 pada CSV lama menunjuk nomor cetak B-1. Salinan dataset dengan metadata halaman yang benar sudah tersedia. |
| Tiga baseline dan GWR | Dijalankan ulang dengan Python 3.12.16 serta versi pustaka yang dicatat. Prediksi, metrik, parameter terpilih, skor validasi internal dan fold sama dengan arsip; maksimum selisih prediksi 0 untuk semua model. |
| Protokol uji | 127 prediksi per model, 7 blok per model, 28 baris hasil regional untuk empat model. StandardScaler dilatih hanya pada bagian latih; pemilihan k, kedalaman, bandwidth tidak menerima indeks uji luar. |
| Singularitas | Tidak terjadi pada data dan grid yang diuji. Tes memastikan kasus singular ditolak dan seluruh kandidat singular menghentikan seleksi. |
| Geometri | Audit independen Shapely/pyproj terhadap poligon arsip mengonfirmasi 127 titik di dalam poligon; minimum jarak batas 383,022469 m. Maksimum selisih terhadap titik representatif sekitar 3,26e-9 m. Ini bukan verifikasi garis batas tahun 2020. |
| Tes | 10 lulus: 7 tes protokol dan 3 tes baru untuk kejujuran status audit dataset. |
| Artefak acuan | 25 hash dalam artifacts/sha256.json cocok. Hash membuktikan konsistensi berkas, bukan kebenaran substantif pengukuran awal. |

Ringkasan mesin ada di `artifacts/review_20261118/summary.json`. Perintah berikut membuat ulang hasil audit di `hasil/audit_20261118/`. Hasil acuan tersedia di `artifacts/`.

| Model | MAE (Rp/m²) | RMSE (Rp/m²) |
| --- | --- | --- |
| Linear | 739.020 | 1.355.435 |
| KNN | 732.073 | 1.530.233 |
| Decision Tree | 756.462 | 1.449.369 |
| GWR | 802.227 | 1.409.692 |

## Kekeliruan dan celah yang diperbaiki

1. **Status audit ditulis tetap.** Skrip lama menulis kalimat keberhasilan sebelum assertion numerik terakhir. Jika CSV berubah, proses dapat gagal tetapi meninggalkan JSON yang masih menyebut 381 nilai cocok. Sekarang jumlah dan status dihitung dari hasil aktual; kegagalan mengganti JSON menjadi `failed`. Generator paper berhenti jika pemeriksaan gagal. Tes sengaja mengubah nilai penduduk untuk membuktikannya.
2. **PDF tidak selalu tersedia.** Skrip dahulu dapat menyatakan pemeriksaan PDF tanpa membedakan keberadaan berkas lokal. Sekarang `pdf_lokal_diperiksa` menyatakan apakah hash PDF lokal benar-benar dicek. Tanpa PDF, perbandingan hanya terhadap ekstraksi yang diarsipkan. Tanggal pemeriksaan visual sebelumnya dipisahkan dari tanggal eksekusi audit.
3. **Generator paper terlalu mengandalkan keluaran lama.** Sekarang verifier menghitung ulang MAE/RMSE/R² dan memeriksa struktur fold sebelum DOCX dibuat. Kalimat tetap tentang jumlah tes di tabel paper diganti dengan penjelasan pemeriksaan yang benar-benar dipanggil generator.
4. **Dokumentasi sumber tertinggal.** Ringkasan eksperimen dan draf lama masih menyebut seluruh angka belum dicocokkan dengan lampiran, padahal audit PDF sudah selesai. Teks tersebut diselaraskan; ketidakpastian harga primer tetap dinyatakan.
5. **Asal wilayah Wonosamodro terlalu disederhanakan.** Uraian diperbaiki menjadi Wonosegoro dan Kemusu sesuai [berita resmi Pemprov Jawa Tengah, 11 Februari 2019](https://jatengprov.go.id/beritadaerah/tiga-kecamatan-baru-terbentuk-berikut-camat-yang-menjabat/). Keberadaan kecamatan baru tidak membuktikan geometri BIG identik dengan batas 2020.
6. **Klaim toleransi koordinat terlalu ketat.** Catatan <1e-9 m tidak sesuai hasil ulang maksimum 3,26e-9 m. Dokumentasi sekarang menyebut nilai terukur dan batas <1e-8 m. Angka koordinat tidak diubah.
7. **Satu titik bukan satu-satunya pilihan metodologis.** Paper kini menyebut representasi satu titik sebagai pilihan implementasi, bukan kewajiban universal semua model spasial.

## Pemeriksaan referensi dan cakupan klaim

- [Saefuddin dkk. (2012), laman penerbit](https://scialert.net/fulltext/?doi=ajms.2012.132.141) mendukung perbandingan OLS/GWR di Tangerang Selatan dan pembahasan akses jalan/fasilitas. Studi tersebut menggunakan data titik serta transformasi log-harga; tidak dipakai untuk mengesahkan akurasi eksperimen kecamatan Solo Raya.
- [Syahar dkk. (2020), laman penerbit](https://geomatejournal.com/geomate/article/view/1136) mendukung pembahasan CBD, fasilitas, perubahan penggunaan lahan dan bencana. Abstraknya menyebut data koridor Padang tahun 2014, sehingga tahun publikasi 2020 bukan tahun observasinya.
- Koreksi bibliografi Arumingtyas dan pembatasan penggunaan Janssen dari audit sebelumnya dipertahankan. Tidak semua isi seluruh referensi diperiksa ulang secara penuh pada sesi ini.

## Hal yang tetap belum terbukti

- Definisi harga primer dan pembentukan rata-rata kecamatan: arsip layer Bhumi 2020, sampel, serta metode agregasi belum tersedia. Kecocokan PDF tidak otomatis membuktikan harga transaksi.
- Perbedaan fasilitas pada tujuh wilayah serta penduduk pada tiga wilayah antara lampiran dan artikel tetap ada. Tidak ditetapkan sebagai salah ketik atau beda tahun tanpa bukti tambahan.
- Kesesuaian garis batas historis 2020 belum diverifikasi untuk 127 kecamatan; alias Sidoarjo–Sidoharjo belum dikonfirmasi melalui identitas wilayah penulis sumber.
- Tidak ada eksperimen prediktor tambahan, uji signifikansi perbedaan model, interval ketidakpastian blok, atau uji autokorelasi residual baru. Jangan menyajikan rencana sebagai hasil.
- DOCX diperiksa sebagai ZIP/XML yang valid dan dibangun ulang. Tata letak halaman belum dirender ulang dengan Microsoft Word/LibreOffice pada sesi ini.

## Reproduksi dan keterbatasan lingkungan

Docker dan ogr2ogr tidak tersedia dalam sesi ini. Python 3.12.16 terisolasi dipasang dengan dependensi sesuai `artifacts/requirements-resolved.txt`; pypdf 5.9.0 ditambahkan untuk ekstraksi sumber. Model dihitung ulang dan geometri diaudit menggunakan koordinat arsip. Langkah ekspor GDAL tidak dijalankan ulang; ini bukan klaim bahwa seluruh scripts/reproduce.py berhasil pada sesi ini.

```bash
python scripts/extract_appendix.py
python scripts/audit_dataset.py
python -m unittest discover -s tests -v
python -m tanah run --output hasil/audit_20261118/baseline
python -m tanah run --koordinat data/koordinat.csv --output hasil/audit_20261118/spasial
python scripts/check_regression.py artifacts/baseline hasil/audit_20261118/baseline
python scripts/check_regression.py artifacts/spasial hasil/audit_20261118/spasial
python -m tanah verify hasil/audit_20261118/baseline
python -m tanah verify hasil/audit_20261118/spasial --spasial
python -m tanah audit --output hasil/audit_20261118/geometri
python scripts/build_manuscript.py
```
