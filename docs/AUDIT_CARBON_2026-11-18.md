# Audit perubahan setelah pengerjaan Gemini Carbon

Tanggal: 18 November 2026. Dasar pembandingan: commit `1bff01d` dan lima berkas kerja yang belum di-commit. Atribusi kepada Gemini Carbon mengikuti keterangan pengguna; Git tidak mencatat identitas pembuat perubahan yang belum di-commit.

## Temuan dan perbaikan

| Prioritas | Temuan sebelum perbaikan | Tindakan |
| --- | --- | --- |
| Tinggi | Paper menyimpulkan harga Aziz merupakan agregasi poligon ZNT 2020 tanpa arsip layer atau metode agregasi. | Diganti dengan status belum terverifikasi pada template, sumber dataset, generator, Markdown dan DOCX. |
| Tinggi | Ketiadaan unduhan massal/arsip 2020 dinyatakan sebagai fakta meskipun akses aplikasi gagal. | Diganti dengan belum memperoleh/memverifikasi akses. Timeout bukan bukti ketiadaan data. |
| Sedang | Standar atribut 2025/2026 dipakai seolah membuktikan skema BHUMI 2020, tahun berjalan, dan protokol GetFeatureInfo. | Dipisahkan antara standar dan pengamatan layanan; klaim protokol dan atribut live tanpa respons dihapus. |
| Sedang | Fallback generator menangkap semua ModuleNotFoundError dan mengizinkan audit.json tidak ada. | Fallback dibatasi untuk numpy/pandas; verifier stdlib mewajibkan audit.json dan menjelaskan bahwa model tidak dilatih ulang. |

## Bukti sumber

- [Katalog Data BHUMI](https://bhumi.atrbpn.go.id/bantuan/katalog_data) dan [Unsur Peta](https://bhumi.atrbpn.go.id/bantuan/unsur_peta): cuplikan indeks pencarian resmi menyebut ZNT. Pembukaan langsung dalam sesi audit gagal timeout dan HTTP 502. Tidak dilakukan pemeriksaan atribut live atau pengambilan zona Solo Raya.
- [Permen ATR/BPN No. 1 Tahun 2025](https://www.peraturan.go.id/files/permen-atrbpn-no-1-tahun-2025.pdf): PDF resmi berhasil dibaca, halaman tercetak 95–96 (indeks PDF 94–95) memuat NOZN, NILAIZN, NILBULAT dan THNNILAI. Ini mendukung deskripsi standar tersebut, bukan asal angka 2020 dalam Lampiran A.
- Artikel Aziz mengatribusikan harga ke BHUMI 2020 sesuai audit terdahulu. Belum tersedia bukti yang menghubungkan 127 angka dengan identitas zona, sampel, dan rumus agregasi. PDF artikel tidak dibaca ulang seluruhnya pada sesi ini.

## Verifikasi lokal

- Seluruh 25 hash dalam `artifacts/sha256.json` cocok, termasuk CSV utama, geometri, koordinat, kode eksperimen dan tiga CSV hasil spasial.
- Audit transkripsi: 127 kunci dan 381/381 nilai cocok dengan ekstraksi PDF yang diarsipkan; hash PDF lokal juga cocok. Ekstraksi dan pemeriksaan visual PDF tidak diulang dalam sesi ini.
- Verifier stdlib menghitung ulang MAE, RMSE dan R² dari prediksi tersimpan, memeriksa 127 prediksi tiap model, tujuh wilayah tiap model, 28 baris hasil wilayah, serta pemisahan wilayah latih/uji dalam log.
- Tiga tes audit dataset dan empat tes verifier manuskrip lulus, termasuk penolakan prediksi yang diubah, audit hilang, dan wilayah uji yang masuk daftar latih.
- Generator berhasil memperbarui Markdown dan DOCX. ZIP/XML DOCX valid, dua gambar disematkan. Tampilan visual Word tidak diperiksa.
- Pustaka eksperimen tidak tersedia dalam interpreter sesi ini. Pelatihan model, tujuh tes protokol yang membutuhkan pustaka tersebut, serta perhitungan ulang geometri tidak dijalankan. Verifikasi CSV tidak membuktikan ulang semua langkah pelatihan; hash menunjukkan kode dan artefaknya tidak berubah dari arsip.

| Model | MAE (Rp/m²) | RMSE (Rp/m²) |
| --- | ---: | ---: |
| Linear | 739.020 | 1.355.435 |
| KNN | 732.073 | 1.530.233 |
| Decision Tree | 756.462 | 1.449.369 |
| GWR | 802.227 | 1.409.692 |

Perintah verifikasi sesi ini:

```bash
python3 -m unittest discover -s tests -p test_dataset_audit.py
python3 -m unittest discover -s tests -p test_manuscript_verification.py
python3 scripts/build_manuscript.py
```

## Implikasi presentasi

Eksperimen tetap dapat dipresentasikan sebagai studi data sekunder rata-rata kecamatan 2020. Jangan menyebutnya hasil pengambilan transaksi resmi atau ekstraksi ZNT langsung. Perbedaan total fasilitas pada tujuh wilayah, penduduk pada tiga wilayah, dan kecocokan batas historis 2020 tetap belum terselesaikan. Daftar 25 kandidat variabel adalah rancangan pengembangan; belum menjadi 25 prediktor terukur atau bukti korelasi signifikan.

Perbaikan tersimpan lokal. Tidak dilakukan commit atau push pada sesi audit ini.
