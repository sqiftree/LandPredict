# Estimasi Harga Tanah Rata-Rata Kecamatan di Solo Raya Tahun 2020: Perbandingan Geographically Weighted Regression dan Model Nonspasial dengan Validasi Lintas Kabupaten/Kota

## Abstrak

Penelitian ini mengevaluasi manfaat pembobotan geografis untuk memperkirakan harga tanah rata-rata kecamatan pada kabupaten/kota yang tidak dilibatkan dalam pelatihan. Dataset mencakup 127 kecamatan di tujuh kabupaten/kota Solo Raya tahun 2020, dengan jumlah penduduk dan jumlah fasilitas umum regional sebagai prediktor. Geographically Weighted Regression (GWR) Gaussian dibandingkan dengan regresi linear, K-Nearest Neighbors (KNN), dan Decision Tree menggunakan tujuh lipatan luar leave-one-kabupaten/kota-out. Standardisasi dan pemilihan parameter dilakukan pada bagian latih melalui validasi internal antarkabupaten/kota. Koordinat dihitung sebagai point-on-surface dari poligon kecamatan BIG setelah proyeksi ke UTM 49S dan digunakan untuk menghitung jarak haversine. Pada eksperimen dua prediktor, KNN menghasilkan MAE terendah sebesar Rp732.073/m², sedangkan regresi linear menghasilkan RMSE terendah sebesar Rp1.355.435/m². GWR menghasilkan MAE Rp802.227/m² dan RMSE Rp1.409.692/m². Eksperimen tujuh prediktor menambahkan kepadatan dan tutupan lahan serta memodelkan log-harga. KNN berbobot menghasilkan MAE Rp619.531/m² dan RMSE Rp1.309.859/m². Dengan demikian, pembobotan geografis pada spesifikasi yang diuji belum memberi keunggulan konsisten. Seluruh model menghasilkan 127 prediksi uji dan hasilnya dapat direproduksi melalui pipeline modular. Interpretasi dibatasi pada rata-rata kecamatan tahun 2020, dengan ketidakpastian definisi harga, perbedaan fasum dan penduduk antarsumber, serta kesesuaian batas historis yang masih perlu dikonfirmasi.

Kata kunci: harga tanah; GWR; KNN; validasi spasial; Solo Raya; kecamatan.

## 1. Pendahuluan

Harga tanah memiliki variasi spasial yang dapat berkaitan dengan karakter penduduk, aksesibilitas, fasilitas, dan intensitas pembangunan wilayah. Dalam dataset penelitian, harga tanah rata-rata Kecamatan Laweyan mencapai Rp11.800.794/m², sedangkan Kecamatan Jebres Rp6.269.466/m². Perbedaan tersebut mengilustrasikan heterogenitas harga bahkan di dalam Kota Surakarta. Pertanyaan yang dikaji adalah apakah karakteristik wilayah dan kedekatan geografis dapat digunakan untuk memperkirakan harga rata-rata kecamatan di wilayah administratif yang tidak dilibatkan dalam pelatihan.

Aziz, Rahayu, dan Istanabi (2023) mengkaji struktur pusat aktivitas Surakarta Raya melalui karakteristik penggunaan lahan, harga lahan, penduduk, dan fasilitas umum. Penelitian tersebut memberi konteks regional, tetapi menggunakan analisis klaster dan bukan evaluasi prediksi lintas kabupaten/kota. Selain itu, jumlah penduduk pada eksperimen ini berbeda dari konsep kepadatan penduduk yang digunakan dalam kajian pusat aktivitas.

Berbagai kajian empiris nilai tanah di Indonesia menguatkan peran aksesibilitas, fasilitas pelayanan, dan lingkungan dalam membentuk variasi spasial harga tanah. Saefuddin dkk. (2012) mengkaji harga tanah Tangerang Selatan melalui OLS dan GWR, dengan akses terhadap jalan arteri, gerbang tol, dan fasilitas umum sebagai variabel relevan. Syahar dkk. (2020) membahas keterkaitan nilai tanah dengan pusat kegiatan, fasilitas pelayanan, perubahan penggunaan lahan, dan bencana pada konteks Padang. Pada konteks Jawa Tengah, Arumingtyas, Subiyanto, dan Firdaus (2019) menganalisis pengaruh aksesibilitas serta keberadaan fasilitas umum dan fasilitas sosial terhadap harga bidang tanah di Kelurahan Tlogosari Kulon, Semarang, serta membedakan harga pasar dan Nilai Jual Objek Pajak (NJOP). Sementara itu, Janssen, Mulder, dan Yudhistira (2022) mengkaji pemilahan spasial kelompok pendapatan di Jakarta. Kajian tersebut menjadi konteks struktur perkotaan, bukan bukti langsung bahwa tiap kandidat prediktor meningkatkan akurasi harga tanah Solo Raya. Bukti-bukti tersebut mendukung pengujian heterogenitas spasial dan pengembangan prediktor, tetapi tidak menjamin hubungan yang sama berlaku pada rata-rata kecamatan Solo Raya. Perbedaan unit observasi harus diperhatikan ketika mengadaptasi hasil penelitian tingkat bidang atau titik menjadi model tingkat wilayah.

GWR memungkinkan koefisien hubungan prediktor dengan target berubah menurut lokasi (Brunsdon dkk., 1996). Namun, fleksibilitas lokal tidak dengan sendirinya menjamin prediksi yang lebih baik pada wilayah baru. Penelitian ini membandingkan GWR dengan regresi linear, KNN, dan Decision Tree pada prediktor serta pembagian data yang sama. Evaluasi menahan satu kabupaten/kota penuh agar tujuan pengujian sesuai dengan penggunaan model pada kelompok wilayah yang tidak dilibatkan dalam pelatihan.

Kontribusi penelitian adalah evaluasi prediksi lintas tujuh kabupaten/kota dengan pemilihan parameter di dalam data latih, audit pemadanan data harga dengan geometri kecamatan beserta landasan penentuan titik representatifnya, serta penyediaan kode, prediksi uji, dan catatan parameter yang dapat direproduksi. Penelitian tidak berangkat dari asumsi bahwa GWR harus menjadi model terbaik.

## 2. Data dan Wilayah Penelitian

### 2.1. Cakupan dan sumber data

