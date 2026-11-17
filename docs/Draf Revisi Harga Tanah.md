# 1. Permasalahan: Estimasi Harga Tanah Rata-Rata per Meter Persegi pada Tingkat Kecamatan di Solo Raya Tahun 2020 Menggunakan Geographically Weighted Regression dan Model Nonspasial

## a. Deskripsi Permasalahan

Harga tanah menunjukkan variasi antarlokasi yang dapat berkaitan dengan karakteristik penduduk, fasilitas pelayanan, aksesibilitas, dan intensitas pembangunan wilayah. Pada dataset penelitian ini, harga tanah rata-rata Kecamatan Laweyan tercatat sebesar Rp11.800.794/m², sedangkan Kecamatan Jebres sebesar Rp6.269.466/m². Perbedaan tersebut menunjukkan bahwa kecamatan dalam satu kota pun dapat memiliki tingkat harga tanah yang berbeda.

Penelitian mencakup 127 kecamatan di Kota Surakarta serta Kabupaten Boyolali, Sukoharjo, Karanganyar, Wonogiri, Sragen, dan Klaten. Unit pengamatan adalah kecamatan, dengan target berupa harga tanah rata-rata per meter persegi tahun 2020.

Pemilihan karakteristik wilayah sebagai prediktor didukung oleh penelitian terdahulu. Aziz, Rahayu, dan Istanabi (2023) membahas harga lahan, kepadatan penduduk, fasilitas umum, dan penggunaan lahan dalam kajian pusat aktivitas Surakarta Raya. Penelitian tersebut memberikan konteks wilayah bagi pengembangan variabel, meskipun tujuan analisisnya adalah identifikasi struktur polisentris melalui klasterisasi.

Dalam penelitian harga tanah di Tangerang Selatan, Saefuddin dkk. (2012) menggunakan karakteristik aksesibilitas dan lingkungan serta membandingkan regresi global dengan GWR. Jarak terhadap gerbang tol, jalan arteri, dan fasilitas umum menjadi faktor yang relevan dalam penelitian tersebut. Sementara itu, Syahar, Ramadhan, dan Putri (2020) menunjukkan relevansi jarak ke pusat kegiatan, fasilitas pelayanan, perubahan penggunaan lahan, dan kondisi bencana dalam pola nilai tanah di Padang. Temuan tersebut menjadi dasar untuk menguji variabel aksesibilitas dan pembangunan wilayah pada konteks Solo Raya; bukan jaminan bahwa hubungan yang sama berlaku pada skala kecamatan.

Selain kedua kajian tersebut, Arumingtyas, Subiyanto, dan Firdaus (2019) menganalisis pengaruh aksesibilitas serta keberadaan fasilitas umum dan fasilitas sosial terhadap harga bidang tanah di Kelurahan Tlogosari Kulon, Kota Semarang, sekaligus membedakan harga pasar dan Nilai Jual Objek Pajak (NJOP) sebagai rujukan operasionalisasi target di Jawa Tengah. Pada skala kota besar di Indonesia, Janssen, Mulder, dan Yudhistira (2022) mengkaji pemilahan spasial kelompok pendapatan di Jakarta; kajian ini digunakan sebagai konteks struktur perkotaan, bukan pengesahan langsung prediktor harga tanah Solo Raya.

Eksperimen awal menggunakan jumlah penduduk dan jumlah fasilitas umum regional. Pengembangan penelitian direncanakan melalui pengujian kepadatan penduduk, akses terhadap pusat kegiatan, akses jalan utama, dan proporsi permukaan terbangun. Penambahan tersebut bertujuan memperluas informasi penjelas harga tanah, bukan menjamin peningkatan kinerja model.

GWR digunakan untuk mengevaluasi hubungan lokal antara karakteristik wilayah dan harga tanah. Regresi linear, K-Nearest Neighbors, dan Decision Tree menjadi pembanding dengan prediktor yang sama. Pertanyaan utama penelitian adalah: apakah pembobotan berdasarkan kedekatan geografis membantu memperkirakan harga tanah rata-rata kecamatan ketika seluruh kabupaten/kotanya dikeluarkan dari data latih?

