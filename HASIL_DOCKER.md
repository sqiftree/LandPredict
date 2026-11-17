# Hasil verifikasi Docker — 15 November 2026

Build Docker dan eksekusi baseline berhasil. Perintah reproduksi tersedia pada
README.md, bagian Menjalankan dengan Docker. Tiga keluaran baru:
`hasil/baseline/metrik.csv`, `hasil/baseline/per_wilayah.csv`, dan
`hasil/baseline/prediksi_uji.csv`.

| Model | MAE (Rp/m²) | RMSE (Rp/m²) |
| --- | ---: | ---: |
| Linear | 739.020 | 1.355.435 |
| KNN | 732.073 | 1.530.233 |
| Decision Tree | 756.462 | 1.449.369 |

Angka dibulatkan ke rupiah. Ketiga MAE cocok dengan acuan. Verifikasi independen
dari CSV prediksi lulus: 127 kunci unik sesuai data sumber, 127 prediksi valid
per model, tujuh blok kabupaten/kota per model, 21 baris per_wilayah, serta
kesesuaian MAE/RMSE gabungan dan MAE tiap blok.

Evaluasi menahan satu kabupaten/kota penuh pada setiap lipatan luar. Standardisasi
dipasang hanya pada data latih; pemilihan k (3, 7, 15) dan kedalaman (2, 4, 6)
menggunakan lipatan kabupaten/kota di dalam data latih. Parameter terpilih tercatat
di per_wilayah.csv. Kedua prediktor tetap jumlah penduduk dan jumlah fasum regional.

GWR belum dijalankan: seluruh 127 kecamatan masih membutuhkan geometri dan
koordinat terverifikasi. Status sumber ada di data/SUMBER_KOORDINAT.md.
Belum ada 28 baris evaluasi empat model. Karena itu belum dapat disimpulkan
apakah kedekatan geografis membantu prediksi. Interpretasi baseline hanya
mencakup rata-rata harga tanah kecamatan tahun 2020, bukan harga bidang tanah.

Implementasi GWR menggunakan Gaussian dengan kandidat bandwidth 5, 10, 20, 40 km.
Jika desain lokal berbobot kehilangan rank, kode menghentikan eksperimen dengan
ValueError regresi lokal singular; tidak menggantinya secara diam-diam dengan
model lain. Ini dapat terjadi akibat kolinearitas atau bobot efektif yang terlalu
terkonsentrasi pada sedikit observasi. Belum ada kegagalan empiris GWR yang diuji.

Lingkungan build: Python 3.12 slim-bookworm, GDAL 3.6.2; numpy 2.3.5,
pandas 2.2.3, scikit-learn 1.8.0, threadpoolctl 3.6.0. Dependensi transitif
yang terpasang: scipy 1.18.1, joblib 1.6.0, cloudpickle 3.1.2,
python-dateutil 4.0.0, pytz 2026.6, tzdata 2026.6.
Snapshot pip freeze juga disimpan di hasil/requirements-resolved.txt.
Tag base image dan paket sistem belum dikunci; rebuild di masa depan dapat
memperbaruinya. Digest base image pada build yang diuji:
`sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df`.

SHA256 CSV sumber:
`b86e3c363db243a4cbb7ccfe38f6868bd3300898f1eeea6eee38752b57f0ae66`.

Pemeriksaan tambahan lulus: konfigurasi Compose, kompilasi sintaks Python,
ogr2ogr --version, dan CLI bantuan koordinat dalam container. Transformasi
geometri sesungguhnya belum diuji karena data poligon belum tersedia.
