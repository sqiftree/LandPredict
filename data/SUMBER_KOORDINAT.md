# Sumber dan Verifikasi Data Koordinat Kecamatan Solo Raya 2020

Tanggal audit ulang: 18 November 2026.
Status: **127/127 padanan dan titik terverifikasi terhadap geometri arsip BIG; kesesuaian batas historis 2020 belum terverifikasi.**

Tanggal pengambilan arsip menurut catatan sesi sebelumnya: 15 November 2026; tidak tersedia log unduhan bertimestamp untuk pembuktian independen. Metadata layanan diperiksa ulang melalui URL pada 17 November 2026. Arsip lokal digunakan kembali tanpa mengganti geometri.

---

## 1. Sumber Data Geometri dan Poligon

### Sumber Utama: Badan Informasi Geospasial (BIG) — KSP Satu Peta
* **Layanan REST ArcGIS**:  
  `https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3`
* **Nama Layer**: `Peta Wilayah Administrasi Kecamatan` (Layer ID: 3, Tipe Geometri: `esriGeometryPolygon`)
* **Metadata Layer**: `TASWIL1000020230928_DATA_BATAS_DESAKELURAHAN` (penanda metadata fitur 28 September 2023; bukan bukti tanggal berlaku batas)
* **Sistem Koordinat Acuan Sumber**: WGS84 (EPSG:4326), `srs_id`: `SRGI 2013`
* **Kolom Identitas Sumber**:
  - `wadmkk`: Nama kabupaten / kota
  - `wadmkc`: Nama kecamatan
  - `kdcpum`: Kode wilayah kecamatan Kemendagri (misal `33.09.10`)
  - `objectid`: Nomor ID unik objek BIG
* **File Ekspor Wilayah**: `data/jawa_tengah_big.geojson` (576 kecamatan se-Jawa Tengah, format GeoJSON FeatureCollection WGS84)

### Catatan Akses Sumber Alternatif / Terkait
1. **BAPANAS MapServer**:  
   `https://geoservices.big.go.id/gis/rest/services/BAPANAS/Batas_Administrasi/MapServer/1` yang dirujuk pada README awal dialihkan ke halaman autentikasi/login BIG (`code: 499, message: Token Required`), sehingga layer publik KSP Satu Peta BIG di atas digunakan sebagai sumber resmi terbuka.
2. **HDX (Humanitarian Data Exchange / UN OCHA & WFP)**:  
   Dataset `cod-ab-idn` (validitas batas BPS 1 April 2020) diarsipkan di `data/sumber/hdx/` sebagai pembanding historis.

---

## 2. Kesesuaian Wilayah Administratif Tahun 2020

Sebanyak **127 kecamatan** dalam dataset harga tanah 2020 (`data/harga_tanah_2020.csv`) terdistribusi dalam 7 kabupaten/kota:
- **Kabupaten Boyolali**: 22 kecamatan
- **Kabupaten Klaten**: 26 kecamatan
- **Kabupaten Sukoharjo**: 12 kecamatan
- **Kabupaten Wonogiri**: 25 kecamatan
- **Kabupaten Karanganyar**: 17 kecamatan
- **Kabupaten Sragen**: 20 kecamatan
- **Kota Surakarta**: 5 kecamatan

### Pengecekan Pemekaran dan Batas Historis
* **Pemekaran Boyolali (2018–2019)**:  
  Berdasarkan Perda Kabupaten Boyolali No. 18 Tahun 2018, terjadi pemekaran 3 kecamatan baru:
  1. *Gladagsari* (pemekaran dari Ampel)
  2. *Tamansari* (pemekaran dari Musuk)
  3. *Wonosamodro* (wilayah asal Wonosegoro dan Kemusu; menurut berita resmi Pemprov Jawa Tengah 11 Februari 2019)
  Jumlah kecamatan di Boyolali bertambah dari 19 menjadi 22. Dataset penelitian Salim Aziz (tahun data 2020) mencatat seluruh 22 kecamatan ini secara lengkap. Poligon BIG juga memuat 22 poligon definitif tersebut, sehingga daftar nama dapat dipadankan. Kesamaan jumlah dan nama tidak membuktikan kesamaan garis batas tahun 2020.
* **Wilayah Lain**:  
  Jumlah padanan Klaten (26), Sukoharjo (12), Karanganyar (17), Wonogiri (25), Sragen (20), dan Surakarta (5) sesuai CSV. Pemeriksaan ini belum membuktikan tidak adanya perubahan batas 2020–2023.

---

## 3. Padanan Nama (127/127 Padanan Unik)

Sebanyak 125 kecamatan cocok secara otomatis melalui normalisasi teks baku (casefold, pembersihan spasi ganda, dan penghapusan prefiks `kabupaten ` / `kota `).  
Dua (2) kecamatan memiliki perbedaan variasi ejaan dan dipadankan secara eksplisit melalui `data/padanan_nama.csv`:

| Kab Sumber (BIG) | Kec Sumber (BIG) | Kab Kota (Data 2020) | Kecamatan (Data 2020) | Alasan & Bukti BPS 2020 |
| :--- | :--- | :--- | :--- | :--- |
| Karanganyar | Kebakkramat | Kabupaten Karanganyar | Kebakramat | Variasi ejaan huruf `k` tunggal vs dobel. Publikasi BPS Karanganyar 2020 menggunakan `Kebakkramat`. |
| Wonogiri | Sidoharjo | Kabupaten Wonogiri | Sidoarjo | Ejaan pada CSV memakai `Sidoarjo`; satu-satunya kecamatan yang berpadanan di Wonogiri adalah `Sidoharjo` sesuai BPS Wonogiri 2020. |

Tidak ada benturan kunci dalam padanan yang dipilih; PDF lampiran halaman 2 telah mengonfirmasi ejaan Sidoarjo; interpretasi identitas administratif Sidoarjo → Sidoharjo masih perlu dikonfirmasi; setiap pasangan `(kab_kota, kecamatan)` memetakan tepat ke satu kode Kemendagri (`kdcpum`) dan poligon unik.

---

## 4. Ekstraksi Titik Representatif Spasial

Titik representatif dihasilkan menggunakan script `siapkan_koordinat.py` dengan prosedur:
1. Memproyeksikan poligon kecamatan WGS84 (EPSG:4326) ke UTM Zona 49S (EPSG:32749).
2. Melakukan penggabungan poligon per kecamatan (`ST_Union`).
3. Mengambil titik permukaan terjamin di dalam poligon (`ST_PointOnSurface`).
4. Mentransformasikan kembali koordinat titik ke WGS84 derajat desimal (`lat`, `lon`).

### Hasil Audit Spasial (`audit_spasial.py`)
* **In-Polygon Check**: **127 dari 127 titik (100%)** berada di dalam poligon kecamatan masing-masing.
* **Jarak Minimum ke Batas Poligon**: **383,02 meter** (Kecamatan Serengan, Kota Surakarta; luas wilayah 3,06 km²).
* **Selisih Point-on-Surface**: audit ulang 18 November 2026 menghasilkan maksimum sekitar 3,26e-9 meter, di bawah 1e-8 meter (konsisten numerik). Klaim lama <1e-9 meter telah dikoreksi.
* **Peta Audit**: Visualisasi visual 127 titik dan batas administratif tersimpan di `hasil/audit_spasial/peta_audit.png` dan `hasil/audit_spasial/peta_audit.pdf`.

## 5. Koreksi audit 17 November 2026 dan batas penggunaan

Deskripsi layanan BIG menyebut edisi 2022/revisi 27 Desember 2022, sedangkan atribut fitur arsip bertuliskan 20230928. Keduanya harus dilaporkan; geometri ini tidak boleh disebut batas 2020 yang terverifikasi. Sumber metadata: https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3?f=pjson (diakses ulang 17 November 2026). Deskripsi menyebut penyelarasan batas kabupaten/kota, sehingga kesamaan nama saja tidak memadai.

Belum ada kecamatan yang gagal dipadankan secara struktural (0/127). Namun kesamaan geometri historis masih belum dibuktikan untuk seluruh 127 kecamatan, tercantum satu per satu di `hasil/audit_spasial/padanan_dan_titik.csv`. Prioritas pemeriksaan adalah Gladagsari, Tamansari, Wonosamodro, serta wilayah asal Ampel, Musuk, Wonosegoro dan Kemusu. Pembentukan tiga kecamatan didukung berita Pemerintah Provinsi Jawa Tengah tentang pelantikan camat tahun 2019: https://jatengprov.go.id/beritadaerah/tiga-kecamatan-baru-terbentuk-berikut-camat-yang-menjabat/ . Jangan menyimpulkan asal seluruh desa hanya dari ringkasan pemekaran di atas.

Padanan Wonogiri/Sidoarjo memakai Sidoharjo, yang tercantum dalam tabel SP2020 BPS: https://wonogirikab.bps.go.id/id/statistics-table/2/MTkyIzI%3D/jumlah-penduduk-hasil-sp2020.html . Nama CSV asli tetap dipertahankan. Dukungan nama administratif ini tidak dengan sendirinya mengonfirmasi angka harga dalam lampiran sumber.

Arsip metadata HDX `data/sumber/hdx.json` menyebut batas dibuat 8 April 2020, valid untuk penggunaan kemanusiaan 1 April 2020, serta peninjauan 30 Oktober 2025. Tanggal itu bukan jaminan seluruh pemekaran sudah dimuat. Akses ulang halaman HDX pada 17 November 2026 menghasilkan HTTP 403; arsip lokal tetap tersedia. Belum dilakukan pembuktian kesetaraan semua poligon BIG terhadap HDX. Karena itu keluaran GWR bersifat eksploratif dengan ketidakpastian geometri historis yang dinyatakan eksplisit.

Harga, penduduk, dan fasilitas tetap nilai sumber tahun 2020; tidak dilakukan interpolasi harga ke desa, bidang, atau tahun lain. GeoJSON hasil gabungan memakai WGS84 (EPSG:4326); kolom proyeksi titik dan peta memakai UTM 49S (EPSG:32749). GWR memakai jarak haversine dalam km dari titik WGS84, bukan jarak derajat atau koordinat UTM sebagai prediktor.