## b. Sumber Data

Dataset utama. Dataset awal merupakan transkripsi Lampiran A penelitian Salim Aziz di Repositori Universitas Sebelas Maret, halaman A-1 sampai A-4. Berkas yang digunakan memuat 127 kecamatan beserta jumlah penduduk, jumlah fasilitas umum regional, dan harga tanah rata-rata. Kolom halaman_lampiran disertakan untuk menelusuri kembali setiap observasi ke tabel sumber. Tautan sumber tercantum pada bagian referensi.

Sebelum penyusunan naskah akhir, definisi harga tanah pada sumber perlu dikonfirmasi, termasuk apakah berasal dari transaksi, penawaran, NJOP, atau sumber penilaian lainnya. Cara penghitungan rata-rata dan cakupan sampelnya juga perlu diperiksa. Pada tahap ini, target diperlakukan sesuai label pada dataset sumber sebagai harga tanah rata-rata kecamatan. Data belum diklaim sebagai hasil pengumpulan langsung dari instansi sumber primer.

Geometri kecamatan. Eksperimen menggunakan arsip poligon dari layanan publik BIG KSP Satu Peta, layer Peta Wilayah Administrasi Kecamatan. Ekspor Jawa Tengah memuat 576 kecamatan dan telah dipadankan dengan 127 kecamatan pada dataset penelitian. Atribut fitur arsip memiliki penanda metadata 20230928, sedangkan deskripsi layanan menyebut edisi 2022. Kesesuaiannya dengan batas administratif tahun 2020 masih perlu dikonfirmasi. Sumber dan proses pencocokan dicatat dalam data/SUMBER_KOORDINAT.md.

Data tambahan yang direncanakan. Pengembangan variabel akan menggunakan sumber berikut setelah kelengkapan dan kesesuaian tahunnya diperiksa.

| Data | Kandidat sumber | Kebutuhan verifikasi |
| --- | --- | --- |
| Penduduk dan luas kecamatan | BPS, SP2020, publikasi kabupaten/kecamatan dalam angka | Tahun observasi dan kesesuaian wilayah |
| Fasilitas umum | Tabel sumber awal, BPS, dan instansi penyedia fasilitas | Jenis fasilitas, satuan, dan keberadaan pada 2020 |
| Pusat kegiatan | RTRW/RDTR atau dokumen perencanaan resmi yang relevan | Definisi pusat dan masa berlaku dokumen |
| Jaringan jalan utama | BIG/RBI dan dinas terkait | Klasifikasi jalan serta tahun data |
| Permukaan terbangun | GHSL GHS-BUILT-S epoch 2020 | Resolusi dan metode agregasi ke kecamatan |

GHSL menyediakan produk permukaan terbangun multitemporal yang dapat digunakan untuk menyusun indikator intensitas pembangunan. Definisi indikator harus mengikuti produk tersebut dan tidak disamakan langsung dengan luas kawasan permukiman dalam dokumen tata ruang (European Commission, Joint Research Centre, GHS-BUILT-S R2023A).

Tahun terbit publikasi tidak otomatis menjadi tahun observasi. Setiap tabel dan layer harus diperiksa secara terpisah. Data tambahan yang tidak memenuhi kesesuaian tahun atau cakupan wilayah tidak akan dimasukkan ke eksperimen utama tanpa penjelasan. Sumber alternatif DIY yang pernah ditelusuri tidak digunakan sebagai dataset eksperimen Solo Raya ini.

## c. Rumusan Masalah

1. Seberapa besar galat GWR dalam memperkirakan harga tanah rata-rata kecamatan pada kabupaten/kota yang tidak dilibatkan dalam pelatihan?

2. Bagaimana kinerja GWR dibandingkan dengan KNN, Decision Tree, dan regresi linear berdasarkan MAE, RMSE, dan R² pada observasi uji yang sama?

3. Apakah penambahan variabel aksesibilitas dan intensitas pembangunan meningkatkan kemampuan prediksi dibandingkan dua prediktor awal?

4. Seberapa sensitif hasil GWR terhadap metode penentuan titik representatif kecamatan?

5. Pada kabupaten/kota mana GWR menghasilkan galat lebih kecil daripada model pembanding?

