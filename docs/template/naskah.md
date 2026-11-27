# Estimasi Harga Tanah Rata-Rata Kecamatan di Solo Raya Tahun 2020: Perbandingan Geographically Weighted Regression dan Model Nonspasial dengan Validasi Lintas Kabupaten/Kota

## Abstrak

Penelitian ini menguji apakah pembobotan geografis membantu memperkirakan harga tanah rata-rata tingkat kecamatan ketika seluruh kabupaten/kota tujuan dikeluarkan dari data latih. Dataset mencakup 127 kecamatan di tujuh kabupaten/kota Solo Raya tahun 2020 dari kompilasi sekunder Lampiran A penelitian Salim Aziz. Protokol konfirmatori utama membandingkan Geographically Weighted Regression (GWR) Gaussian klasik dengan regresi linear, K-Nearest Neighbors (KNN), dan Decision Tree pada dua prediktor sumber (jumlah penduduk dan jumlah fasilitas umum regional), skala target Rp/m², serta tujuh lipatan luar *leave-one-kabupaten/kota-out* (LOKO) dengan standardisasi dan penyetelan parameter di dalam bagian latih. Pada protokol terkunci 127 kecamatan, KNN menghasilkan MAE terendah Rp732.073/m² dan regresi linear menghasilkan RMSE terendah Rp1.355.435/m² (R² 0,557), sedangkan GWR menghasilkan MAE Rp802.227/m² (selisih +Rp63.207/m² terhadap regresi linear; interval kepercayaan bootstrap blok 95%: +Rp16.219 hingga +Rp163.778/m²). Pada enam kabupaten non-Surakarta (122 kecamatan), KNN tetap terendah dalam MAE (Rp525.199/m²), sementara lima kecamatan Kota Surakarta memicu *domain shift* perkotaan ekstrem yang berada di luar *Area of Applicability* (AoA) ruang fitur pelatihan. Analisis sensitivitas eksploratif menunjukkan bahwa penambahan tutupan lahan ESA WorldCover 2020 dengan penyaringan multikolinearitas (VIF ≤ 2,05) dan kendala nonnegatif menurunkan MAE Ridge global setara hingga Rp496.144/m² (R² 0,822), sedangkan GWR berperan lebih kuat dalam meredam autokorelasi spasial residual (Moran's I turun menjadi 0,073; p = 0,120) daripada melampaui akurasi prediksi lintas kabupaten. Karena definisi pengukuran primer harga dan ukuran sampel pembentuk rata-rata kecamatan belum tervalidasi ke ATR/BPN, seluruh temuan dibatasi untuk evaluasi metodologis rata-rata kecamatan tahun 2020 dan tidak ditujukan bagi penilaian persil, penetapan pajak, atau kebijakan praktis.

Kata kunci: harga tanah; GWR; validasi spasial lintas wilayah; domain shift; Area of Applicability; Solo Raya.

## 1. Pendahuluan

Harga tanah bervariasi secara spasial mengikuti aglomerasi penduduk, ketersediaan fasilitas, aksesibilitas, dan intensitas terbangun wilayah. Dalam dataset penelitian ini, rata-rata harga tanah Kecamatan Laweyan tercatat Rp11.800.794/m², sedangkan Kecamatan Jebres di kota yang sama tercatat Rp6.269.466/m² dan sejumlah kecamatan pedesaan di Wonogiri berada di bawah Rp60.000/m². Rentang yang lebar tersebut menimbulkan pertanyaan metodologis yang spesifik: ketika model dilatih pada enam kabupaten/kota di Solo Raya, apakah pembobotan kedekatan geografis membantu memperkirakan rata-rata harga tanah kecamatan pada satu kabupaten/kota yang sama sekali tidak dilibatkan dalam pelatihan?

Aziz, Rahayu, dan Istanabi (2023) meneliti struktur polisentris Surakarta Raya melalui karakteristik penggunaan lahan, harga lahan, penduduk, dan fasilitas umum. Studi tersebut memberikan konteks kewilayahan, tetapi menggunakan pengelompokan klaster alih-alih evaluasi prediksi lintas batas administratif. Kajian nilai tanah di berbagai kota Indonesia juga mendokumentasikan kaitan aksesibilitas dan fasilitas terhadap harga lahan. Saefuddin dkk. (2012) membandingkan OLS dan GWR di Tangerang Selatan dengan prediktor jalan arteri, gerbang tol, dan fasilitas umum. Syahar dkk. (2020) menelaah hubungan pusat kegiatan, perubahan penggunaan lahan, dan risiko bencana terhadap nilai tanah di Padang. Di Jawa Tengah, Arumingtyas, Subiyanto, dan Firdaus (2019) membedakan harga pasar bidang tanah dan Nilai Jual Objek Pajak (NJOP) di Kelurahan Tlogosari Kulon, Semarang, sedangkan Janssen, Mulder, dan Yudhistira (2022) memberi konteks pemilahan spasial kelompok pendapatan di Jakarta. Temuan pada tingkat bidang atau kelurahan tersebut menjadi pijakan konseptual, tetapi tidak menjamin daya prediksi yang sama ketika data diagregasikan ke unit kecamatan dan diuji lintas kabupaten/kota.

Geographically Weighted Regression (GWR) mengizinkan koefisien regresi berubah menurut koordinat lokasi melalui pembobotan jarak (Brunsdon dkk., 1996). Meski fleksibel menangkap heterogenitas lokal di dalam sampel latih, GWR menghadapi tiga tantangan serius saat memprediksi wilayah administratif baru: kerentanan terhadap multikolinearitas lokal (Wheeler, 2007), penyempitan sampel efektif ketika memprediksi ke seberang batas kabupaten/kota, serta pergeseran distribusi fitur (*domain shift*) apabila wilayah uji memiliki intensitas perkotaan yang melampaui cakupan data latih (Meyer & Pebesma, 2021).

Penelitian ini merancang evaluasi yang memisahkan secara tegas pengujian hipotesis konfirmatori dari eksplorasi pasca-evaluasi. Kontribusi utamanya mencakup: (1) evaluasi konfirmatori terkunci empat keluarga model pada tujuh lipatan luar *leave-one-kabupaten/kota-out* (LOKO) yang dilengkapi interval kepercayaan bootstrap blok kabupaten/kota, metrik terpisah dengan dan tanpa Kota Surakarta, analisis *Area of Applicability* (AoA), serta pengujian autokorelasi spasial residual (Global dan Local Moran's I); (2) audit transparan atas keterbatasan validitas data target sekunder, ketidakselarasan waktu antarsumber, serta perilaku prediksi negatif; dan (3) diagnostik metodologis terkendali untuk memisahkan pengaruh multikolinearitas lokal, bias retransformasi logaritmik (koreksi Duan smearing dan model *log-link* Quasi-Poisson), sensitivitas titik representatif kecamatan, serta keadilan penyetelan antarmode. Penelitian tidak mengasumsikan GWR harus unggul sebagai model prediksi utama.

## 2. Data dan Wilayah Penelitian

### 2.1. Cakupan, validitas target, dan keselarasan temporal sumber

Wilayah penelitian meliputi seluruh 127 kecamatan di tujuh kabupaten/kota Solo Raya: Kota Surakarta serta Kabupaten Boyolali, Karanganyar, Klaten, Sragen, Sukoharjo, dan Wonogiri. Tabel utama berasal dari transkripsi Lampiran A penelitian Salim Aziz di Repositori Universitas Sebelas Maret (UNS) untuk tahun acuan 2020. Keempat halaman tabel pada berkas PDF sumber (nomor cetak A-1, A-2, A-3, dan B-1) telah diperiksa secara visual dan komputasional; label urutan lama A-4 pada 21 kecamatan Kabupaten Klaten telah dipetakan ulang pada berkas `dataset_2020_rujukan_terverifikasi.csv` tanpa mengubah nilai numerik eksperimen. Ringkasan distribusi kecamatan, rata-rata dan rentang harga, jumlah penduduk, jumlah fasilitas regional, serta luas poligon tiap wilayah disajikan berikut ini.

{{REGION_COUNTS}}

Kelemahan pengukuran paling mendasar pada dataset ini terletak pada belum tervalidasinya definisi operasional variabel target di tingkat sumber primer. Audit tanggal 17 November 2026 memastikan 127 kunci wilayah dan seluruh 381 sel numerik pada CSV cocok 100% dengan PDF Lampiran A. Namun, kecocokan salinan hanya membuktikan ketepatan transkripsi sekunder. Artikel Aziz dkk. (2023, Gambar 4–5 hlm. 147) mengatribusikan peta harga lahan ke portal Bhumi ATR/BPN tahun 2020. Meskipun dokumentasi resmi Bhumi dan standar atribut Permen ATR/BPN No. 1 Tahun 2025 mengenal layer Zona Nilai Tanah (ZNT), arsip digital ZNT tahun 2020, metode perataan dari poligon zona ke satu angka kecamatan, maupun jumlah sampel pembentuk di tiap kecamatan belum tersedia untuk diaudit. Tabel berikut merangkum status bukti validitas target beserta batasan klaim yang diterapkan di seluruh naskah.

{{TARGET_VALIDITY_TABLE}}

Selain ketidakpastian definisi primer harga, pemeriksaan silang antara Lampiran A dan tabel ringkas dalam artikel Aziz dkk. (2023) menunjukkan perbedaan angka agregat yang perlu dicatat terbuka.

{{SOURCE_AUDIT}}

Karena analisis sensitivitas pada Bagian 6 turut menggabungkan geometri batas administratif, tutupan lahan satelit, objek lokasi OpenStreetMap, dan model elevasi digital, keselarasan waktu antar-sumber juga harus diperiksa agar proksi pasca-2020 tidak ditafsirkan seolah-olah pengukuran serentak tahun 2020.

{{TEMPORAL_ALIGNMENT_TABLE}}

### 2.2. Variabel pada eksperimen konfirmatori utama

Untuk menjaga kemurnian evaluasi konfirmatori, eksperimen utama pada Bagian 4 dikunci hanya pada variabel yang tersedia langsung di tabel sumber tahun 2020 tanpa penambahan fitur pasca-eksplorasi. **Metrik keputusan utama** ditetapkan pada skala asli Rp/m² (MAE dan RMSE gabungan) karena tujuan tugas adalah menaksir besaran rata-rata harga wilayah dalam satuan moneter, bukan sekadar mengurutkan peringkat logaritmik.

{{VARIABLES}}

Jumlah penduduk mewakili skala demografis kecamatan dan jumlah fasilitas umum regional mewakili ketersediaan layanan berskala wilayah menurut klasifikasi sumber. Keduanya dipakai murni sebagai prediktor statistik tanpa klaim hubungan kausal. Sebanyak 99 dari 127 kecamatan memiliki nilai fasilitas umum regional nol pada tabel sumber sehingga sebaran variabel tersebut sangat miring ke kanan.

{{DESCRIPTIVE}}

### 2.3. Geometri batas dan representasi koordinat titik kecamatan

Poligon batas kecamatan diambil dari arsip Badan Informasi Geospasial (BIG) KSP Satu Peta, layer Peta Wilayah Administrasi Kecamatan (576 fitur Jawa Tengah, disaring menjadi 127 pasangan unik kabupaten/kota dan kecamatan Solo Raya). Seluruh 127 kecamatan cocok dengan kode wilayah resmi Kemendagri. Dua perbedaan penulisan ejaan dipetakan secara eksplisit melalui `data/padanan_nama.csv`: `Kebakkramat` (BIG/BPS) dengan `Kebakramat` (CSV), serta `Sidoharjo` (BIG/BPS) dengan `Sidoarjo` (tercetak `Sidoarjo` pada halaman A-2 PDF lampiran).

Dalam GWR berbasis titik, setiap unit areal kecamatan seluas rata-rata 47,54 km² harus diwakili oleh sepasang koordinat untuk menghitung matriks jarak kernel. Representasi acuan proyek menggunakan `ST_PointOnSurface(ST_Union(geom))` setelah memproyeksikan poligon WGS84 ke bidang metrik UTM Zona 49S (`EPSG:32749`), kemudian mengembalikan titik ke WGS84 (`EPSG:4326`) untuk perhitungan jarak lingkaran besar Haversine (radius bumi 6.371,0088 km). Berbeda dari pusat massa geometris biasa (*centroid*) yang dapat jatuh di luar poligon cekung atau terpisah waduk, `ST_PointOnSurface` menjamin titik berada di dalam poligon kecamatan masing-masing dan dibentuk murni dari geometri tanpa membaca target harga.

{{COORDINATE_AUDIT}}

Penyederhanaan satu kecamatan menjadi satu titik mengabaikan variasi intra-kecamatan (*Modifiable Areal Unit Problem* / MAUP) dan belum tentu berimpit dengan pusat permukiman atau koridor niaga. Untuk menguji seberapa peka hasil GWR terhadap penyederhanaan ini, Bagian 6.8 menguji empat alternatif titik representatif secara langsung. Selain itu, meskipun seluruh 127 kecamatan telah berdiri sebelum tahun 2020 (termasuk pemekaran Boyolali tahun 2018–2019), metadata fitur arsip BIG bertanggal `20230928` (edisi layanan 2022) sehingga kesamaan garis batas mikro dengan kondisi tepat tahun 2020 tetap dicatat sebagai asumsi proksi.

{{MAP_FIGURE}}

## 3. Metode Penelitian

### 3.1. Pemisahan protokol konfirmatori, eksplorasi, dan pencegahan kebocoran data

Banyak studi pemodelan spasial menjadi bias ketika peneliti menguji puluhan kombinasi fitur dan transformasi pada lipatan uji yang sama lalu melaporkan spesifikasi dengan galat terendah seolah-olah hasil konfirmatori. Untuk mencegah hal tersebut, seluruh rangkaian eksperimen dalam penelitian ini dibagi ke dalam empat tingkat inferensi yang terpisah tegas.

{{EXPERIMENT_HIERARCHY}}

Evaluasi utama menggunakan skema tujuh lipatan luar *leave-one-kabupaten/kota-out* (LOKO) mengikuti prinsip validasi berkelompok untuk data berstruktur spasial (Roberts dkk., 2017). Pada setiap lipatan luar, satu kabupaten/kota ditahan sepenuhnya sebagai data uji dan enam kabupaten/kota lainnya menjadi data latih, sehingga terkumpul tepat 127 prediksi uji *out-of-fold* per model. Di dalam setiap bagian latih luar, penyetelan parameter dilakukan melalui enam lipatan validasi dalam antarkabupaten/kota (lima wilayah *fit*, satu wilayah validasi). Parameter dipilih berdasarkan MAE gabungan seluruh observasi validasi dalam; jika terjadi nilai seri, kandidat pertama pada urutan grid dipilih secara deterministik.

Pencegahan kebocoran data diterapkan ketat: rata-rata dan simpangan baku standardisasi prediktor dihitung ulang hanya pada bagian *fit* di setiap lipatan dalam dan pada enam wilayah latih di setiap lipatan luar. Target wilayah uji tidak pernah diakses saat penyaringan fitur, standardisasi, pemilihan parameter, maupun perhitungan koreksi retransformasi. Koordinat lokasi uji hanya dipakai untuk menghitung jarak geografis ke titik-titik latih sebagaimana lazimnya prediksi spasial pada lokasi tujuan yang diketahui. Matriks perbandingan ruang penyetelan dan perlakuan setiap model dirangkum pada tabel berikut.

{{MODEL_PROTOCOL_MATRIX}}

### 3.2. Regresi linear dan Decision Tree

Pada eksperimen konfirmatori utama, regresi linear mengestimasi satu intersep dan dua koefisien global dengan kuadrat terkecil biasa tanpa pemotongan nilai negatif pasca-estimasi, sehingga perilaku ekstrapolasi linear terlihat apa adanya. Pada benchmark protokol setara di Bagian 6.8, model global diperluas menjadi regresi Ridge dengan kandidat penalti L2 yang disetel setara dengan GWR tanpa mempenalti intersep. Decision Tree menggunakan algoritma CART (`min_samples_leaf=3`, `random_state=124`, Pedregosa dkk., 2011) dengan kandidat kedalaman maksimum 2, 4, dan 6. Karena prediksi setiap daun merupakan rata-rata harga data latih di daun tersebut, pohon keputusan secara alami selalu menghasilkan prediksi positif.

### 3.3. K-Nearest Neighbors

KNN mengukur jarak Euclidean di dalam ruang prediktor yang telah distandardisasi pada data latih, bukan jarak geografis di permukaan bumi. Kandidat jumlah tetangga pada eksperimen utama adalah `k ∈ {3, 7, 15}` dengan bobot kebalikan jarak (`weights='distance'`). Karena prediksi dibentuk sebagai rata-rata tertimbang konveks dari harga kecamatan latih terdekat di ruang atribut, prediksi KNN terjamin positif tetapi tidak mampu melakukan ekstrapolasi melampaui rentang harga maksimum yang pernah muncul di data latih.

> ŷ(x) = Σᵢ∈Nₖ₍ₓ₎ wᵢyᵢ / Σᵢ∈Nₖ₍ₓ₎ wᵢ

### 3.4. Geographically Weighted Regression

Model spasial yang dievaluasi adalah **GWR klasik** (*Locally Weighted Least Squares*, Brunsdon dkk., 1996). Pada eksperimen utama Bagian 4, digunakan kernel **Fixed Gaussian** dengan kandidat *bandwidth* jarak tetap `h ∈ {5, 10, 20, 40}` km yang berlaku seragam bagi intersep dan prediktor terstandardisasi. Untuk setiap kecamatan uji `s`, koefisien lokal diestimasi hanya dari himpunan kecamatan latih `T` dengan bobot eksponensial jarak Haversine `dᵢ(s)`.

> ŷ(s) = β̂₀(s) + β̂₁(s)x₁(s) + β̂₂(s)x₂(s)

> β̂(s) = arg minᵦ Σᵢ∈T wᵢ(s)[yᵢ − b₀ − b₁xᵢ₁ − b₂xᵢ₂]²

> wᵢ(s) = exp[−dᵢ(s)² / (2h²)]

Pada protokol konfirmatori awal, sistem lokal diselesaikan tanpa penalti Ridge; setiap kehilangan *rank* matriks desain berbobot pada validasi dalam langsung menggugurkan kandidat *bandwidth* dan dicatat di berkas audit. Pada diagnostik sensitivitas Bagian 6.7–6.8, GWR diperluas mencakup kernel *Adaptive Gaussian* dan *Adaptive Bisquare* (berdasarkan jarak ke tetangga latih ke-`k`) serta penalti Ridge lokal pada koefisien lereng tanpa mempenalti intersep untuk mengendalikan kolinearitas lokal (Wheeler, 2007).

### 3.5. Metrik evaluasi, ketidakpastian bootstrap blok, AoA, dan autokorelasi residual

Kinerja diukur dari 127 prediksi *out-of-fold* menggunakan MAE, RMSE, dan koefisien determinasi gabungan R² dalam satuan Rp/m². Mengingat adanya pergeseran domain perkotaan ekstrem di Kota Surakarta, hasil utama dilaporkan secara berdampingan untuk **seluruh 127 kecamatan** dan **enam kabupaten non-Surakarta (122 kecamatan)**, sementara kelima kecamatan Surakarta juga dianalisis terpisah sebagai uji tekan perkotaan (*urban stress test*).

> MAE = (1/n) Σᵢ |yᵢ − ŷᵢ|

> RMSE = √[(1/n) Σᵢ (yᵢ − ŷᵢ)²]

> R² = 1 − Σᵢ (yᵢ − ŷᵢ)² / Σᵢ (yᵢ − ȳ)²

Untuk mengukur ketidakpastian statistik tanpa melanggar ketergantungan spasial maupun kesamaan model di dalam lipatan uji yang sama, dihitung **interval kepercayaan 95% berbasis bootstrap blok kabupaten/kota** (*cluster block bootstrap*, `B = 10.000` replikasi berseed tetap `124`). Setiap replikasi menarik tujuh blok kabupaten/kota dengan pengembalian (atau enam blok untuk metrik 122 kecamatan), lalu menghitung distribusi empiris MAE, RMSE, dan selisih berpasangan `ΔMAE` terhadap model acuan.

Dua diagnostik spasial tambahan diterapkan secara baku pada hasil utama. Pertama, **Area of Applicability (AoA)** dan *Dissimilarity Index* (`DI`) dihitung murni *out-of-fold* mengikuti Meyer dan Pebesma (2021): jarak Euclidean terdekat tiap kecamatan uji ke data latih terstandardisasi dinormalisasi oleh rata-rata jarak berpasangan data latih, lalu dibandingkan terhadap ambang pencilan `Q₃ + 1,5 × IQR` yang diperoleh dari validasi silang internal data latih. Kedua, struktur spasial residual `eᵢ = yᵢ − ŷᵢ` diuji menggunakan **Global Moran's I** (uji permutasi dua sisi `9.999` pengacakan) dan **Local Indicators of Spatial Association (LISA / Local Moran's I)** (Anselin, 1995; `999` permutasi bersyarat) di atas matriks kontiguitas *Queen* terstandardisasi baris dari poligon penuh BIG.

## 4. Hasil Eksperimen Konfirmatori Utama (Protokol Terkunci Dua Prediktor)

### 4.1. Kinerja gabungan, pemisahan Kota Surakarta, dan ketidakpastian blok

Tabel berikut menyajikan hasil konfirmatori utama keempat model pada protokol terkunci dua prediktor, lengkap dengan interval kepercayaan bootstrap blok 95% serta perbandingan langsung antara evaluasi penuh 127 kecamatan dan evaluasi enam kabupaten non-Surakarta (122 kecamatan).

{{METRICS}}

Tiga temuan pokok muncul dari tabel utama. Pertama, pada gabungan 127 kecamatan, KNN memberikan MAE titik terendah (Rp732.073/m²) dan regresi linear memberikan RMSE terendah (Rp1.355.435/m²; R² 0,557). Namun, selisih berpasangan KNN terhadap regresi linear hanya −Rp6.947/m² dengan interval kepercayaan bootstrap blok 95% yang sangat lebar melintasi nol (−Rp112.571 hingga +Rp175.407/m²), sehingga keunggulan tipis KNN atas regresi linear tidak bermakna secara statistik. Kedua, GWR Gaussian mencatat MAE Rp802.227/m²; selisih +Rp63.207/m² di atas regresi linear memiliki interval kepercayaan bootstrap blok 95% yang seluruhnya positif (+Rp16.219 hingga +Rp163.778/m²). Artinya, pada dua prediktor dasar, pembobotan geografis secara konsisten menghasilkan galat absolut sedikit lebih besar daripada regresi global. Ketiga, ketika lima kecamatan Kota Surakarta dipisahkan (kolom 122 kecamatan), rentang ketidakpastian menyempit tajam dan memperjelas peringkat di wilayah kabupaten: KNN mencapai MAE Rp525.199/m², regresi linear mencapai RMSE terendah Rp875.922/m² (R² 0,602), sedangkan GWR tetap tertinggal +Rp32.120/m² dari regresi linear (95% CI blok: +Rp8.491 hingga +Rp51.807/m²).

### 4.2. Variasi kinerja per kabupaten/kota dan analisis Area of Applicability

Rincian MAE dan RMSE setiap kabupaten/kota memperlihatkan ketimpangan skala galat antara enam kabupaten dan Kota Surakarta.

{{REGIONAL_MAE}}

{{REGIONAL_RMSE}}

Pada tingkat wilayah individual, GWR menghasilkan MAE lebih rendah daripada regresi linear hanya di Karanganyar dan Sukoharjo, serta mengungguli KNN di Karanganyar dan Surakarta. Keunggulan lokal di sebagian wilayah pinggiran Surakarta tersebut tidak cukup menutup kenaikan galat di lima wilayah lainnya.

{{SURAKARTA_DISCUSSION}}

Untuk menguji secara objektif apakah kegagalan di Kota Surakarta disebabkan oleh ketiadaan padanan ruang fitur pada data latih, tabel berikut merangkum hasil pengujian *Area of Applicability* (AoA) lintas ruang prediktor.

{{AOA_TABLE}}

Hasil AoA mengonfirmasi mekanisme *domain shift* tersebut tanpa memakai informasi harga uji. Pada ruang dua prediktor utama, 19 dari 127 kecamatan (15,0%) berada di luar AoA pelatihan, termasuk 4 dari 5 kecamatan Kota Surakarta, dengan median *Dissimilarity Index* Surakarta hampir 37 kali lipat median kabupaten lainnya (0,41 dibanding 0,01). Di luar AoA, MAE GWR melonjak lebih dari tiga kali lipat dari Rp591.448/m² menjadi Rp2.000.340/m² (dan KNN melonjak dari Rp485.239/m² menjadi Rp2.135.131/m²). Ketika ruang fitur diperluas mencakup proporsi terbangun pada Bagian 6 (empat fitur VIF maupun tujuh fitur), kelima kecamatan Kota Surakarta (5/5) seluruhnya jatuh jauh di luar ambang AoA data latih.

### 4.3. Parameter terpilih dan audit prediksi negatif

Parameter yang dipilih validasi internal pada tiap lipatan luar tercantum pada tabel berikut.

{{PARAMETERS}}

Enam lipatan kabupaten memilih batas atas *bandwidth* kandidat GWR (40 km), sedangkan lipatan Kota Surakarta memilih *bandwidth* sempit (10 km) untuk menangkap gradien harga kecamatan penyangga terdekat seperti Kartasura, Colomadu, Grogol, dan Baki. Tidak terjadi kegagalan matriks singular pada eksperimen utama, tetapi ketiadaan kendala nonnegatif pada model berbasis regresi linear memunculkan prediksi harga negatif di kecamatan pedesaan berpenduduk kecil dan tanpa fasilitas regional.

{{NEGATIVE_TABLE}}

Sebanyak 17 kecamatan (13,4%) pada regresi linear dan 15 kecamatan (11,8%) pada GWR memperoleh prediksi negatif, dengan nilai paling ekstrem mencapai −Rp450.353/m² (Linear) dan −Rp469.120/m² (GWR) di Kecamatan Paranggupito, Kabupaten Wonogiri. Kecamatan terdampak terkonsentrasi di Wonogiri dan Boyolali dengan rata-rata harga aktual sekitar Rp120–129 ribu/m². Prediksi negatif tidak layak secara domain ekonomi dan menandai salah spesifikasi bentuk fungsional ekor bawah; nilai asli tetap dipertahankan pada tabel konfirmatori Bagian 4 agar tolok ukur baseline transparan, sedangkan model berkendala nonnegatif dievaluasi secara sistematis pada Bagian 6.8.

{{SCATTER_FIGURE}}

### 4.4. Diagnostik autokorelasi spasial residual (Moran's I dan LISA)

Agar evaluasi tidak berhenti pada besaran agregat MAE dan RMSE, residual *out-of-fold* keempat model diperiksa terhadap matriks kontiguitas *Queen* 127 poligon kecamatan. Tabel berikut merangkum nilai Global Moran's I beserta jumlah klaster lokal signifikan (LISA, `p < 0,05`) baik untuk eksperimen konfirmatori dua fitur maupun pembanding empat fitur non-kolinear dari Bagian 6.7.

{{MORAN_TABLE}}

Variabel target harga aktual memiliki autokorelasi spasial positif yang sangat kuat (Moran's I = 0,592; `z = 11,28`; `p = 0,0001`) dengan 14 kecamatan klaster *High-High* di koridor inti Surakarta dan kecamatan penyangga Sukoharjo–Karanganyar. Pada eksperimen dua prediktor, seluruh model masih menyisakan autokorelasi residual yang signifikan (`p ≤ 0,0006`) karena dua variabel demografi-fasilitas belum mampu menjelaskan struktur aglomerasi ruang. Meskipun demikian, terlihat perbedaan perilaku spasial yang jelas: KNN menyisakan pengelompokan galat tertinggi (Moran's I = 0,545; 10 klaster *High-High*), diikuti regresi linear (I = 0,364; 8 *High-High*), sedangkan GWR meredam autokorelasi residual paling kuat di antara model baseline (I = 0,240; 6 *High-High*). Ketika fitur tutupan terbangun non-kolinear disertakan pada model empat fitur VIF linear, GWR Fixed + Ridge (I = 0,073; `p = 0,1195`) dan GWR Adaptive + Ridge (I = 0,075; `p = 0,1127`) berhasil menekan autokorelasi residual hingga tidak lagi berbeda signifikan dari sebaran acak, sedangkan residual KNN masih mengelompok kuat (I = 0,418; `p = 0,0001`).

{{RESIDUAL_MAP_FIGURE}}

## 5. Pembahasan Hasil Utama

Hasil konfirmatori pada Bagian 4 menjawab pertanyaan penelitian utama secara lugas: ketika satu kabupaten/kota dikeluarkan penuh dari pelatihan dan model hanya dibekali jumlah penduduk serta fasilitas umum regional, pembobotan geografis GWR belum meningkatkan akurasi prediksi dibandingkan regresi linear maupun KNN. Sebaliknya, GWR justru menunjukkan fungsi diagnostik yang berguna karena kemampuannya menyerap sebagian dependensi spasial residual di perbatasan antarkabupaten, sebagaimana tercermin dari penurunan Global Moran's I dan penyusutan kantong *underprediction* LISA.

Terdapat tiga penjelasan struktural atas hasil tersebut. Pertama, validasi lintas kabupaten/kota memutus informasi harga lokal tepat di sekitar pusat wilayah uji. Untuk kecamatan di bagian tengah kabupaten uji yang berjarak puluhan kilometer dari kabupaten tetangga, tetangga latih terdekat berada di wilayah administratif lain sehingga regresi lokal dengan *bandwidth* sempit kekurangan sampel efektif, sedangkan *bandwidth* lebar menyusutkan GWR mendekati OLS global. Kedua, ketimpangan struktur ruang antara Kota Surakarta dan enam kabupaten penyangganya menciptakan *domain shift* yang tajam. Baik model lokal maupun global tidak memiliki titik rujukan di data latih dengan kepadatan dan aglomerasi komersial setara Surakarta, sehingga galat pada lima kecamatan kota mendominasi lebih dari separuh jumlah kuadrat galat gabungan. Ketiga, dengan hanya tujuh klaster kabupaten/kota, variabilitas antarklaster cukup besar sehingga selisih kecil MAE antarmode nonspasial (seperti Rp6.947/m² antara KNN dan regresi linear) berada sepenuhnya di dalam rentang derau pengambilan sampel blok.

Temuan ini membawa implikasi praktis yang tegas. Model tingkat kecamatan yang dilatih dari dua variabel agregat sekunder tidak memadai untuk penaksiran nilai bidang tanah, penyusunan NJOP/ZNT operasional, ataupun pengambilan keputusan fiskal daerah. Selain galat absolut rata-rata masih berkisar Rp525–623 ribu/m² di luar Surakarta dan melampaui Rp4 juta/m² di Surakarta, regresi tanpa kendala nonnegatif juga menghasilkan taksiran negatif di wilayah pedesaan berharga rendah. Oleh sebab itu, seluruh eksperimen pengembangan pada Bagian 6 diposisikan untuk menguji apakah perbaikan fitur tutupan lahan, pengendalian kolinearitas, dan kendala nonnegatif dapat mengatasi kelemahan spesifikasi tersebut tanpa diklaim mengesampingkan keterbatasan data target.

## 6. Keterbatasan, Audit Sumber, dan Analisis Sensitivitas Eksploratif

Ringkasan status verifikasi komponen data, geometri, dan komputasi penelitian disajikan pada tabel berikut sebagai pijakan kehati-hatian sebelum membaca rangkaian eksperimen eksploratif.

{{AUDIT_STATUS}}

Rencana pengembangan prediktor beserta kandidat sumber resmi dan syarat verifikasinya dirangkum pada tabel di bawah ini.

{{CANDIDATE_SOURCES}}

### 6.1. Kerangka kandidat variabel berbasis literatur

Sebanyak 25 kandidat variabel diinventarisasi dari delapan rujukan empiris untuk memetakan dimensi demografi, fasilitas, aksesibilitas transportasi, tutupan lahan, dan fisik medan (Berawi dkk., 2018; Huang & Hewings, 2021; Zhang dkk., 2021; Arafah dkk., 2026). Daftar ini berfungsi sebagai kerangka konseptual terstruktur, bukan kumpulan fitur yang dimasukkan serentak ke dalam regresi lokal berobservasi 127 kecamatan.

{{CANDIDATE_REGISTRY}}

Kode rujukan pada tabel mengacu pada: R1 Aziz dkk. (2023); R2 Saefuddin dkk. (2012); R3 Syahar dkk. (2020); R4 Arumingtyas dkk. (2019); R5 Berawi dkk. (2018); R6 Huang dan Hewings (2021); R7 Zhang dkk. (2021); serta R8 Arafah dkk. (2026). Rincian satuan dan status ketersediaan dicatat pada `data/kandidat_variabel.csv` dan `docs/PENGEMBANGAN_VARIABEL.md`.

### 6.2. Aturan penyaringan eksploratif dan tahapan uji

Korelasi peringkat Spearman digunakan sebagai ukuran asosiasi eksploratif utama karena sebaran harga dan fasilitas sangat miring, didampingi korelasi linear Pearson sebagai pembanding sensitivitas terhadap nilai ekstrem. Nilai `p` korelasi maupun koreksi pengujian berganda Benjamini dan Hochberg (1995) diperlakukan semata-mata sebagai indikator deskriptif karena ketergantungan spasial antar-kecamatan melanggar asumsi pengamatan bebas. Dalam pemodelan prediktif, pemilihan fitur dan parameter wajib diisolasi di dalam bagian latih setiap lipatan agar tidak mencemari evaluasi uji luar.

{{FUTURE_EXPERIMENTS}}

### 6.3. Eksplorasi lima variabel tambahan tutupan lahan dan kepadatan (Eksploratif)

Tahap pengolahan geospasial mengekstrak tiga proporsi tutupan lahan tahun 2020 dari raster ESA WorldCover 10 m v100 (Zanaga dkk., 2021; tile `S09E108` dan `S09E111` dengan pembobotan luas piksel elipsoid di dalam poligon) serta dua ukuran kepadatan proksi dari pembagian jumlah penduduk dan fasilitas terhadap luas poligon BIG dalam proyeksi UTM 49S. Kelas `cropland` mencakup lahan tanaman semusim secara umum (bukan khusus sawah irigasi), `tree cover` mencakup tajuk pepohonan secara umum, dan `built-up` mewakili permukaan terbangun pada resolusi 10 meter.

| Sumber data | Kolom yang digunakan | Cara memperoleh nilai kecamatan |
| --- | --- | --- |
| Lampiran A Salim Aziz | Penduduk, jumlah fasilitas umum regional, harga rata-rata (Rp/m²) | Angka per kecamatan ditranskripsi dan dicocokkan dengan lampiran PDF. Harga menjadi variabel target. |
| Poligon BIG dan jumlah dari Lampiran A | Kepadatan penduduk proksi (jiwa/km²), kepadatan fasilitas proksi (unit/km²) | Masing-masing jumlah dibagi luas poligon kecamatan dalam proyeksi UTM 49S. |
| ESA WorldCover 2020 v100 dan poligon BIG | Persentase terbangun, tanaman budidaya (*cropland*), tutupan pohon | Luas piksel valid kelas terkait dibagi total luas piksel valid kecamatan lalu dikalikan 100. |

Sebagai ilustrasi perhitungan pada satu baris, Kecamatan Banjarsari di Kota Surakarta memiliki luas poligon arsip 15,4864 km², penduduk 168.770 jiwa, dan 9 fasilitas regional sehingga diperoleh kepadatan proksi 10.897,95 jiwa/km² serta 0,581 unit/km², dengan tutupan WorldCover 80,79% terbangun, 1,67% tanaman budidaya, 14,33% tutupan pohon, dan harga rata-rata Rp7.678.425/m². Ringkasan kuartil seluruh variabel disajikan pada tabel berikut.

{{STATISTIK_VARIABEL}}

![Median lima variabel tambahan menurut kabupaten/kota. Angka dalam kurung menunjukkan jumlah kecamatan. Intensitas biru dibandingkan di dalam masing-masing kolom.](../artifacts/analisis_variabel/profil_wilayah.png)

Perbedaan profil fisik antara Kota Surakarta dan kabupaten sekitarnya sangat mencolok: median proporsi terbangun Surakarta mencapai 84,95% dengan kepadatan 10.898 jiwa/km², berbanding 2,99% dan 543 jiwa/km² pada 25 kecamatan di Kabupaten Wonogiri.

![Harga teramati terhadap setiap variabel tambahan pada 127 kecamatan tahun 2020. Titik jingga menandai lima kecamatan Kota Surakarta.](../artifacts/analisis_variabel/sebaran_harga.png)

Korelasi bivariat ketujuh prediktor terhadap harga pada 127 kecamatan dirangkum di bawah ini.

{{KORELASI_HARGA}}

![Matriks korelasi tujuh prediktor dan harga untuk 127 kecamatan: segitiga atas menampilkan Pearson r dan segitiga bawah menampilkan Spearman ρ.](../artifacts/analisis_variabel/matriks_korelasi.png)

Proporsi lahan terbangun menunjukkan asosiasi terkuat terhadap harga (`r = 0,893`; `ρ = 0,676`), tetapi sekaligus berkorelasi sangat tinggi dengan kepadatan penduduk proksi (`r = 0,952`; `ρ = 0,950`) serta membentuk konstrain komposisional dengan tutupan pohon dan tanaman budidaya. Tumpang tindih linear inilah yang memicu pembengkakan varians apabila ketujuh variabel dimasukkan serentak ke model regresi tanpa penyaringan.

### 6.4. Replikasi tujuh prediktor skala logaritmik dan sensitivitas titik notebook (Eksploratif)

Subbagian ini mendokumentasikan replikasi eksak protokol notebook pendamping (`tanah/colab.py`) yang menggabungkan ketujuh prediktor di atas dan melatih empat model *from scratch* pada skala target `ln(harga)`, kemudian mengembalikan prediksi ke skala Rp/m² melalui transformasi balik naif `exp(ẑ)` tanpa koreksi *smearing*. Pada protokol notebook tersebut, KNN memakai `k = 5` tetap, pohon keputusan memakai kedalaman `4` tetap, OLS memakai penalti numerik `10⁻⁸`, dan GWR Fixed Gaussian menyetel *bandwidth* dari `{5, 10, 15, 25, 40, 60, 80}` km melalui RMSE internal dengan penalti `10⁻³` yang ikut dikenakan pada intersep. Tabel berikut menyajikan metrik gabungan pada skala keputusan Rp/m² menggunakan 127 titik interior BIG.

{{COLAB_METRICS}}

![Evaluasi tujuh prediktor skala log dengan titik BIG: diagram sebar KNN per kecamatan dan peta panas MAE per wilayah dalam skala warna logaritmik.]({{FIGUR_TUJUH_PREDIKTOR}})

Pada KNN berbobot, penambahan lima fitur WorldCover/BIG menurunkan MAE dari Rp733.681/m² (ablasi dua fitur bertarget log) menjadi Rp619.531/m² dan RMSE menjadi Rp1.309.859/m², kendati MAE di Kota Surakarta masih tinggi (Rp3.958.006/m² karena prediksi dibatasi rata-rata tetangga latih non-Surakarta). Sebaliknya, OLS dan GWR mengalami ledakan galat ekstrem (MAE Rp25,74 juta/m² dan Rp5,38 juta/m²; lima kecamatan Surakarta menyumbang 99,66% SSE GWR). Audit menunjukkan dua akar masalah pada protokol notebook ini: (1) multikolinearitas berat antarprediktor (VIF `built_pct` mencapai 36,65 dan `tree_pct` 24,27) dan (2) pemetaan eksponensial `exp(ẑ)` yang menggandakan kelebihan taksiran linear di wilayah berkepadatan tinggi menjadi ratusan juta rupiah per meter persegi. Sebagai catatan audit geometri, penggunaan berkas koordinat kiriman awal notebook menghasilkan MAE GWR Rp4.633.597/m², tetapi dua titik di Kabupaten Boyolali (`Ampel` dan `Wonosegoro`) terbukti jatuh di luar poligon BIG pasca-pemekaran karena masih memakai centroid GADM v4.1 pra-pemekaran.

### 6.5. Eksplorasi pasca-galat: proksi akses wisata, kampus, dan topografi (Eksploratif)

Setelah meninjau galat lokal di kawasan lereng wisata Tawangmangu, dilakukan uji eksploratif dengan menambahkan empat fitur fisik-aksesibilitas: jarak Haversine terdekat dari titik interior kecamatan ke objek wisata (`attraction`, `museum`, `theme_park`) dan perguruan tinggi (`university`, `college`) pada ekstrak OpenStreetMap 1 Januari 2021, serta median elevasi dan kemiringan lereng dari raster SRTM v4.1 CIAT (Jarvis dkk., 2008). Pemilihan fitur ini merujuk pada kajian wisata Tawangmangu (Riswandha & Wahyono, 2017), kedekatan kampus (Wang, 2023), dan kemiringan lahan (Huang & Hewings, 2021), namun harus diperlakukan dengan sangat hati-hati karena dua keterbatasan: (a) jarak garis lurus dari ekstrak OSM awal 2021 merupakan proksi kasar yang tidak mengukur waktu tempuh jaringan jalan raya, kapasitas pengunjung, maupun ketimpangan kelengkapan pemetaan sukarela, dan (b) spesifikasi diuji ulang pada tujuh blok LOKO yang sama setelah peneliti melihat pola galat sebelumnya (*post-error specification search*).

![Hubungan empat variabel aksesibilitas dan medan terhadap harga rata-rata kecamatan dalam sumbu vertikal logaritmik; titik jingga menandai Kecamatan Tawangmangu.](../artifacts/akses_medan/akses_medan.png)

Delapan kombinasi prediktor diuji pada target `ln(harga)` dengan penyetelan parameter internal berbasis MAE gabungan (`KNN k ∈ {3, 5, 7, 15}`; `Pohon d ∈ {2, 4, 6}`; `Ridge global` dan `GWR ridge` dengan intersep bebas penalti serta kandidat *bandwidth* tetap maupun adaptif).

{{HASIL_AKSES}}

Penambahan jarak kampus menurunkan MAE KNN dari Rp633.139/m² (spesifikasi dasar pada grid penyetelan yang sama) menjadi Rp610.868/m² (RMSE Rp1.263.634/m²), terutama berkat perbaikan prediksi di kecamatan penyangga kampus seperti Kartasura dan Grogol, sedangkan galat di Tawangmangu sendiri tidak membaik (Rp1.666.854/m²). Pada sebelas prediktor skala asli dengan target log, GWR ridge tetap mengalami ledakan ekstrapolasi di Surakarta (RMSE Rp58,96 juta/m²), dan transformasi prediktor `ln(1+x)` masih menempatkan GWR di belakang Ridge global. Karena fitur-fitur ini lahir dari inspeksi galat pada sampel yang sama, penurunan MAE KNN sebesar ~3,5% tersebut tidak boleh diklaim sebagai bukti generalisasi konfirmatori sebelum diuji pada periode atau wilayah baru dengan matriks jarak jaringan jalan yang terverifikasi.

### 6.6. Eksplorasi konsentrasi wisata dalam blok dan seleksi spesifikasi internal (Eksploratif)

Sebagai pemeriksaan lanjutan atas hubungan peringkat di dalam kabupaten yang sama, dihitung korelasi peringkat terpusat blok beserta uji acak 9.999 permutasi dalam-kabupaten terkoreksi Bonferroni, lalu diuji model skala asli Rp/m² dengan pemotongan batas bawah nol (`max(0, ŷ)`) dan seleksi gabungan spesifikasi-model-parameter berdasarkan RMSE validasi dalam.

{{UJI_KORELASI}}

{{UJI_SELEKSI}}

{{ZERO_CLIP_SUMMARY}}

Di dalam kabupaten yang sama, kepadatan penduduk dan persentase lahan terbangun tetap berkorelasi positif kuat terhadap peringkat harga (`p = 0,0007`), sedangkan jarak wisata garis lurus dan hitungan objek wisata radius 5 km tidak menunjukkan hubungan monotonik umum setelah dikendalikan menurut kabupaten. Prosedur seleksi internal berbasis RMSE menghasilkan MAE gabungan Rp820.533/m², lebih buruk daripada spesifikasi tetap Ridge lima variabel (MAE Rp660.964/m²), karena pemilihan model antar-enam kabupaten pedesaan gagal mengantisipasi lonjakan skala perkotaan saat lipatan Surakarta diuji.

### 6.7. Diagnostik terkendali GWR: multikolinearitas, skala target, bandwidth adaptif, dan domain shift

Untuk mengisolasi penyebab kegagalan GWR pada Bagian 6.4 secara sistematis, dijalankan eksperimen faktorial terkendali (`tanah/sensitivity.py`) yang memisahkan efek tiga faktor: (1) reduksi multikolinearitas dari tujuh fitur (VIF maksimum 36,65) menjadi empat fitur non-redundan (`built_pct`, `cropland_pct`, `jumlah_penduduk`, `jumlah_fasum_regional`; VIF masing-masing 1,96; 1,06; 2,05; dan 1,88); (2) skala target `ln(harga)` lawan skala linear `Rp/m²`; serta (3) pilihan kernel *Fixed Gaussian*, *Adaptive Gaussian*, dan *Adaptive Bisquare* dengan penalti Ridge lokal `λ ∈ {0; 0,01; 0,1; 1; 10}` tanpa mempenalti intersep.

{{GWR_SENSITIVITY_TABLE}}

Tabel di atas membongkar tiga mekanisme penting. Pertama, mengganti *bandwidth* tetap menjadi adaptif saja pada tujuh fitur bertarget log sama sekali tidak mengatasi ledakan galat (MAE GWR Adaptive Gaussian + Ridge mencapai Rp25,90 juta/m²). Kedua, berpindah ke skala target linear `Rp/m²` langsung menghentikan amplifikasi eksponensial di Surakarta sehingga MAE GWR turun ke Rp565.799/m² bahkan sebelum penyaringan fitur. Ketiga, ketika redundansi kolinear disaring menjadi empat fitur ber-VIF rendah pada skala linear, galat turun tajam di seluruh model regresi: OLS mencapai MAE Rp512.702/m² (R² 0,813), GWR Fixed Gaussian + Ridge Rp519.091/m² (R² 0,788), dan GWR Adaptive Gaussian + Ridge Rp520.261/m² (R² 0,794), melampaui KNN (`k = 5`, MAE Rp539.872/m²) serta Decision Tree (`d = 4`, MAE Rp669.970/m²). Pada bootstrap blok kabupaten/kota (`artifacts/diagnostik_lanjut/block_bootstrap.csv`), selisih MAE antara GWR Fixed/Adaptive + Ridge dan OLS hanya berkisar +Rp6.389 hingga +Rp7.559/m² dengan interval kepercayaan 95% blok yang melintasi nol (−Rp2.989 hingga +Rp35.225/m²), sehingga ketiganya setara secara statistik.

{{GWR_REGIONAL_4FITUR}}

Rincian parameter per wilayah pada tabel di atas menunjukkan mengapa GWR dan OLS berkinerja sangat mirip: pada enam dari tujuh lipatan kabupaten, validasi internal memilih batas atas *bandwidth* (`80 km` atau `80 tetangga`) beserta `λ = 10` sehingga GWR menyusut mendekati regresi global. Hanya saat memprediksi Kota Surakarta validasi internal memilih lingkungan lokal (`15 km` atau `25 tetangga`, `λ = 1`), di mana GWR Adaptive + Ridge mencatat MAE Surakarta sedikit lebih rendah (Rp2.847.320/m²) daripada GWR Fixed + Ridge (Rp2.908.146/m²) maupun KNN (Rp3.247.967/m²), meskipun masih sedikit di atas OLS (Rp2.646.569/m²). Perbandingan lintas skema pembagian data (LORO 127 kecamatan, LORO 122 kecamatan tanpa Surakarta, dan *Stratified 5-Fold CV* yang mencampur kecamatan urban-rural di data latih) semakin mempertegas peran *domain shift*.

{{GWR_DOMAIN_SHIFT_TABLE}}

Catatan: tanda `*` menunjukkan baris tujuh fitur log LORO 127 memakai `λ = 10⁻³` sesuai protokol notebook, sedangkan kolom LORO 122 dan Stratified memakai penyetelan Ridge. Ketika data latih diizinkan memuat sebagian kecamatan perkotaan melalui *Stratified 5-Fold CV*, MAE KNN membaik tajam ke Rp483.126/m² (R² 0,799), membuktikan bahwa hambatan utama prediksi lintas wilayah memang terletak pada ketiadaan representasi kota inti saat seluruh Kota Surakarta ditahan.

### 6.8. Pemeriksaan ketahanan metodologis: bilangan kondisi lokal, koreksi Duan, kendala nonnegatif, protokol setara, dan sensitivitas titik lokasi

Empat pemeriksaan tambahan dijalankan dalam modul `tanah/rigor.py` untuk menutup celah evaluasi yang belum terjawab pada subbagian sebelumnya.

**Pertama, gerbang pra-pemodelan multikolinearitas dan bilangan kondisi lokal (*local condition number*).** Mengikuti Wheeler (2007), matriks desain lokal berbobot GWR berisiko tidak stabil apabila bilangan kondisi `κ` melebihi ambang praktis 30 meskipun sistem tidak singular secara numerik. Tabel berikut merangkum VIF maksimum di dalam lipatan latih beserta sebaran `κ` lokal pada 127 titik uji.

{{COLLINEARITY_TABLE}}

Pada tujuh fitur tanpa regularisasi memadai (`bw = 15 km`, `λ = 0` maupun `λ = 0,001`), VIF maksimum di dalam lipatan latih menyentuh 49,79 dan **seluruh 127 lokasi uji (100%) melampaui ambang `κ > 30`** (median `κ` 733,4 hingga 852,1; maksimum 4.080,0). Sebaliknya, pada empat fitur hasil penyaringan kolinearitas (`VIF latih ≤ 2,64`) yang dipadukan dengan penalti Ridge, **0 dari 127 lokasi melebihi `κ = 30`** (median `κ` turun menjadi 3,88–4,51). Hal ini menunjukkan bahwa penyaringan VIF dan pemeriksaan `κ` lokal wajib dijadikan gerbang pra-pemodelan sebelum estimasi GWR.

**Kedua, evaluasi konsisten transformasi logaritmik (koreksi Duan smearing) dan model berkendala nonnegatif.** Pada Bagian 6.4, retransformasi `exp(ẑ)` dilakukan tanpa koreksi bias ekspektasi lognormal, sementara model skala linear pada Bagian 4 dan 6.7 menghasilkan prediksi negatif (17 pada OLS, 10 pada GWR Fixed + Ridge, dan 9 pada GWR Adaptive + Ridge di spesifikasi empat fitur VIF, terutama di Kabupaten Sragen dan Wonogiri dengan nilai terendah −Rp484.572/m²). Tabel berikut membandingkan secara konsisten lima perlakuan target pada empat dan tujuh fitur dengan seluruh parameter dan faktor *smearing* Duan (1983) dihitung murni di dalam data latih tiap lipatan, dilengkapi estimator *Quasi-Poisson QMLE* ber-*log-link* langsung pada skala asli `y > 0` (Silva & Tenreyro, 2006).

{{TARGET_TREATMENT_TABLE}}

Hasilnya memperjelas untung-rugi setiap pendekatan pada skala keputusan Rp/m². Pada enam kabupaten non-Surakarta (122 kecamatan) dengan empat fitur VIF, koreksi *smearing* Duan memang memperbaiki bias turun retransformasi naif pada regresi global (MAE turun dari Rp537.740/m² menjadi Rp481.843/m² pada kualitas suai skala log yang identik, `MAE_ln = 1,007`). Namun, pada gabungan 127 kecamatan, pengali *smearing* (`> 1`) justru memperparah ledakan ekstrapolasi eksponensial di Surakarta (MAE naik dari Rp37,38 juta menjadi Rp51,84 juta/m²). Estimator *Quasi-Poisson* dan *Spatially Weighted Poisson QMLE* berhasil menjamin seluruh prediksi positif murni (`0/127` negatif) tanpa bias transformasi balik, tetapi fungsi hubung eksponensialnya tetap menggandakan ekstrapolasi fitur perkotaan Surakarta (MAE gabungan Rp5,10–5,25 juta/m²). Sebaliknya, model linear dengan pemotongan domain nonnegatif transparan `max(0, ŷ)` menghilangkan seluruh prediksi negatif (`0/127`) sekaligus menurunkan MAE gabungan empat fitur VIF ke Rp496.075/m² (Regresi Global) dan Rp502.863/m² (GWR Fixed + Ridge).

**Ketiga, perbandingan model pada protokol penyetelan yang disetarakan.** Pada Bagian 6.4 dan 6.7, ruang penyetelan antarmode belum sepenuhnya simetris (misalnya `k = 5` dan `d = 4` dikunci pada KNN/Tree sementara GWR menyetel puluhan pasangan *bandwidth*-Ridge, dan OLS belum menyetel penalti Ridge). Tabel berikut menyetarakan kriteria validasi dalam (`MAE gabungan`), standardisasi dalam-lipatan, dan penyetelan hiperparameter bagi seluruh model, sekaligus membandingkan penyaringan otomatis buta `VIF ≤ 5` murni di dalam lipatan latih (yang memilih empat fitur yang sama di 7/7 lipatan tanpa pernah melihat data uji, tetapi menggugurkan `built_pct` lebih dulu karena konstrain komposisional tutupan lahan) dengan empat fitur non-kolinear terarah domain.

{{FAIR_BENCHMARK_TABLE}}

Ketika seluruh model disetel secara adil, kesimpulan metodologis menjadi sangat bersih: baik pada saringan otomatis `VIF ≤ 5` dalam-lipatan (MAE Ridge Global Rp598.204/m² vs GWR Fixed + Ridge Rp620.699/m²) maupun pada empat fitur non-kolinear berkendala nonnegatif (MAE Ridge Global Rp496.144/m², R² 0,822 vs GWR Fixed + Ridge Rp520.210/m² dan KNN Rp556.287/m²), regresi global terregularisasi tetap sedikit lebih akurat dan jauh lebih sederhana daripada GWR untuk generalisasi lintas kabupaten/kota.

**Keempat, uji sensitivitas titik representatif kecamatan.** Untuk memeriksa apakah peringkat GWR berubah apabila kecamatan tidak diwakili oleh `ST_PointOnSurface` poligon BIG, GWR dijalankan ulang menggunakan centroid geometris poligon BIG, titik pusat referensi BPS/HDX COD-AB, serta titik kiriman notebook (centroid GADM v4.1 dan tiga titik pusat kecamatan Boyolali).

{{POINT_SENSITIVITY_TABLE}}

Meskipun pergeseran koordinat antarsumber memiliki median 93,5 hingga 604,1 meter dan maksimum mencapai 7.910,8 meter pada kecamatan pemekaran, perubahan MAE GWR sangat kecil (kurang dari Rp700/m² pada dua fitur maupun empat fitur) dan **peringkat model di antara keempat metode tidak berubah sama sekali** (`4/4` pada dua fitur konfirmatori dan `2/4` di bawah regresi global pada empat fitur VIF). Dengan demikian, kesimpulan utama penelitian terbukti kokoh terhadap pilihan titik representatif tingkat kecamatan, meskipun variasi harga persil di dalam kecamatan tetap tidak teramati tanpa data tingkat bidang.

## 7. Kesimpulan

Evaluasi konfirmatori terkunci pada 127 kecamatan di tujuh kabupaten/kota Solo Raya tahun 2020 menunjukkan bahwa pembobotan kedekatan geografis melalui GWR Gaussian klasik belum memberikan keunggulan prediktif ketika seluruh kabupaten/kota tujuan ditahan dari pelatihan. Pada spesifikasi dua prediktor sumber (penduduk dan fasilitas umum regional), KNN memperoleh MAE gabungan terendah Rp732.073/m² dan regresi linear memperoleh RMSE terendah Rp1.355.435/m² (R² 0,557; selisih KNN terhadap regresi linear tidak signifikan menurut bootstrap blok kabupaten/kota), sedangkan GWR menghasilkan MAE lebih tinggi sebesar Rp802.227/m² (`ΔMAE` +Rp63.207/m²; 95% CI blok: +Rp16.219 hingga +Rp163.778/m²). Tanpa Kota Surakarta (122 kecamatan pada enam kabupaten), KNN menghasilkan MAE terendah Rp525.199/m² dan regresi linear menghasilkan RMSE terendah Rp875.922/m² (R² 0,602). Sebaliknya, lima kecamatan Kota Surakarta berada di luar *Area of Applicability* data latih dan menyumbang 43,6%–64,1% jumlah kuadrat galat gabungan karena premi aglomerasi perkotaan inti tidak terwakili oleh keenam kabupaten latih.

Rangkaian analisis sensitivitas dan diagnostik metodologis memperjelas batas kemampuan serta peran yang tepat bagi masing-masing pendekatan. Pertama, ledakan galat OLS dan GWR pada replikasi tujuh prediktor bertarget `ln(harga)` dipicu oleh kombinasi kolinearitas lokal ekstrem (`κ` lokal melampaui 30 pada 127/127 lokasi) dan retransformasi eksponensial di wilayah ekstrapolasi Surakarta; koreksi *smearing* Duan memperbaiki bias skala rupiah di enam kabupaten non-Surakarta tetapi tidak mencegah ledakan eksponensial di luar AoA. Kedua, penerapan gerbang penyaringan kolinearitas (empat fitur dengan `VIF ≤ 2,05`), skala linear berkendala nonnegatif, dan protokol penyetelan yang setara menurunkan MAE gabungan Ridge global menjadi Rp496.144/m² (R² 0,822; `0/127` prediksi negatif) dan GWR Fixed + Ridge menjadi Rp520.210/m², dengan hasil yang tidak peka terhadap pergantian empat alternatif titik representatif kecamatan. Ketiga, nilai tambah utama GWR pada data agregat kecamatan ini terletak pada perannya sebagai **alat diagnostik struktur spasial** yang meredam autokorelasi residual (menurunkan Global Moran's I menjadi 0,073–0,075 hingga tidak signifikan secara statistik), bukan sebagai pemenang prediksi lintas kabupaten. Karena definisi pengukuran primer harga dan metode perataan kecamatan pada sumber sekunder belum tervalidasi ke ATR/BPN serta fitur aksesibilitas pasca-galat masih berupa proksi garis lurus pada lipatan yang sama, seluruh hasil penelitian ini dibatasi ketat pada analisis metodologis rata-rata kecamatan tahun 2020 dan tidak boleh digunakan untuk penilaian properti individual maupun kebijakan perpajakan tanah.

## 8. Ketersediaan Kode, Data, dan Reproduksi

Repositori publik penelitian tersedia di https://github.com/sqiftree/LandPredict. Seluruh eksperimen dikemas secara modular di dalam paket Python `tanah`: `config` dan `data` untuk kontrak skema 127 kecamatan, `models` dan `selection` untuk estimator serta validasi bersarang LOKO, `experiment` dan `verification` untuk eksekusi dan pemeriksaan ulang metrik konfirmatori, `colab` untuk replikasi tujuh prediktor, `sensitivity` untuk analisis faktorial GWR, `rigor` untuk diagnostik statistik-spasial lanjutan (bootstrap blok, AoA, Moran's I/LISA, koreksi Duan, Quasi-Poisson QMLE, benchmark setara, dan sensitivitas titik), serta `provenance` untuk pencatatan versi pustaka dan sidik SHA-256 berkas masukan maupun keluaran.

Untuk mereproduksi seluruh artefak terverifikasi, menjalankan pengujian otomatis, dan membangun ulang naskah Markdown beserta dokumen Word dari satu rangkaian perintah pada lingkungan Python 3.12 (`requirements.txt`, dengan dependensi terpin lengkap pada `artifacts/requirements-resolved.txt`):

> python -m tanah run --output hasil/baseline && python -m tanah run --koordinat data/koordinat.csv --output hasil/spasial && python -m tanah sensitivity --verify && python -m tanah rigor --verify && python scripts/build_manuscript.py && python -m unittest discover -s tests

Generator `scripts/build_manuscript.py` secara otomatis mengaudit ulang kecocokan 381 nilai sumber terhadap PDF lampiran, memverifikasi integritas 127 prediksi uji dan sidik audit di `artifacts/spasial/`, `artifacts/tujuh_prediktor_big/`, `artifacts/sensitivitas_gwr/`, serta `artifacts/diagnostik_lanjut/`, lalu menyusun `docs/harga_tanah_solo_raya_2020.md` dan `docs/harga_tanah_solo_raya_2020.docx` tanpa campur tangan penyalinan angka manual. Eksekusi terisolasi tanpa jaringan juga didukung melalui kontainer Docker (`docker build -t gwr-solo-raya:local .` diikuti `python scripts/reproduce.py`).

## Referensi

{{REFERENCES}}

## Lampiran: Status dan Kontribusi Tim

Naskah ini melaporkan satu eksperimen konfirmatori terkunci (Bagian 4) yang dipisahkan secara eksplisit dari eksplorasi fitur tambahan dan diagnostik sensitivitas metodologis (Bagian 6.3–6.8). Pembagian kontribusi anggota tim penelitian tercantum pada tabel berikut.

{{CONTRIBUTIONS}}
