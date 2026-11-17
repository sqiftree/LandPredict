# Eksperimen harga tanah kecamatan Solo Raya 2020

Audit ulang 17 November 2026. Status: eksperimen komputasional selesai dan dapat direproduksi; geometri historis 2020 belum terbukti. Judul kerja paper: **Evaluasi GWR dan Model Nonspasial untuk Prediksi Harga Tanah Rata-rata Kecamatan di Solo Raya dengan Validasi Lintas Kabupaten/Kota**.

Pertanyaan: apakah kedekatan geografis membantu memperkirakan rata-rata harga tanah kecamatan ketika seluruh kabupaten/kotanya tidak ikut dilatih?

## Hasil evaluasi

| Model | MAE (Rp/m²) | RMSE (Rp/m²) | R² gabungan |
|---|---:|---:|---:|
| Linear | 739.020 | 1.355.435 | 0,557 |
| KNN | 732.073 | 1.530.233 | 0,435 |
| Decision Tree | 756.462 | 1.449.369 | 0,493 |
| GWR Gaussian | 802.227 | 1.409.692 | 0,521 |

MAE ketiga baseline cocok persis dengan acuan setelah pembulatan ke rupiah. GWR mempunyai MAE sekitar 9,58% lebih tinggi daripada KNN, tetapi RMSE sekitar 7,88% lebih rendah. Linear memiliki RMSE terbaik. Dengan spesifikasi yang diuji, belum ada bukti peningkatan prediksi yang konsisten dari pembobotan geografis. Ini bukan bukti bahwa semua model spasial tidak berguna, dan bukan uji signifikansi statistik. Semua metrik dihitung gabungan atas 127 prediksi uji; bukan rata-rata sederhana tujuh skor wilayah.

GWR memilih bandwidth 40 km pada enam kabupaten dan 10 km pada Surakarta. Karena enam lipatan memilih ujung atas grid, pencarian ini belum membuktikan bandwidth optimal di luar 40 km; perlu eksperimen sensitivitas yang ditentukan sebelumnya. Surakarta merupakan kasus sulit: MAE GWR Rp5.393.705/m² dan KNN Rp5.779.800/m². Lima kecamatan tersebut tetap masuk evaluasi. GWR mengungguli KNN dalam MAE hanya pada Karanganyar dan Surakarta (2/7 blok).

## Data dan metode yang dapat ditulis di paper

Satu observasi adalah satu kecamatan pada 2020. Target adalah harga tanah rata-rata dalam Rp/m²; kedua prediktor identik untuk semua model, yaitu jumlah penduduk dan jumlah fasilitas umum regional. Sumber transkripsi tercantum di README dan kolom halaman_lampiran pada CSV. Tidak ada penggantian nilai harga, interpolasi ke bidang tanah, atau proyeksi harga ke tahun mendatang.

Keempat model memakai tujuh lipatan luar leave-one-kabupaten/kota-out yang sama. Pada setiap lipatan, enam kabupaten/kota melatih model dan satu kabupaten/kota menguji. Pemilihan parameter memakai enam lipatan wilayah di dalam bagian latih saja, dengan MAE gabungan validasi sebagai kriteria. StandardScaler dipasang ulang pada bagian latih setiap pemanggilan model, termasuk lipatan dalam. Tidak ada standardisasi atau pemilihan parameter dari target uji luar.

KNN memakai jarak pada dua prediktor terstandardisasi (bukan kedekatan geografis), bobot distance dan k ∈ {3,7,15}. Decision Tree memakai kedalaman {2,4,6}, min_samples_leaf=3, random_state=124. Linear memakai intercept. GWR memodelkan intercept dan dua prediktor, dengan bobot Gaussian w=exp[-0,5(d/b)²], bandwidth tetap {5,10,20,40} km, dan jarak haversine antar titik representatif. Titik dihitung di dalam gabungan poligon kecamatan melalui UTM 49S, lalu dikembalikan ke WGS84. Penyelesaian kuadrat terkecil memakai akar bobot; normalisasi log-bobot tidak mengubah solusi.

Semua 127 kunci unik, 127 prediksi finite per model, tujuh blok per model, dan 28 baris hasil wilayah lulus verifikasi. MAE dan RMSE gabungan serta setiap wilayah dihitung ulang langsung dari prediksi. Audit.json menyimpan versi, hash, parameter, skor validasi dalam dan pembagian latih/uji. Tidak ada singularitas yang ditemukan. Jika suatu kandidat singular pada validasi dalam, kandidat itu ditolak dan kegagalan dicatat; jika seluruh kandidat gagal atau regresi luar singular, eksperimen berhenti. Tidak ada pergantian model diam-diam atau regularisasi tersembunyi.