Wilayah penelitian meliputi Kota Surakarta serta Kabupaten Boyolali, Karanganyar, Klaten, Sragen, Sukoharjo, dan Wonogiri. Dataset merupakan transkripsi Lampiran A penelitian Salim Aziz di Repositori UNS. Satu baris menyatakan satu kecamatan pada tahun 2020. Lokasi sumber telah diperiksa pada halaman PDF 1–4, dengan nomor cetak A-1, A-2, A-3, dan B-1. Label A-4 pada 21 baris CSV lama berbeda dari nomor cetak; tabel perbandingan_halaman.csv dan dataset_2020_rujukan_terverifikasi.csv menyediakan rujukan yang diperbaiki tanpa mengubah angka eksperimen. Dataset yang digunakan memuat 127 pasangan unik kabupaten/kota–kecamatan dengan distribusi wilayah, rata-rata harga tanah, rentang harga, total penduduk, total fasilitas regional, dan total luas poligon sebagai berikut.

{{REGION_COUNTS}}

Target diperlakukan mengikuti label sumber sebagai harga tanah rata-rata per meter persegi. Dataset belum dapat diklaim sebagai pengumpulan langsung transaksi tanah. Jenis harga, metode penghitungan rata-rata, distribusi sampel, dan sumber primer setiap kolom masih perlu dikonfirmasi terhadap dokumen sumber. Audit 17 November 2026 mencocokkan 127 kunci dan seluruh 381 nilai pada tiga kolom numerik dengan ekstraksi langsung PDF Lampiran A yang diberikan pengguna. Keempat halaman tabel diperiksa secara visual; hash berkas dan lokasi setiap baris dicatat. Hasil ini memverifikasi transkripsi terhadap dokumen sumber, tetapi belum memvalidasi pengukuran primer. Artikel Aziz dkk. (2023), Gambar 4–5 hlm.147, mengatribusikan harga ke Bhumi ATR-BPN 2020. Dokumentasi resmi BHUMI menyebut Zona Nilai Tanah (ZNT) sebagai salah satu dataset. Namun, audit belum memperoleh arsip layer 2020, atribut layanan historis, atau metode yang menghubungkan zona dengan 127 nilai kecamatan. Karena itu, asal angka tersebut dari agregasi poligon ZNT belum dapat dipastikan. Status ketersediaan unduhan historis juga belum terverifikasi. Penelusuran dokumentasi BHUMI dan katalog ATLAS pada 18 November 2026 mengidentifikasi calon sumber pendukung penggunaan lahan, akses kesehatan, dan bahaya gunung api. Tahun, cakupan Solo Raya, dan data numeriknya belum terverifikasi; temuan katalog ini belum digunakan sebagai prediktor eksperimen. Rincian bukti dan syarat penggunaan disimpan pada data/SUMBER_BHUMI.md dan data/inventaris_bhumi.csv.

{{SOURCE_AUDIT}}

### 2.2. Variabel yang benar-benar diuji

{{VARIABLES}}

Jumlah penduduk dan fasilitas digunakan karena tersedia bersama target pada tabel sumber. Jumlah penduduk mewakili ukuran populasi, sedangkan jumlah fasilitas menggambarkan layanan regional menurut klasifikasi sumber. Penggunaan keduanya bersifat prediktif; tidak dimaksudkan mengidentifikasi dampak kausal. Kategori fasilitas perlu dipastikan sebelum replikasi dengan sumber lain. Tidak ada prediktor kepadatan penduduk, akses jalan, atau permukaan terbangun dalam hasil eksperimen yang dilaporkan pada bagian 4.

{{DESCRIPTIVE}}

### 2.3. Geometri dan Landasan Penentuan Titik Koordinat GWR

Geometri berasal dari arsip BIG KSP Satu Peta, layer Peta Wilayah Administrasi Kecamatan. Ekspor Jawa Tengah memuat 576 kecamatan. Sebanyak 127 kecamatan penelitian dipilih melalui pasangan nama kabupaten/kota dan kecamatan. Dua padanan eksplisit digunakan: Kebakkramat pada BIG dengan Kebakramat pada CSV, serta Sidoharjo pada BIG dengan Sidoarjo pada CSV. Nama CSV dipertahankan. PDF lampiran halaman 2 memang menulis Sidoarjo; identitas administratif padanannya dengan Sidoharjo tetap memerlukan konfirmasi meskipun tidak ada benturan kunci dalam pemetaan.

Penetapan koordinat titik untuk pembobotan GWR didasarkan pada empat landasan metodologis dan teknis berikut.

Pertama, landasan representasi unit areal (areal unit point representation). Dalam implementasi GWR yang diuji, setiap observasi direpresentasikan dengan koordinat titik untuk menghitung jarak geografis antarunit dalam kernel Gaussian. Karena dataset menyajikan harga tanah sebagai atribut agregat tingkat kecamatan (poligon areal) dan bukan lokasi persil transaksi tunggal, penelitian ini memilih satu titik representatif untuk setiap kecamatan. Pilihan ini merupakan penyederhanaan implementasi, bukan satu-satunya representasi wilayah yang mungkin.

Kedua, landasan geometris dan GIS melalui algoritma ST_PointOnSurface dibandingkan centroid biasa. Poligon kecamatan yang berbentuk cekung (concave), memanjang, atau terdiri atas beberapa bagian dapat menyebabkan pusat massa geometris biasa (centroid) jatuh di luar batas kecamatan tersebut. Sebaliknya, algoritma ST_PointOnSurface(ST_Union(geom)) secara matematis memilih titik interior yang dijamin berada di dalam gabungan poligon kecamatan masing-masing.

Ketiga, landasan geodetik melalui proyeksi metrik planar UTM Zona 49S (EPSG:32749). Sebelum penggabungan poligon dan penghitungan ST_PointOnSurface, geometri WGS84 diproyeksikan ke UTM 49S agar operasi spasial berlangsung pada bidang datar bersatuan meter sesuai posisi geografis Solo Raya. Titik kemudian ditransformasikan kembali ke WGS84 (EPSG:4326) untuk menghitung jarak lingkaran besar haversine dengan radius bumi 6.371,0088 km.

Keempat, konstruksi koordinat tidak menggunakan target harga. Koordinat titik ditentukan semata-mata oleh geometri batas administratif BIG tanpa membaca nilai harga tanah aktual. Dengan demikian, harga pada baris Banjarsari sebesar Rp7.678.425/m² tidak berarti harga bidang tepat pada koordinat point-on-surface Banjarsari bernilai demikian, melainkan nilai rata-rata kecamatan yang dilekatkan pada simpul koordinat wilayahnya. Titik ini bukan jaminan lokasi kantor kecamatan, pusat penduduk, pusat perdagangan, atau titik transaksi, dan satu titik menyederhanakan variasi internal wilayah yang rata-rata seluas 47,54 km².