## d. Metode Pendekatan

Penelitian menggunakan pendekatan kuantitatif melalui regresi terawasi. Satu baris data mewakili satu kecamatan pada tahun 2020. Eksperimen dibagi menjadi baseline yang telah dijalankan dan pengembangan variabel yang direncanakan. Hasil yang tersedia saat ini hanya menggunakan dua prediktor awal; variabel tambahan belum dikumpulkan dan diuji secara lengkap.

### i. Variabel Penelitian dan Dasar Pemilihannya

| Simbol | Variabel | Definisi operasional | Status |
| --- | --- | --- | --- |
| Y | Harga tanah rata-rata | Harga rata-rata kecamatan, Rp/m² | Tersedia |
| X₁ | Jumlah penduduk | Penduduk per kecamatan, jiwa | Baseline |
| X₂ | Fasilitas umum regional | Jumlah fasilitas sesuai definisi sumber | Baseline |
| X₃ | Kepadatan penduduk | Penduduk dibagi luas kecamatan, jiwa/km² | Pengembangan |
| X₄ | Akses pusat kegiatan | Jarak ke pusat kegiatan terdekat dari sumber independen, km | Pengembangan |
| X₅ | Akses jalan utama | Jarak titik representatif ke jalan arteri terdekat, km | Pengembangan |
| X₆ | Proporsi permukaan terbangun | Luas permukaan terbangun dibagi luas kecamatan, persen | Pengembangan |
| s | Lokasi representatif | Lintang dan bujur titik kecamatan | Tersedia |
| g | Kelompok wilayah | Kabupaten/kota untuk pembagian evaluasi | Tersedia |

Jumlah penduduk menggambarkan ukuran populasi, sedangkan kepadatan penduduk menggambarkan intensitas populasi terhadap luas wilayah. Oleh karena itu, keduanya akan dibandingkan dalam spesifikasi berbeda terlebih dahulu. Kepadatan penduduk administratif juga berbeda dari kepadatan terhadap luas lahan terbangun yang dibahas dalam penelitian Aziz dkk. (2023).

Fasilitas umum regional digunakan sebagai indikator pelayanan wilayah. Definisi jenis fasilitas dan cara penghitungannya harus konsisten antarkecamatan. Indikator akses pusat kegiatan dan jalan utama digunakan untuk menguji informasi konektivitas yang belum tercakup oleh jumlah fasilitas, dengan landasan empiris dari Saefuddin dkk. (2012) dan Syahar dkk. (2020).

Proporsi permukaan terbangun direncanakan sebagai indikator intensitas pembangunan. Variabel tersebut merupakan operasionalisasi yang diusulkan dalam penelitian ini; manfaat prediktifnya belum diketahui sebelum pengujian.

Pusat kegiatan ditentukan berdasarkan sumber perencanaan atau inventarisasi independen. Penentuannya tidak menggunakan harga tanah tertinggi pada dataset, sehingga target tidak digunakan untuk membentuk prediktor. Definisi jarak utama direncanakan sebagai jarak garis lurus dalam proyeksi metrik; jarak jaringan, jika tersedia untuk 2020, akan diperlakukan sebagai analisis tambahan dengan definisi terpisah.

| Eksperimen | Prediktor | Tujuan |
| --- | --- | --- |
| A | Jumlah penduduk dan fasilitas regional | Baseline |
| B | Kepadatan penduduk dan fasilitas regional | Menguji perubahan indikator penduduk |
| C | Eksperimen B ditambah akses pusat kegiatan, akses jalan utama, dan proporsi terbangun | Menguji kontribusi informasi tambahan |
| D | Prediktor sama dengan C, dengan alternatif titik representatif | Menguji sensitivitas lokasi |

Eksperimen B–D belum dijalankan. Semua model pada setiap eksperimen akan menggunakan himpunan prediktor dan observasi uji yang sama. Dalam eksperimen D, aksesibilitas dipertahankan tetap agar perubahan hasil dapat dikaitkan dengan representasi lokasi untuk bobot GWR. Jika aksesibilitas turut dihitung ulang, hasil dilaporkan sebagai skenario gabungan yang berbeda.