## Keterbatasan sebelum publikasi

- Padanan dan uji containment terhadap arsip BIG berhasil 127/127; peta audit dan peta perbandingan diperiksa visual. Ini tidak mengesahkan garis batas tahun 2020. Metadata fitur BIG berpenanda 20230928, sementara deskripsi layanan menyebut edisi 2022. Seluruh 127 kecamatan masih memerlukan konfirmasi kesetaraan batas historis. Rincian sumber dan wilayah prioritas di data/SUMBER_KOORDINAT.md. Hasil GWR harus diberi status eksploratif sampai tahap itu selesai.
- Dua padanan eksplisit: Kebakkramat → Kebakramat dan Sidoharjo → Sidoarjo. Nama asli CSV tidak diubah. Padanan kedua masih perlu dicocokkan kembali ke lampiran harga, meskipun nama administratif Sidoharjo didukung BPS SP2020.
- Linear menghasilkan 17 dan GWR 15 prediksi negatif. Prediksi tidak dipotong menjadi nol agar baseline tetap sebanding. Nilai negatif merupakan keterbatasan regresi tanpa kendala, bukan harga tanah yang masuk akal. Transformasi log atau kendala nonnegatif perlu menjadi eksperimen terpisah.
- Satu titik mewakili wilayah, tidak mewakili lokasi seluruh transaksi. Hanya dua prediktor dan 127 observasi; tujuh blok tidak memberi dasar untuk klaim generalisasi nasional atau kausalitas. Tidak ada interval ketidakpastian atau pengujian autokorelasi residual dalam eksperimen ini.
- Angka harga dan prediktor memakai transkripsi yang tersedia; audit ulang seluruh angka terhadap lampiran sumber belum dilakukan pada sesi ini. Kesimpulan terbatas pada rata-rata kecamatan tahun 2020, bukan nilai per bidang atau harga saat ini.

## Berkas hasil

- data/koordinat.csv: 127 titik WGS84; data/SUMBER_KOORDINAT.md: provenance dan keterbatasan.
- hasil/spasial/metrik.csv, per_wilayah.csv, prediksi_uji.csv: tiga keluaran utama empat model.
- hasil/baseline/: tiga keluaran baseline yang dijalankan ulang.
- hasil/spasial/audit.json: parameter, skor seleksi, fold dan lingkungan.
- hasil/audit_spasial/padanan_dan_titik.csv: daftar lengkap nama dan kode sumber, posisi titik, containment, luas dan jarak ke batas.
- hasil/paper/dataset_paper_2020.csv: 127 observasi beserta prediksi uji, residu aktual minus prediksi, kode administratif, sumber, WGS84 dan UTM 49S dalam meter.
- hasil/paper/harga_prediksi_solo_raya_2020.geojson: 127 poligon WGS84 dengan atribut dataset tersebut, dapat dibuka di QGIS. Kolom UTM adalah atribut titik; geometri GeoJSON tetap WGS84.
- hasil/paper/peta_harga_dan_prediksi.pdf dan .png: lima peta dengan skala warna yang sama, termasuk prediksi negatif tanpa pemotongan.
- hasil/paper/sha256.json dan hasil/requirements-resolved.txt: sidik berkas dan dependensi aktual.

## Reproduksi

Dari direktori proyek, setelah memasang Python 3.12, GDAL/ogr2ogr dan requirements.txt:

```bash
python eksperimen_tanah.py --output hasil/baseline
python verifikasi_hasil.py hasil/baseline
python siapkan_koordinat.py data/jawa_tengah_big.geojson --kab wadmkk --kec wadmkc --padanan data/padanan_nama.csv --output data/koordinat.csv
python audit_spasial.py
python eksperimen_tanah.py --koordinat data/koordinat.csv --output hasil/spasial
python verifikasi_hasil.py hasil/spasial --spasial
python siapkan_paper.py
```

Sesi ini memakai image lokal gwr-solo-raya:local (ID e979288ea0c0), Python 3.12.16, numpy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0. Untuk menjalankan perintah di atas dalam Docker, build image lalu awali setiap perintah dengan:

```bash
docker build -t gwr-solo-raya:local .
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD:/app" -w /app gwr-solo-raya:local python siapkan_paper.py
```

Ganti bagian `python siapkan_paper.py` dengan masing-masing perintah sesuai urutan. Mount direktori proyek memastikan kode terkini dan keluaran tersedia di host. Build membutuhkan jaringan; eksekusi memakai arsip lokal dan tidak membutuhkan jaringan. Dependensi transitif dapat berubah saat rebuild; gunakan hasil/requirements-resolved.txt untuk mereplikasi versi sesi ini.