{{COORDINATE_AUDIT}}

Metadata fitur arsip BIG berpenanda 20230928, sedangkan deskripsi layanan menyebut edisi 2022. Kesamaan batas dengan tahun 2020 belum dibuktikan untuk seluruh kecamatan. Status ini membatasi interpretasi hasil spasial sebagai eksperimen dengan proksi geometri administratif yang lebih baru.

{{MAP_FIGURE}}

## 3. Metode Penelitian

### 3.1. Protokol evaluasi dan pencegahan kebocoran data

Evaluasi menggunakan tujuh lipatan luar leave-one-kabupaten/kota-out. Satu kabupaten/kota menjadi data uji dan enam lainnya menjadi data latih. Setiap kecamatan mendapat tepat satu prediksi uji per model. Rancangan kelompok dipilih untuk menilai kemampuan generalisasi ke wilayah administratif yang belum dilatih, sejalan dengan pertimbangan evaluasi data berstruktur dalam Roberts dkk. (2017).

Pada masing-masing lipatan luar, parameter dipilih melalui enam lipatan dalam berdasarkan kabupaten/kota pada bagian latih. Dalam setiap lipatan dalam, lima wilayah menjadi data fit dan satu menjadi validasi. Kriteria pemilihan adalah MAE gabungan semua observasi validasi, bukan rata-rata sederhana MAE wilayah. Bila nilai kriteria sama, kandidat pertama pada urutan grid dipilih. Model dengan parameter terpilih dilatih kembali menggunakan seluruh enam wilayah latih untuk memprediksi wilayah uji luar.

StandardScaler dipasang hanya pada bagian latih setiap pemanggilan model, termasuk pada validasi internal. Nilai target wilayah uji luar tidak digunakan untuk memilih parameter, menghitung standardisasi, atau mengestimasi koefisien. Koordinat wilayah uji digunakan untuk menghitung jaraknya ke lokasi latih, sebagaimana lokasi tujuan prediksi diketahui.

### 3.2. Regresi linear dan Decision Tree

Regresi linear mengestimasi satu intersep dan dua koefisien global. Decision Tree menggunakan pemisahan prediktor berdasarkan ambang nilai, dengan kandidat kedalaman maksimum 2, 4, dan 6; min_samples_leaf=3; serta random_state=124. Keduanya menerima dua prediktor yang sama dengan model lain. Tidak ada pemotongan prediksi negatif setelah estimasi.

### 3.3. K-Nearest Neighbors

KNN menggunakan jarak Euclidean pada ruang dua prediktor yang distandardisasi. Kandidat jumlah tetangga adalah 3, 7, dan 15, dengan bobot invers jarak melalui weights='distance'. Kedekatan pada KNN menyatakan kemiripan atribut, bukan kedekatan geografis. Prediksi merupakan rata-rata berbobot target tetangga; implementasi menangani tetangga berjarak nol sesuai KNeighborsRegressor.

> ŷ(x) = Σᵢ∈Nₖ₍ₓ₎ wᵢyᵢ / Σᵢ∈Nₖ₍ₓ₎ wᵢ

### 3.4. Geographically Weighted Regression

GWR membentuk regresi lokal untuk lokasi uji s menggunakan seluruh observasi latih dan bobot yang menurun menurut jarak. Model menggunakan intersep serta dua prediktor terstandardisasi.

> ŷ(s) = β̂₀(s) + β̂₁(s)x₁(s) + β̂₂(s)x₂(s)

> β̂(s) = arg minᵦ Σᵢ∈T wᵢ(s)[yᵢ − b₀ − b₁xᵢ₁ − b₂xᵢ₂]²

> wᵢ(s) = exp[−dᵢ(s)² / (2h²)]

T merupakan himpunan observasi latih. Jarak d dihitung menggunakan haversine dengan radius bumi 6371,0088 km. Kandidat bandwidth Gaussian tetap adalah 5, 10, 20, dan 40 km. Penyelesaian kuadrat terkecil menggunakan akar bobot; normalisasi log-bobot menghindari underflow tanpa mengubah solusi optimum akibat pengalian semua bobot dengan konstanta positif yang sama.

Rank desain berbobot diperiksa pada setiap regresi lokal. Kandidat yang singular pada salah satu validasi internal ditolak dan dicatat. Jika semua kandidat gagal, eksperimen dihentikan. Singularitas pada prediksi uji luar juga menghentikan eksperimen. Tidak diterapkan ridge atau penggantian model secara diam-diam. Prosedur tersebut mempertahankan keterlacakan kegagalan numerik.

### 3.5. Metrik dan verifikasi

MAE, RMSE, dan R² dihitung atas prediksi out-of-fold. MAE memberi bobot yang sama untuk setiap kecamatan, sedangkan RMSE lebih peka terhadap kesalahan besar. R² gabungan menggunakan rata-rata target seluruh 127 kecamatan.

> MAE = (1/n) Σᵢ |yᵢ − ŷᵢ|

> RMSE = √[(1/n) Σᵢ (yᵢ − ŷᵢ)²]

> R² = 1 − Σᵢ (yᵢ − ŷᵢ)² / Σᵢ (yᵢ − ȳ)²

Verifikasi memeriksa kesamaan kunci dan nilai sumber, 127 prediksi finite setiap model, tujuh blok, 28 baris hasil wilayah, dan menghitung ulang MAE/RMSE gabungan serta setiap wilayah. R² gabungan juga dihitung ulang. Catatan audit memeriksa kesesuaian wilayah latih dan kunci uji. Prediksi sebelum dan setelah refaktor dibandingkan dengan toleransi numerik ketat; parameter, skor seleksi internal, dan pembagian wilayah harus tetap sama.

## 4. Hasil Eksperimen

### 4.1. Kinerja gabungan

{{METRICS}}

KNN memberi MAE terbaik, sedangkan regresi linear memberi RMSE terbaik. MAE GWR sekitar 9,58% lebih tinggi daripada KNN, tetapi RMSE GWR sekitar 7,88% lebih rendah. Perbedaan peringkat menunjukkan bahwa model dengan galat absolut rata-rata terkecil tidak selalu paling baik dalam mengurangi kesalahan besar. GWR belum mengungguli regresi linear pada MAE maupun RMSE gabungan. Ketiga baseline cocok dengan acuan pembulatan MAE: Linear Rp739.020/m², KNN Rp732.073/m², dan Decision Tree Rp756.462/m².

### 4.2. Kinerja per kabupaten/kota