### ii. Penentuan Koordinat dan Keterkaitannya dengan Harga Tanah

Penetapan titik koordinat untuk GWR berdiri di atas empat landasan metodologis dan teknis:

1. **Representasi Unit Areal**: GWR mengestimasi koefisien regresi lokal menggunakan pembobot kernel Gaussian wᵢ(s) = exp[−dᵢ(s)² / (2h²)] yang membutuhkan jarak antarlokasi dᵢ(s) berbasis titik. Karena observasi pada dataset berupa agregat wilayah kecamatan (poligon areal) dan bukan titik persil transaksi tunggal, setiap kecamatan diwakili oleh satu koordinat titik representatif.
2. **Jaminan Ketercakupan Interior (`ST_PointOnSurface` vs Centroid Biasa)**: Berbeda dengan pusat massa geometris biasa (centroid) yang dapat jatuh di luar batas wilayah pada poligon kecamatan yang berbentuk cekung (concave) atau tidak beraturan, algoritma `ST_PointOnSurface(ST_Union(geom))` menjamin titik wakil selalu berada di bagian dalam poligon kecamatan masing-masing. Hasil audit spasial menunjukkan 127 dari 127 titik berada di dalam poligon kecamatannya, dengan jarak terdekat ke batas sebesar 383,02 m (Kecamatan Serengan, Kota Surakarta; luas 3,06 km²) dan jarak terjauh ke batas sebesar 4.572,15 m (Kecamatan Pracimantoro, Kabupaten Wonogiri; luas 144,40 km²).
3. **Konsistensi Geodetik (UTM Zona 49S EPSG:32749 dan Jarak Haversine WGS84)**: Poligon dipadankan menggunakan pasangan identitas kabupaten/kota dan kecamatan, diproyeksikan terlebih dahulu ke sistem metrik planar UTM zona 49S (EPSG:32749) agar penggabungan dan penentuan titik berlangsung pada bidang datar bersatuan meter, kemudian ditransformasikan kembali ke WGS84 (EPSG:4326) untuk menghitung jarak lingkaran besar Haversine (radius bumi 6.371,0088 km).
4. **Konstruksi koordinat tanpa target harga**: Titik ditentukan murni dari geometri poligon administratif BIG tanpa menggunakan informasi harga tanah (`harga_tanah_rata_rata_rp_m2`).

Metode tersebut menghasilkan titik yang berada di dalam wilayah, tetapi tidak menjamin titik itu merupakan pusat penduduk, pusat perdagangan, kantor kecamatan, atau lokasi transaksi tanah. Harga pada dataset merupakan atribut kecamatan. Dengan demikian, harga rata-rata kecamatan yang dilekatkan pada titik representatif tidak ditafsirkan sebagai harga bidang tanah tepat pada koordinat tersebut. Titik hanya digunakan untuk merepresentasikan lokasi wilayah dalam penghitungan jarak geografis.

Sebagai contoh, nilai Rp7.678.425/m² pada baris Banjarsari merupakan harga rata-rata kecamatan menurut dataset, bukan hasil pengukuran harga tepat di titik point-on-surface Banjarsari. Koordinat pengamatan transaksi yang mendasari rata-rata tersebut belum tersedia dalam CSV.

Audit komputasional menunjukkan 127 dari 127 titik berada di dalam poligon padanannya. Namun, pemeriksaan tersebut tidak membuktikan kesetaraan batas dengan tahun 2020 atau keterwakilan titik terhadap lokasi sampel harga. Padanan eksplisit diterapkan pada Kebakkramat–Kebakramat dan Sidoharjo–Sidoarjo; padanan terakhir masih perlu dikonfirmasi kembali terhadap lampiran harga.

Uji sensitivitas direncanakan dengan membandingkan titik administratif yang digunakan saat ini dengan titik pusat berbobot penduduk atau permukaan terbangun, apabila data pendukung tersedia. Aturan penentuan titik dan penanganan titik yang berada di luar poligon harus ditetapkan sebelum evaluasi. Harga aktual tidak digunakan untuk menentukan atau menggeser titik.

### iii. Geographically Weighted Regression

