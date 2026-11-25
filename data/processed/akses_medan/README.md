# Akses wisata, kampus, dan topografi Solo Raya

Satu baris dalam **fitur.csv** mewakili satu kecamatan. Gabungkan tabel dengan data harga melalui pasangan `kab_kota` dan `kecamatan`. Berkas **poi_osm.csv** menyimpan objek sumber beserta kelas dan identitasnya. **sha256.json** mencatat sidik berkas mentah, geometri, koordinat dan hasil ekstraksi. Pengambilan sumber dilakukan pada 25 November 2026.

| Variabel | Definisi dan satuan | Sumber |
| --- | --- | --- |
| harga_tanah_rata_rata_rp_m2 | Harga rata-rata per kecamatan tahun 2020, Rp/m² | Lampiran A Salim Aziz, transkripsi dan status sumber primer dalam [audit harga](../../SUMBER_DATASET.md) |
| kepadatan_penduduk_proksi | Jumlah penduduk dalam lampiran dibagi luas arsip BIG, jiwa/km² | Lampiran Aziz dan [geometri BIG](../../SUMBER_KOORDINAT.md) |
| built_pct | Persentase luas piksel valid berkelas terbangun | [ESA WorldCover 2020 v100](https://doi.org/10.5281/zenodo.5571936), [manifest raster](../manifest.json) |
| objek_wisata_5km | Jumlah objek wisata terpetakan dalam radius 5 km dari titik interior, termasuk objek lintas batas | © OpenStreetMap contributors, titik dan area pada ekstrak Geofabrik Indonesia 1 Januari 2021 |
| jarak_wisata_km | Jarak Haversine terpendek dari titik interior kecamatan ke objek berkelas attraction, museum atau theme_park, km | OpenStreetMap, ekstrak Geofabrik Indonesia 1 Januari 2021 |
| jarak_kampus_km | Jarak yang sama ke objek berkelas university atau college, km | OpenStreetMap, ekstrak yang sama |
| elevasi_median_m | Median ketinggian sel valid di dalam poligon BIG, meter | Jarvis, Reuter, Nelson & Guevara (2008), CIAT, SRTM v4.1, tile 59_14 |
| lereng_median_derajat | Median sudut kemiringan sel yang dihitung dari gradien elevasi dengan koreksi jarak menurut lintang, derajat | DEM yang sama, resolusi 3 detik busur (sekitar 90 m) |

**Cakupan dan interpretasi.** Objek diambil dari layer titik dan area OSM pada kotak 109,8–111,9° BT dan 8,8–6,7° LS, termasuk daerah sekitar Solo Raya. Untuk objek area digunakan satu titik interior. Ada 293 objek berlabel wisata dan 366 objek berlabel kampus dalam kotak ini. Satu institusi dapat memiliki lebih dari satu objek. Jarak menggambarkan kedekatan dengan objek yang sudah dipetakan sekitar akhir 2020. Kelengkapan pemetaan, waktu perjalanan, jumlah pengunjung dan tahun mulai operasi memerlukan sumber tersendiri. Posisi titik interior juga dapat berbeda dari pusat permukiman. Data objek dan jarak turunannya menggunakan atribusi © OpenStreetMap contributors, ODbL. [Arsip unduhan Geofabrik](https://download.geofabrik.de/asia/indonesia-210101-free.shp.zip) · [Lisensi OSM](https://www.openstreetmap.org/copyright).

**Topografi.** Misi SRTM merekam permukaan pada tahun 2000. Relief digunakan sebagai proksi kondisi fisik tahun 2020. Dua kolom audit memuat banyaknya sel dengan elevasi dan gradien valid serta proporsinya terhadap sel dengan pusat di dalam poligon. Sumber raster adalah CIAT/CGIAR-CSI. Tahun batas BIG dan ketidakpastian historis dijelaskan di [catatan koordinat](../../SUMBER_KOORDINAT.md). [Deskripsi SRTM](https://srtm.csi.cgiar.org/srtmdata/) · [Tile sumber](https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/srtm_59_14.zip).

**Landasan pemilihan variabel.** Riswandha & Wahyono (2017) meneliti kegiatan wisata dan perubahan penggunaan lahan di Tawangmangu. Wang (2023) meneliti kedekatan universitas dan harga rumah di sekitar 128 universitas di Amerika Serikat. Huang & Hewings (2021) memasukkan lereng dalam pemodelan harga tanah di Auckland. Studi tersebut mendukung pengujian hipotesis. Arah dan besaran hubungan perlu diestimasi pada sampel Solo Raya. [Studi Tawangmangu](https://doi.org/10.14710/tpwk.2017.18052) · [Studi universitas](https://doi.org/10.3390/jrfm16030167) · [Studi lereng](https://doi.org/10.3390/land10030261).

Dataset gabungan dengan target tersedia dalam [dataset.csv](../../../artifacts/review_kepadatan_wisata/dataset.csv). [Uji korelasi](../../../artifacts/review_kepadatan_wisata/korelasi.csv) dan [prediksi luar](../../../artifacts/review_kepadatan_wisata/prediksi_seleksi.csv) dapat ditelusuri ke tabel tersebut. Tahun 2020 pada CSV merujuk pada harga dan populasi. Tahun pengamatan atau versi sumber lain mengikuti tabel di atas.

## Reproduksi

Dari akar repositori, eksperimen dapat dijalankan dengan CSV terbitan dan dependensi pemodelan di requirements.txt.

```sh
python scripts/eksperimen_akses_medan.py --output hasil/akses_medan
python scripts/grafik_akses_medan.py hasil/akses_medan
python scripts/review_kepadatan_wisata.py --output hasil/review_kepadatan_wisata
```

Untuk membangun ulang fitur, siapkan poligon penuh melalui tahap audit spasial di README utama. Gunakan lingkungan geospasial dengan NumPy, Rasterio, Shapely dan pyshp. Ekstraksi terbitan memakai NumPy 2.5.5, Rasterio 1.5.2, Shapely 2.2.0 dan pyshp 3.1.9.

```sh
python scripts/unduh_poi_historis.py
mkdir -p data/raw/srtm
curl --fail --location https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/srtm_59_14.zip -o data/raw/srtm/srtm_59_14.zip
python scripts/fitur_akses_medan.py
```