{{REGIONAL_MAE}}

{{REGIONAL_RMSE}}

GWR memiliki MAE lebih kecil daripada regresi linear pada Karanganyar dan Sukoharjo, serta lebih kecil daripada KNN pada Karanganyar dan Surakarta. GWR juga mengungguli Decision Tree dalam MAE pada Boyolali, Karanganyar, dan Sukoharjo. Dengan demikian, peningkatan lokal tidak merata. Seluruh wilayah tetap disertakan pada hasil gabungan.

{{SURAKARTA_DISCUSSION}}

### 4.3. Parameter terpilih dan perilaku prediksi

{{PARAMETERS}}

Bandwidth 40 km terpilih pada enam lipatan, sedangkan 10 km terpilih ketika Surakarta menjadi wilayah uji. Karena enam lipatan memilih ujung atas grid, hasil ini belum membuktikan bahwa bandwidth optimal berada dalam rentang yang dicoba. Grid yang lebih luas dapat menjadi eksperimen lanjutan dengan pemilihan parameter tetap dilakukan di dalam data latih.

{{NEGATIVE_TABLE}}

Tidak ditemukan singularitas pada kandidat bandwidth dan pembagian data yang diuji. Keberhasilan numerik tersebut tidak berarti prediksi selalu layak secara ekonomi. Prediksi negatif pada Linear dan GWR merupakan konsekuensi model tanpa kendala nonnegatif. Prediksi itu tidak dipotong agar perbandingan baseline tetap dapat direproduksi. Model log-harga atau model berkendala dapat diuji secara terpisah; hasil dalam paper ini tetap dilaporkan pada spesifikasi asli.

{{SCATTER_FIGURE}}

## 5. Pembahasan

Eksperimen ini belum memberikan bukti bahwa pembobotan geografis meningkatkan prediksi secara konsisten ketika seluruh kabupaten/kota dikeluarkan dari pelatihan. Kesimpulan berlaku untuk Gaussian GWR dengan dua prediktor, representasi titik yang dipakai, dan grid bandwidth yang ditentukan. Hasil tersebut bukan penolakan terhadap seluruh pendekatan spasial.

Secara metodologis, validasi wilayah menilai tugas yang lebih spesifik daripada merekonstruksi harga pada lokasi yang ikut dilatih. Nilai kecocokan dalam sampel yang baik tidak menjamin kemampuan prediksi lintas kabupaten/kota. Perbandingan dengan studi lain perlu memperhatikan perbedaan unit observasi, variabel, rentang geografis, dan skema validasi, sehingga angka akurasi tidak dibandingkan langsung tanpa konteks.

Dua prediktor yang tersedia belum menangkap seluruh karakter pasar tanah. Jumlah penduduk tidak sama dengan kepadatan, sedangkan jumlah fasilitas tidak menunjukkan jarak, kualitas, kapasitas, atau akses jaringan. Penelitian terdahulu memberi dasar untuk memperluas informasi, tetapi seluruh prediktor tambahan harus memiliki definisi dan tahun yang sesuai. Mengulang satu nilai PDRB kabupaten pada semua kecamatan, misalnya, tidak menjadikannya ukuran ekonomi kecamatan.

Representasi satu titik untuk wilayah luas juga menyederhanakan variasi spasial internal. Titik administratif tidak ditentukan berdasarkan distribusi transaksi. Bila hasil sangat berubah ketika representasi titik diganti, ketidakpastian tersebut harus dibahas, bukan memilih titik yang semata-mata memberi skor terbaik pada uji luar.

Selisih skor yang dilaporkan bersifat deskriptif. Belum dilakukan uji signifikansi perbedaan model, interval ketidakpastian berbasis blok, atau pengujian autokorelasi residual. Penelitian berfokus pada prediksi, sehingga koefisien atau korelasi tidak ditafsirkan sebagai dampak kausal.

## 6. Keterbatasan, Status Audit, dan Pengembangan Lanjutan

Keterbatasan utama adalah definisi harga dan pembentuk rata-ratanya belum sepenuhnya diaudit, geometri BIG lebih baru daripada tahun data, dan identitas administratif padanan Sidoarjo–Sidoharjo masih memerlukan konfirmasi. Ejaan Sidoarjo telah cocok dengan PDF lampiran halaman 2, tetapi hal itu belum membuktikan kesesuaian batas historis. Kesamaan nama dan keberadaan titik di dalam poligon tidak membuktikan kesamaan batas tahun 2020. Seluruh hasil tetap dibatasi pada rata-rata kecamatan tahun 2020. Rangkuman status audit seluruh komponen penelitian disajikan pada tabel berikut.

{{AUDIT_STATUS}}

Pengembangan yang direncanakan mencakup penggantian jumlah penduduk dengan kepadatan penduduk, kemudian penambahan akses pusat kegiatan, akses jalan utama, dan proporsi permukaan terbangun. Kandidat sumber resmi dan kebutuhan verifikasinya dirangkum berikut ini; seluruh data tersebut belum menjadi bagian hasil pada bagian 4.

{{CANDIDATE_SOURCES}}

### 6.1. Perluasan kandidat berbasis literatur

Sebanyak 25 kandidat dirumuskan, termasuk dua prediktor baseline; sebagian merupakan alternatif operasionalisasi konsep yang sama. Daftar ini merupakan agenda pengumpulan dan pengujian, bukan dataset tambahan yang telah lengkap. Berawi dkk. (2018) mendukung pengujian akses stasiun, Huang dan Hewings (2021) mendukung pengujian kemiringan lereng, serta Zhang dkk. (2021) mendukung penggunaan POI dan cahaya malam untuk pemodelan harga tanah. Arafah dkk. (2026) menguji 14 prediktor pada NJOP 2025 di Banda Aceh dan tidak menemukan signifikansi pada seluruh kandidat; konteks tersebut tidak disamakan dengan target Solo Raya 2020.

{{CANDIDATE_REGISTRY}}

Kode sumber: R1 Aziz dkk. (2023); R2 Saefuddin dkk. (2012); R3 Syahar dkk. (2020); R4 Arumingtyas dkk. (2019); R5 Berawi dkk. (2018); R6 Huang dan Hewings (2021); R7 Zhang dkk. (2021); R8 Arafah dkk. (2026). Kode menunjukkan landasan konsep; definisi tingkat kecamatan dan sejumlah variabel turunan merupakan adaptasi penelitian ini, bukan variabel yang semuanya telah terbukti signifikan. Rincian dukungan langsung/adaptasi, satuan, tahun dan status data tersedia dalam data/kandidat_variabel.csv dan docs/PENGEMBANGAN_VARIABEL.md.