GWR memungkinkan koefisien regresi berbeda menurut lokasi. Pendekatan ini digunakan untuk menguji apakah hubungan karakteristik wilayah dengan harga tanah lebih baik dimodelkan secara lokal (Brunsdon dkk., 1996). Untuk lokasi s dengan p prediktor:

> ŷ(s) = β̂₀(s) + Σⱼ₌₁ᵖ β̂ⱼ(s)xⱼ(s)

Koefisien diperoleh dengan meminimalkan jumlah kuadrat residual berbobot:

> β̂(s) = arg minᵦ Σᵢ∈T wᵢ(s)[yᵢ − b₀ − Σⱼ₌₁ᵖ bⱼxᵢⱼ]²

T merupakan himpunan observasi latih. Bobot Gaussian ditentukan sebagai:

> wᵢ(s) = exp[−dᵢ(s)² / (2h²)]

Jarak dᵢ(s) dihitung menggunakan haversine dalam kilometer. Eksperimen awal menggunakan kandidat bandwidth 5, 10, 20, dan 40 km, yang dipilih melalui validasi internal. Prediktor distandardisasi menggunakan statistik data latih pada setiap pemanggilan model.

Regresi lokal diperiksa terhadap kehilangan rank. Kandidat yang singular pada validasi internal ditolak dan dicatat. Jika seluruh kandidat gagal atau regresi pada tahap uji luar singular, eksperimen dihentikan. Penambahan prediktor akan disertai pemeriksaan kolinearitas dan kecukupan informasi lokal.

### iv. K-Nearest Neighbors

KNN memilih observasi latih berdasarkan kemiripan prediktor terstandardisasi. Pada eksperimen awal, kemiripan dihitung dari jumlah penduduk dan fasilitas umum, bukan jarak geografis. Prediksi merupakan rata-rata berbobot harga tetangga:

> ŷ(x) = Σᵢ∈Nₖ₍ₓ₎ wᵢyᵢ / Σᵢ∈Nₖ₍ₓ₎ wᵢ

Bobot menggunakan invers jarak fitur, dengan kandidat k sebesar 3, 7, dan 15. Standardisasi dilakukan menggunakan statistik bagian latih pada setiap lipatan. Implementasi menggunakan KNeighborsRegressor dengan weights='distance'.

### v. Decision Tree dan Regresi Linear

Decision Tree membagi observasi berdasarkan ambang prediktor. Eksperimen awal menguji kedalaman maksimum 2, 4, dan 6, dengan minimum tiga observasi per daun serta random_state=124. Regresi linear digunakan sebagai pembanding global yang mengestimasi satu intersep dan satu koefisien untuk setiap prediktor pada seluruh data latih.

Istilah model nonspasial mengacu pada tidak digunakannya pembobotan lokal berdasarkan jarak antarkecamatan. Pada eksperimen pengembangan, model pembanding tetap dapat menerima prediktor aksesibilitas yang diturunkan dari data geografis. Dengan demikian, perbandingan menguji manfaat pembobotan geografis setelah informasi prediktor disamakan.

### vi. Skema Evaluasi

Evaluasi menggunakan tujuh lipatan luar leave-one-kabupaten/kota-out. Setiap putaran menahan seluruh kecamatan dalam satu kabupaten/kota sebagai data uji, sedangkan enam wilayah lainnya digunakan untuk pelatihan.

Di dalam data latih, pemilihan parameter dilakukan melalui validasi antarkabupaten/kota. MAE gabungan validasi internal menjadi kriteria pemilihan parameter. Standardisasi, imputasi jika diperlukan, dan seleksi prediktor berbasis data hanya menggunakan bagian latih. Pendekatan evaluasi berkelompok dipilih agar pengujian sesuai dengan tujuan prediksi ke wilayah yang tidak dilibatkan dalam pelatihan (Roberts dkk., 2017).

> MAE = (1/n) Σᵢ |yᵢ − ŷᵢ|

> RMSE = √[(1/n) Σᵢ (yᵢ − ŷᵢ)²]

> R² = 1 − Σᵢ (yᵢ − ŷᵢ)² / Σᵢ (yᵢ − ȳ)²