### 6.2. Rencana pemeriksaan korelasi dan seleksi

Spearman direncanakan sebagai layar eksplorasi utama dan Pearson sebagai pemeriksaan sensitivitas; arah, besar koefisien, jumlah observasi, outlier dan kestabilan antarwilayah dilaporkan. Apabila p-value eksploratif dihitung, seluruh keluarga uji yang ditetapkan dilaporkan beserta koreksi Benjamini–Hochberg (1995). Koreksi pengujian berganda tidak memperbaiki asumsi independensi yang dilanggar oleh ketergantungan spasial. P-value standar diperlakukan sebagai nominal/eksploratif sampai prosedur inferensi spasial yang sesuai ditetapkan. Korelasi bukan pengaruh kausal, dan p-value terkecil bukan ukuran manfaat prediksi terbaik.

Untuk pengembangan model, imputasi, penyaringan korelasi dan seleksi fitur hanya memakai bagian fit setiap lipatan dalam; pilihan fitur serta parameter dinilai pada validasi dalam, kemudian prosedur dipasang kembali pada seluruh data latih luar. Matriks antarprediktor, VIF dan rank desain lokal diperiksa. Jumlah penduduk dan kepadatan, jumlah fasilitas dan kepadatan fasilitas, serta beberapa ukuran urbanisasi diperlakukan sebagai kandidat yang berpotensi redundan. Semua 25 kandidat tidak dimasukkan sekaligus ke GWR. Korelasi eksploratif seluruh sampel dilaporkan pada bagian 6.3; evaluasi tujuh prediktor disajikan pada bagian 6.4. Hasil eksplorasi ini tidak dipakai untuk memilih fitur lalu mengklaim evaluasi independen pada data yang sama.


{{FUTURE_EXPERIMENTS}}

Pusat kegiatan harus ditetapkan dari dokumen independen, bukan dari harga tanah tertinggi. Untuk menguji efek representasi lokasi saja, prediktor aksesibilitas dipertahankan saat titik pembobotan GWR diganti. Jika aksesibilitas turut dihitung ulang, perubahan tersebut dilaporkan sebagai skenario gabungan. Penambahan variabel perlu mempertimbangkan kolinearitas serta jumlah observasi efektif pada regresi lokal.

### 6.3. Pengolahan variabel pendukung dan eksplorasi awal

Pengolahan tambahan menghasilkan lima variabel untuk seluruh 127 kecamatan: proporsi terbangun, cropland dan tutupan pohon dari ESA WorldCover 2020 v100 (Zanaga dkk., 2021, DOI 10.5281/zenodo.5571936), serta kepadatan penduduk dan fasilitas menggunakan luas arsip BIG. Dua tile S09E108 dan S09E111 dibaca pada resolusi asli; piksel dimasukkan berdasarkan pusatnya di dalam poligon, kemudian luas piksel elipsoid digunakan sebagai bobot. Proporsi kelas dihitung terhadap luas piksel valid. Seluruh piksel terpilih berkelas valid; hal ini bukan ukuran akurasi klasifikasi. Batas poligon pada tepi piksel merupakan pendekatan dan geometri historis 2020 masih belum terverifikasi. Kedua kepadatan disebut proksi, bukan statistik resmi kepadatan 2020.

Cropland tidak identik dengan sawah; tree cover tidak identik dengan taman; built-up bukan luas tapak bangunan. Proporsi kelas utama tidak mencakup seluruh kelas; tabel keluaran juga menyimpan semua 11 kelas untuk pemeriksaan jumlah 100%. Data ini berasal dari ESA, bukan ekstraksi layer BHUMI. Katalog ATLAS tentang sawah, akses kesehatan, dan bahaya gunung api belum diolah karena metadata dan data numeriknya belum diperoleh.

**Dataset dan satuan pengamatan.** Setiap baris mewakili satu kecamatan pada tahun 2020. Pasangan nama kabupaten/kota dan kecamatan menghubungkan tiga sumber berikut. Setiap kecamatan mendapat bobot yang sama dalam ringkasan dan korelasi.

| Sumber data | Kolom yang digunakan | Cara memperoleh nilai kecamatan |
| --- | --- | --- |
| Lampiran A Salim Aziz | Penduduk, jumlah fasilitas umum regional, harga rata-rata (Rp/m²) | Angka per kecamatan ditranskripsi dan dicocokkan dengan lampiran. Harga menjadi variabel target. |
| Poligon BIG dan jumlah dari Lampiran A | Kepadatan penduduk (jiwa/km²), kepadatan fasilitas regional (unit/km²) | Masing-masing jumlah dibagi luas poligon kecamatan yang dihitung dalam UTM 49S. |
| ESA WorldCover 2020 v100 dan poligon BIG | Persentase terbangun, tanaman budidaya (cropland), tutupan pohon | Luas piksel valid pada kelas yang bersangkutan dibagi total luas piksel valid kecamatan, kemudian dikalikan 100. |

Contoh satu baris pada dataset adalah Banjarsari, Kota Surakarta. Luas arsipnya 15,4864 km². Pembagian 168.770 penduduk dan 9 fasilitas regional dengan luas tersebut menghasilkan 10.897,95 jiwa/km² dan 0,581 unit/km². WorldCover mencatat 80,79% terbangun, 1,67% tanaman budidaya dan 14,33% tutupan pohon. Harga yang dipasangkan dengan baris tersebut adalah Rp7.678.425/m².

**Sebaran nilai.** Tabel menunjukkan median, rentang tengah 50% kecamatan (Q1–Q3), serta nilai minimum dan maksimum. Seluruh variabel memiliki 127 nilai terisi. Sebanyak 99 kecamatan memiliki jumlah fasilitas regional tercatat nol. Karena itu median dan kedua kuartil kepadatan fasilitas bernilai nol. Definisi fasilitas mengikuti kategori regional dalam sumber.

{{STATISTIK_VARIABEL}}

![Median lima variabel tambahan menurut kabupaten/kota. Angka dalam kurung menunjukkan jumlah kecamatan. Intensitas biru dibandingkan di dalam masing-masing kolom; setiap kolom memakai skala sendiri.](../artifacts/analisis_variabel/profil_wilayah.png)

Lima kecamatan di Kota Surakarta memiliki median terbangun 84,95% dan median kepadatan penduduk 10.898 jiwa/km². Di antara 25 kecamatan Wonogiri, median kedua variabel masing-masing 2,99% dan 543 jiwa/km². Median ini menggambarkan kecamatan tipikal dalam setiap wilayah. Persentase tutupan seluruh kabupaten memerlukan pembobotan menurut luas.

![Harga teramati terhadap setiap variabel tambahan. Satu titik mewakili satu kecamatan pada 2020. Semua panel memakai skala harga yang sama. Titik jingga menandai lima kecamatan Kota Surakarta.](../artifacts/analisis_variabel/sebaran_harga.png)

**Perhitungan korelasi.** Pearson dihitung pada nilai asli dengan rumus r = kovarians(X,Y) / (sX × sY), dengan kovarians dan simpangan baku sampel memakai penyebut n − 1. Sebagai contoh, ambil X sebagai persentase terbangun dan Y sebagai harga dalam juta Rp/m². Pada 127 kecamatan, r = 31,52068 / (17,27303 × 2,04426) ≈ 0,893. Untuk Spearman, nilai X dan Y masing-masing diubah menjadi peringkat, nilai yang sama diberi peringkat rata-rata, lalu rumus Pearson diterapkan pada kedua deret peringkat. Pasangan terbangun dan harga menghasilkan ρ = 0,676. Penghitungan menggunakan seluruh presisi angka sumber sebelum pembulatan.

{{KORELASI_HARGA}}

![Korelasi tujuh prediktor dan harga untuk 127 kecamatan. Untuk setiap pasangan, sel di atas diagonal memberikan Pearson dan sel cerminnya di bawah diagonal memberikan Spearman. Merah menunjukkan hubungan positif dan biru hubungan negatif.](../artifacts/analisis_variabel/matriks_korelasi.png)

Proporsi terbangun memiliki hubungan positif paling kuat dengan harga menurut kedua ukuran. Hubungan liniernya lebih kuat daripada hubungan peringkatnya. Diagram sebar memperlihatkan pengelompokan lima kecamatan Surakarta di ujung atas proporsi terbangun dan harga. Untuk tanaman budidaya, Pearson bernilai −0,180 dan Spearman 0,050, sehingga urutan kecamatan menurut persentase tanaman budidaya hampir tidak berkaitan dengan urutan harga. Proporsi terbangun dan kepadatan penduduk sendiri berkorelasi kuat (r = 0,952; ρ = 0,950). Keduanya membawa informasi yang tumpang tindih. Koefisien bersifat deskriptif pada sampel gabungan; perbedaan antarwilayah dapat ikut membentuk hubungan tersebut. Analisis tidak menggunakan korelasi ini untuk memilih prediktor atau menyimpulkan sebab-akibat.

Peta interaktif menampilkan poligon yang disederhanakan 40 meter untuk visualisasi, sedangkan statistik dihitung dari geometri penuh. Dataset, manifest sumber/hash dan tabel korelasi tersedia pada data/processed; cara reproduksi dan keterbatasan dicatat dalam docs/PENGOLAHAN_VARIABEL_2020.md.

### 6.4 Eksperimen tujuh prediktor dan sensitivitas koordinat

Kelima variabel pada bagian 6.3 ditambahkan pada jumlah penduduk dan fasilitas. Empat estimator NumPy dari notebook menggunakan tujuh lipatan luar yang sama dengan bagian 4. Rerata dan simpangan baku setiap fitur dihitung pada bagian latih. Model dilatih pada ln(harga) dan prediksinya dikembalikan ke Rp/m² dengan eksponensial tanpa koreksi retransformasi. Dengan cara ini, galat positif besar pada skala log dapat membesar pada skala rupiah.

KNN menggunakan lima tetangga dengan bobot kebalikan jarak dalam ruang prediktor. Pohon CART memiliki kedalaman maksimum empat, minimal enam observasi untuk membelah simpul dan tiga per daun. Parameter keduanya ditetapkan mengikuti notebook. Regresi linear global menggunakan penalti numerik 10⁻⁸ dan GWR Gaussian memakai penalti 10⁻³, termasuk pada intersep. Bandwidth dipilih dari 5, 10, 15, 25, 40, 60 dan 80 km berdasarkan RMSE gabungan pada enam lipatan validasi internal. Standardisasi dipasang kembali pada setiap bagian latih internal. Koordinat hanya digunakan oleh GWR. Tabel melaporkan skor gabungan dari 127 prediksi uji per model dengan titik BIG.

{{COLAB_METRICS}}

![Gambar. Evaluasi tujuh prediktor dengan titik BIG. Garis putus-putus menunjukkan prediksi tepat. Warna panel kanan menggunakan skala logaritmik.]({{FIGUR_TUJUH_PREDIKTOR}})

Untuk mengukur kontribusi lima fitur secara bersama, KNN dilatih ulang dengan dua prediktor awal. Target log, bobot, k, standardisasi dan lipatan dipertahankan. Penambahan fitur menurunkan MAE dari Rp733.681 menjadi Rp619.531/m² (15,6%) dan RMSE dari Rp1.585.546 menjadi Rp1.309.859/m². Pada lipatan Surakarta, MAE KNN tujuh fitur masih mencapai Rp3.958.006/m². Laweyan memiliki harga aktual Rp11.800.794/m² dan prediksi sekitar Rp3,80 juta/m².

Replikasi dengan koordinat kiriman menghasilkan MAE GWR Rp4.633.597/m² dan RMSE Rp30.928.350/m². Pada arsip BIG, titik kiriman Ampel dan Wonosegoro berada di luar poligon padanannya. Pengulangan dengan 127 titik interior BIG menghasilkan angka pada tabel. Pada eksperimen tujuh prediktor, GWR memperoleh MAE lebih rendah daripada regresi linear global, tetapi lebih tinggi daripada KNN dan pohon. Perbandingan dengan model linear juga melibatkan perbedaan penalti. Lima kecamatan Surakarta menyumbang 99,66% jumlah kuadrat galat GWR dengan titik BIG. Semua regresi lokal menghasilkan prediksi finite. Pada protokol awal, matriks desain lokal yang kehilangan rank menggugurkan kandidat bandwidth dan dicatat di audit. Tidak terjadi kegagalan singular pada run awal ini. Pada protokol notebook, penalti ridge menstabilkan penyelesaian sistem lokal. Besarnya galat di Surakarta terjadi meskipun sistem dapat diselesaikan.