MAE dan RMSE dilaporkan dalam Rp/m². Metrik gabungan dihitung langsung dari 127 prediksi uji setiap model, bukan rata-rata sederhana tujuh skor wilayah. R² gabungan menggunakan rata-rata target seluruh observasi uji gabungan. Hasil per wilayah juga dilaporkan untuk menunjukkan variasi kinerja antarkabupaten/kota.

Program menyimpan metrik.csv, per_wilayah.csv, dan prediksi_uji.csv. Catatan audit menyimpan parameter, skor seleksi internal, pembagian wilayah, versi pustaka, serta hash data. Prediksi dan metrik dihitung ulang melalui verifikasi_hasil.py.

### vii. Hasil Awal

Eksperimen A dengan dua prediktor telah dijalankan ulang pada 17 November 2026 dan menghasilkan hasil berikut. Angka MAE dan RMSE dibulatkan ke rupiah.

| Model | MAE (Rp/m²) | RMSE (Rp/m²) | R² |
| --- | --- | --- | --- |
| Regresi linear | 739.020 | 1.355.435 | 0,557 |
| KNN | 732.073 | 1.530.233 | 0,435 |
| Decision Tree | 756.462 | 1.449.369 | 0,493 |
| GWR Gaussian | 802.227 | 1.409.692 | 0,521 |

KNN menghasilkan MAE terendah, sedangkan regresi linear menghasilkan RMSE terendah. GWR memiliki RMSE lebih rendah daripada KNN, tetapi MAE lebih tinggi. Dengan demikian, spesifikasi awal belum menunjukkan keunggulan geografis yang konsisten. Hasil tersebut tidak membuktikan bahwa semua model spasial tidak bermanfaat.

GWR memilih bandwidth 40 km pada enam lipatan kabupaten dan 10 km pada lipatan Kota Surakarta. Pemilihan batas atas kandidat pada sebagian besar lipatan menunjukkan perlunya pengujian sensitivitas rentang bandwidth. GWR menghasilkan MAE lebih kecil daripada regresi linear pada Karanganyar (17 kecamatan) dan Sukoharjo (12 kecamatan), tetapi tidak pada lima wilayah lainnya.

Seluruh model memiliki 127 prediksi uji dan tujuh blok evaluasi, sehingga terdapat 28 baris hasil per wilayah. Tidak ditemukan regresi lokal singular pada eksperimen awal. Namun, regresi linear menghasilkan 17 prediksi negatif dan GWR menghasilkan 15 prediksi negatif. Nilai tersebut dipertahankan dalam evaluasi sebagai keluaran model tanpa kendala nonnegatif; bukan harga tanah yang layak ditafsirkan secara ekonomi.

Hasil ini merupakan baseline dengan geometri yang kesesuaian historisnya masih perlu dikonfirmasi. Hasil pengembangan variabel belum tersedia dan tidak boleh disimpulkan dari metrik baseline.

### viii. Batasan Penelitian

Penelitian menggunakan data agregat kecamatan tahun 2020. Hasilnya tidak digunakan untuk menaksir harga satu bidang tanah atau perubahan harga pada tahun berikutnya. Hubungan pada tingkat kecamatan tidak otomatis berlaku pada tingkat bidang.

Definisi dan cara pembentukan harga rata-rata pada sumber masih memerlukan penelusuran. Kelengkapan transkripsi, jenis harga, serta distribusi sampel pembentuk rata-rata perlu dikonfirmasi sebelum publikasi.

Geometri yang digunakan memiliki metadata lebih baru daripada tahun observasi. Kecocokan nama dan containment titik telah diperiksa, tetapi kesetaraan garis batas historis belum dibuktikan untuk seluruh 127 kecamatan.

Satu titik menyederhanakan wilayah kecamatan yang dapat memiliki sebaran aktivitas dan harga beragam. Oleh karena itu, sensitivitas terhadap representasi lokasi perlu dievaluasi.

Penambahan variabel berpotensi meningkatkan kolinearitas dan ketidakstabilan regresi lokal. Dengan 127 observasi, pengembangan prediktor dilakukan secara terbatas dan berdasarkan ketersediaan data serta dasar konseptual. Perbedaan tahun sumber tambahan harus dilaporkan, bukan diganti labelnya menjadi 2020.

Evaluasi penelitian berfokus pada prediksi. Hubungan yang ditemukan tidak otomatis menunjukkan pengaruh kausal penduduk, fasilitas, aksesibilitas, atau pembangunan terhadap harga tanah. Belum tersedia interval ketidakpastian atau hasil pengujian autokorelasi residual pada eksperimen awal.

## e. Referensi

Arumingtyas, O., Subiyanto, S., & Firdaus, H. (2019). Analisis faktor aksesibilitas, fasum dan fasos terhadap harga bidang tanah serta visualisasi berbasis WebGIS (Studi kasus: Kelurahan Tlogosari Kulon, Kecamatan Pedurungan, Kota Semarang). Jurnal Geodesi Undip, 8(4), 165–174. https://doi.org/10.14710/jgundip.2019.25155

Aziz, S. (t.t.). Potensi Struktur Ruang Wilayah Polisentris. Repositori UNS, Lampiran A. Tahun publikasi perlu dikonfirmasi; 2020 merupakan tahun data. https://digilib.uns.ac.id/dokumen/download/111483/NzEwODU3/Potensi-Struktur-Ruang-Wilayah-Polisentris-Lampiran_Salim-Aziz.pdf

Aziz, S., Rahayu, P., & Istanabi, T. (2023). Potensi wilayah perkotaan polisentris pada Surakarta Raya ditinjau dari perspektif pusat aktivitas. Jurnal Pengembangan Kota, 11(2), 140–154. https://doi.org/10.14710/jpk.11.2.140-154

Badan Informasi Geospasial. (t.t.). Peta Wilayah Administrasi Kecamatan, KSP Satu Peta, layer 3. Metadata diperiksa ulang 17 November 2026. https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3

Brunsdon, C., Fotheringham, A. S., & Charlton, M. E. (1996). Geographically weighted regression: A method for exploring spatial nonstationarity. Geographical Analysis, 28(4), 281–298. https://doi.org/10.1111/j.1538-4632.1996.tb00936.x

European Commission, Joint Research Centre. GHS-BUILT-S R2023A: Built-up surface grid. Kandidat sumber variabel pengembangan; belum digunakan pada hasil baseline. https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php

Janssen, K. M. J., Mulder, P., & Yudhistira, M. H. (2022). Spatial sorting of rich versus poor people in Jakarta. Bulletin of Indonesian Economic Studies, 58(2), 167–194. https://doi.org/10.1080/00074918.2021.1876209

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., … Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.

Pemerintah Kota Surakarta. Laporan pada portal Dinas Lingkungan Hidup, Gambar 1.10, hlm. i-20: penduduk per kecamatan tahun 2020, sumber BPS Kota Surakarta 2021. Diakses 17 November 2026. https://dlh.surakarta.go.id/web/file/20220714104304.pdf

Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., … Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 40(8), 913–929. https://doi.org/10.1111/ecog.02881

Saefuddin, A., Widyaningsih, Y., Ginting, A., & Mamat, M. (2012). Land price model considering spatial factors. Asian Journal of Mathematics & Statistics, 5, 132–141. https://doi.org/10.3923/ajms.2012.132.141

Syahar, F., Ramadhan, R., & Putri, S. (2020). Statistical interpretation of land value patterns in Padang, Indonesia. International Journal of GEOMATE, 19(72), 109–116. https://geomatejournal.com/geomate/article/view/1136

## Kontribusi Anggota pada Tahap Pengembangan

Pembagian berikut merupakan rencana dan perlu disesuaikan dengan kontribusi aktual.

| Anggota | Rencana pekerjaan |
| --- | --- |
| Yashif Victoriawan | Integrasi pipeline eksperimen dan reproduksi hasil |
| [Nama anggota 2] | Audit sumber harga, transkripsi, dan definisi variabel |
| [Nama anggota 3] | Pengumpulan data tambahan, padanan wilayah, dan pemeriksaan koordinat |
| [Nama anggota 4] | Telaah referensi, analisis galat, dan penyusunan pembahasan |