VIF deskriptif pada seluruh sampel mencapai 36,65 untuk proporsi terbangun dan 24,27 untuk tutupan pohon. Nilai ini menunjukkan redundansi linear antarprediktor dan membatasi interpretasi koefisien individual. Seluruh tujuh fitur tetap digunakan di setiap lipatan. Perbandingan model dilaporkan secara deskriptif karena kecamatan dalam satu blok berbagi wilayah uji dan lipatan menggunakan data latih yang tumpang tindih. Klaim signifikansi Wilcoxon per kecamatan dari notebook memerlukan penanganan ketergantungan tersebut.

### 6.5 Akses wisata, kampus dan topografi

Untuk menguji apakah galat di sekitar Tawangmangu juga muncul di wilayah lain, kami menambah empat variabel yang terukur untuk semua 127 kecamatan. Dari titik interior tiap kecamatan, kami hitung jarak lingkaran besar ke objek wisata dan kampus terpetakan terdekat, termasuk objek di luar batas kecamatan. Sumbernya © OpenStreetMap contributors, ekstrak Geofabrik Indonesia 1 Januari 2021. Klasifikasi, cakupan pemetaan dan posisi titik interior memengaruhi nilai jarak. Median elevasi dan kemiringan dihitung atas sel valid di dalam poligon BIG dari SRTM v4.1 CIAT. Untuk Tawangmangu, elevasi median mencapai 1.218 m, lereng median 15,1°, jarak wisata 0,14 km dan jarak kampus 22,44 km.

Riswandha dan Wahyono (2017) mendokumentasikan perubahan penggunaan lahan di kawasan wisata Tawangmangu. Wang (2023) mempelajari kedekatan kampus dan harga rumah di Amerika Serikat. Huang dan Hewings (2021) menguji peran lereng terhadap harga tanah di Auckland. Perbedaan unit analisis dan pasar membatasi penerapan hasil studi tersebut ke Solo Raya.

![Hubungan empat variabel baru dengan harga rata-rata kecamatan. Titik jingga menandai Tawangmangu. Korelasi dihitung pada angka asli dan peringkat, sedangkan sumbu vertikal logaritmik membantu membaca rentang harga.](../artifacts/akses_medan/akses_medan.png)

Setiap konfigurasi diuji pada tujuh blok luar yang sama. Enam blok latih digunakan untuk memilih parameter dengan MAE gabungan pada validasi internal lintas wilayah. Model dilatih pada ln(harga). GWR menggunakan kernel Gaussian dengan bandwidth tetap (15 atau 40 km) atau adaptif (jarak ke tetangga latih ke-12, 32 atau 64). Ridge menstabilkan estimasi lokal ketika prediktor saling berkaitan (Wheeler, 2007). Bobot dinormalisasi agar jumlahnya satu, dengan penalti koefisien 0,01, 0,1 atau 1 dan intersep bebas penalti. Ridge global menyediakan pembanding dengan bobot seragam. Untuk KNN, k dipilih dari 3, 5, 7 atau 15. Kedalaman pohon dipilih dari 2, 4 atau 6, dengan sedikitnya tiga observasi per daun.

Tabel menampilkan MAE dalam Rp/m². Setiap baris berangkat dari tujuh prediktor awal. Medan menambah elevasi dan lereng, akses menambah dua jarak, dan gabungan menambah keempat fitur. Dua baris log1p merupakan uji sensitivitas setelah melihat galat besar model regresi. Seluruh prediktor ditransformasi sebagai ln(1+x) sebelum standardisasi pada data latih.

{{HASIL_AKSES}}

Jarak kampus memberi perbaikan terbesar pada KNN dengan MAE Rp610.868/m² dan RMSE Rp1.263.634/m². Pada protokol tuning yang sama, KNN dasar menghasilkan MAE Rp633.139/m² dan RMSE Rp1.332.087/m². Di Tawangmangu galat absolut justru meningkat dari Rp1.627.410 menjadi Rp1.666.854/m². Sebaliknya, galat menurun di Ngargoyoso (Rp929.563 menjadi Rp923.471), Matesih (Rp575.507 menjadi Rp506.850), Grogol (Rp5.490.398 menjadi Rp4.579.782) dan Kartasura (Rp2.812.738 menjadi Rp1.720.349). Laweyan masih memiliki galat terbesar, Rp7.800.101/m². Jarak terdekat hanya mengukur satu dimensi akses. Intensitas kunjungan dan lokasi transaksi di dalam kecamatan tetap tidak teramati.

Pada sebelas prediktor skala asli, GWR ridge menghasilkan RMSE Rp58.962.639/m². Saat Surakarta ditahan, MAE mencapai Rp215.847.140/m² meski bilangan kondisi maksimum sistem setelah penalti hanya 6,08. Sistem lokal berhasil diselesaikan, tetapi ekstrapolasi pada skala log menghasilkan prediksi rupiah yang sangat besar. Transformasi prediktor log1p menurunkan MAE GWR gabungan menjadi Rp3.801.444/m² dan RMSE menjadi Rp23.633.260/m². Ridge global pada transformasi yang sama tetap lebih baik. Dengan demikian, eksperimen ini belum menunjukkan manfaat tambahan pembobotan geografis untuk generalisasi lintas kabupaten/kota. Kandidat fitur muncul setelah peninjauan galat dan seluruh perbandingan memakai kembali tujuh blok yang sama. Validasi pada wilayah atau tahun independen diperlukan sebelum memilih spesifikasi untuk penggunaan baru.

### 6.6 Kepadatan, konsentrasi wisata dan pengujian galat besar

Dataset analisis menyatukan harga tahun 2020, kepadatan penduduk (jiwa/km²), lahan terbangun (%), jumlah objek wisata dalam 5 km, jarak wisata dan kampus terdekat (km), elevasi (m) dan kemiringan (derajat). Radius dihitung dari titik interior kecamatan dan dapat melintasi batas wilayah. Satu tujuan wisata dapat memiliki beberapa objek dalam arsip OSM. Sumber dan keterbatasan waktu mengikuti bagian 6.3 dan 6.5.

{{UJI_KORELASI}}

Pearson dan Spearman gabungan memakai 127 observasi. Untuk menguji hubungan di dalam wilayah, kedua variabel diubah ke peringkat gabungan dengan peringkat rata-rata untuk nilai seri, lalu peringkat dikurangi rerata kabupaten/kota masing-masing. Kolom dalam blok adalah korelasi kedua peringkat terpusat. Uji dua sisi memakai 9.999 pengacakan peringkat harga di dalam kabupaten/kota, koreksi tambah satu dan koreksi Bonferroni untuk tujuh pengujian. Interpretasi nilai p mengasumsikan peringkat dapat dipertukarkan di dalam blok. Autokorelasi spasial di antara kecamatan berdekatan masih dapat melanggar asumsi ini. Hasil korelasi memakai seluruh sampel dan tidak digunakan untuk menyetel model.

Untuk menguji galat besar, Ridge global dan GWR Gaussian dilatih langsung pada harga dalam Rp/m². Prediksi negatif diberi batas bawah nol. Lima spesifikasi diuji: kepadatan saja, kepadatan dan lahan terbangun, tambahan ln(1+jumlah objek wisata), elevasi dan lereng, lalu alternatif dengan interaksi elevasi × ln(1+jumlah objek) atau tambahan kedua jarak. Penalti koefisien dipilih dari 0,01, 0,1 atau 1, dengan bandwidth GWR 15, 40 atau 80 km. Standardisasi dipasang ulang pada setiap bagian latih. Pembanding lima variabel memilih parameter melalui MAE internal. Prosedur seleksi RMSE memilih sekaligus spesifikasi, model dan parameter melalui RMSE gabungan enam blok internal. Harga wilayah uji luar hanya dipakai saat evaluasi. Tabel merangkum prediksi lintas tujuh wilayah.

{{UJI_SELEKSI}}

Di Tawangmangu, empat objek wisata berada dalam radius pengukuran. Ridge lima variabel memprediksi Rp1.376.791/m² terhadap harga aktual Rp1.767.344/m². Saat Karanganyar ditahan, seleksi internal memilih kepadatan dan lahan terbangun saja sehingga prediksi turun ke Rp385.175/m². Saat Surakarta ditahan, seleksi internal memilih GWR dua variabel dengan bandwidth 15 km. Prediksi Pasar Kliwon mencapai batas bawah nol. Galat besar ini menunjukkan risiko ekstrapolasi ke wilayah perkotaan yang lebih padat daripada seluruh data latih. Evaluasi bersifat eksploratif karena rancangan fitur berangkat dari peninjauan galat sebelumnya.

## 7. Kesimpulan

Pada spesifikasi awal dua prediktor untuk 127 kecamatan Solo Raya tahun 2020, KNN menghasilkan MAE terendah sebesar Rp732.073/m², sedangkan regresi linear menghasilkan RMSE terendah sebesar Rp1.355.435/m². GWR Gaussian menghasilkan MAE Rp802.227/m² dan RMSE Rp1.409.692/m². Pembobotan geografis pada spesifikasi yang diuji belum memberikan keunggulan prediktif konsisten dalam validasi lintas kabupaten/kota.

Eksperimen menghasilkan 127 prediksi uji per model, tujuh lipatan per model, dan 28 baris evaluasi wilayah. Dalam eksperimen tujuh prediktor, KNN berbobot mencatat MAE dan RMSE gabungan terendah. Hasil pembanding KNN menunjukkan bahwa kepadatan dan tutupan lahan secara bersama membantu prediksi lintas wilayah pada data ini. Pengembangan berikutnya perlu mengutamakan audit sumber harga dan batas historis, penambahan prediktor yang terukur, serta pengujian sensitivitas koordinat dan bandwidth. Kesimpulan tidak digunakan untuk harga bidang tanah atau prediksi harga tahun berjalan.

## 8. Ketersediaan Kode, Data, dan Reproduksi

Repository penelitian: https://github.com/sqiftree/LandPredict. Kode disusun dalam package tanah: config untuk konfigurasi, data untuk validasi input, models untuk estimator, selection untuk validasi internal, experiment untuk orkestrasi, verification untuk pemeriksaan hasil, coordinates dan spatial_audit untuk geometri, reporting dan diagnostics untuk artefak paper, serta provenance untuk hash dan lingkungan. Skrip CLI lama tetap tersedia sebagai adapter.

Tiga keluaran utama adalah metrik.csv, per_wilayah.csv, dan prediksi_uji.csv. Catatan audit menyimpan versi pustaka, hash sumber, grid parameter, skor validasi internal, dan lipatan. Folder artifacts menyimpan hasil acuan yang dapat dibandingkan dengan eksekusi ulang. Geometri diarsipkan dalam gzip beserta hash untuk dekompresi tanpa jaringan. Tanggal pengambilan arsip mengikuti catatan sesi sebelumnya dan belum didukung log unduhan bertimestamp yang independen.

Lingkungan uji menggunakan Python 3.12 dan dependensi yang dicatat pada hasil/requirements-resolved.txt. Reproduksi dijalankan dengan python scripts/reproduce.py setelah dependensi Python dan GDAL tersedia, atau melalui container Docker sesuai README. Pipeline memulihkan geometri, menghitung ulang titik, menjalankan baseline dan GWR, memverifikasi hasil, lalu membuat peta dan diagnostik. Pipeline berhenti ketika pemeriksaan gagal.

## Referensi

{{REFERENCES}}

Jarvis, A., Reuter, H. I., Nelson, A. & Guevara, E. (2008). Hole-filled seamless SRTM data V4. CIAT. https://srtm.csi.cgiar.org/srtmdata/

OpenStreetMap contributors. Ekstrak Indonesia, Geofabrik, 1 Januari 2021. https://download.geofabrik.de/asia/indonesia-210101-free.shp.zip

Riswandha, Y. & Wahyono, H. (2017). Pengaruh kegiatan wisata terhadap perubahan penggunaan lahan di Kecamatan Tawangmangu, Kabupaten Karanganyar. Teknik PWK 6(2), 131–141. https://doi.org/10.14710/tpwk.2017.18052

Wang, B. (2023). The Effect of Proximity to Universities on House Prices after the COVID Outbreak. Journal of Risk and Financial Management 16(3), 167. https://doi.org/10.3390/jrfm16030167

Huang, Y. & Hewings, G. (2021). More Reliable Land Price Index: Is There a Slope Effect? Land 10(3), 261. https://doi.org/10.3390/land10030261

Wheeler, D. C. (2007). Diagnostic Tools and a Remedial Method for Collinearity in Geographically Weighted Regression. Environment and Planning A 39, 2464–2481. https://doi.org/10.1068/a38325

## Lampiran: Status dan Kontribusi Tim

Naskah ini merupakan draf empiris berdasarkan eksperimen dua hingga sebelas prediktor. Bagian 6.3 dan 6.4 melaporkan pengolahan data, eksperimen tujuh prediktor, dan uji sensitivitas koordinat. Identitas anggota dan kontribusi aktual perlu dilengkapi tim sebelum penyerahan.

{{CONTRIBUTIONS}}
