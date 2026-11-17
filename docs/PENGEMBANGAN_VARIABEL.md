# Pengembangan variabel berdasarkan jurnal dan rencana uji

Disusun 18 November 2026. Status: rancangan pengumpulan dan pengujian, bukan hasil eksperimen tambahan. Daftar terstruktur terdapat di `data/kandidat_variabel.csv`: 25 kandidat termasuk dua variabel baseline. Sebagian merupakan cara berbeda mengukur konsep yang sama, sehingga bukan 25 sumber informasi independen. Belum ada angka korelasi atau p-value baru yang dilaporkan.

## 1. Tujuan yang dapat disampaikan kepada dosen

Penelitian memperluas kandidat berdasarkan literatur, kemudian menilai kekuatan hubungan, kestabilan antarwilayah, kolinearitas dan manfaat prediksi. Tujuannya bukan mengumpulkan variabel sampai memperoleh p-value kecil. Variabel yang tidak signifikan tetap dilaporkan; hasil studi lain adalah alasan untuk menguji, bukan jaminan signifikansi di Solo Raya.

Unit analisis tetap rata-rata kecamatan tahun 2020. Penelitian berbasis bidang tanah, NJOP, harga penawaran atau transaksi tidak otomatis memiliki target dan skala yang sama. Operasionalisasi tingkat kecamatan berikut adalah rancangan penelitian ini, kecuali dinyatakan identik dengan sumber.

## 2. Jurnal pendukung dan batas penggunaannya

| ID | Referensi yang diperiksa | Dukungan yang relevan | Batas penerapan |
| --- | --- | --- | --- |
| R1 | Aziz, Rahayu, Istanabi (2023), Jurnal Pengembangan Kota 11(2), 140–154. DOI 10.14710/jpk.11.2.140-154 | Penduduk/kepadatan, fasilitas regional, penggunaan lahan dan pusat aktivitas Solo Raya | Analisis klaster, bukan bukti pengaruh kausal atau seleksi fitur prediksi harga |
| R2 | Saefuddin, Widyaningsih, Ginting, Mamat (2012), Asian Journal of Mathematics & Statistics 5, 132–141. DOI 10.3923/ajms.2012.132.141 | Akses gerbang tol, jalan arteri dan fasilitas; pembandingan OLS/GWR Tangerang Selatan | Data titik dan log-harga; bukan rata-rata kecamatan Solo Raya |
| R3 | Syahar, Ramadhan, Putri (2020), International Journal of GEOMATE 19(72), 109–116 | CBD, fasilitas pelayanan, penggunaan lahan dan bencana pada koridor Padang | Data 2014. Jarak jalan utama tidak menunjukkan kontribusi besar; jangan menganggap seluruh kandidat signifikan |
| R4 | Arumingtyas, Subiyanto, Firdaus (2019), Jurnal Geodesi Undip 8(4), 165–174. DOI 10.14710/jgundip.2019.25155 | Aksesibilitas, pasar, fasilitas umum/sosial pada bidang tanah Tlogosari Kulon | Membedakan harga pasar wajar dan NJOP; bukan efek jumlah fasum agregat |
| R5 | Berawi dkk. (2018), International Journal of Technology 9(7), 1329–1337. DOI 10.14716/ijtech.v9i7.2589 | Jarak stasiun dan nilai tanah dalam model hedonik | Konteks commuter rail; belum membuktikan efek terminal bus atau semua jenis stasiun |
| R6 | Huang & Hewings (2021), Land 10(3), 261. DOI 10.3390/land10030261 | Kemiringan lereng dan nilai tanah Auckland | Penurunan harga terkait slope pada konteks studi; rerata slope kecamatan merupakan adaptasi |
| R7 | Zhang, Hu, Li, Zhang, Yang, Qu (2021), Applied Geography, artikel 102442. DOI 10.1016/j.apgeog.2021.102442 | POI dan cahaya malam untuk pemodelan harga tanah residensial Wuhan; pendidikan dan amenitas alam | Model grid di kota lain; proporsi pohon dan jarak taman di sini adalah adaptasi konsep, bukan daftar variabel identik |
| R8 | Arafah, Hanifah, Sabila, Asra, Djamaluddin (2026), The Journal of Indonesia Sustainable Development Planning 7(2), 290–304. DOI 10.46456/jisdep.v7i2.971 | Menguji 14 prediktor atas 61 titik NJOP 2025; akses supermarket dan rumah sakit menonjol | Tahun/jenis harga berbeda. Sebagian variabel fasilitas dan risiko bencana tidak signifikan |

Tautan penerbit: [R1](https://ejournal2.undip.ac.id/index.php/jpk/article/view/21331), [R2](https://scialert.net/fulltext/?doi=ajms.2012.132.141), [R3](https://geomatejournal.com/geomate/article/view/1136), [R4](https://ejournal3.undip.ac.id/index.php/geodesi/article/view/25155/0), [R5](https://ijtech.eng.ui.ac.id/article/view/2589), [R6](https://www.mdpi.com/2073-445x/10/3/261), [R7](https://www.sciencedirect.com/science/article/pii/S0143622821000588), [R8](https://jurnal.pusbindiklatren.bappenas.go.id/lib/jisdep/article/view/971). Dukungan dirangkum dari bagian yang tersedia pada laman penerbit; ini bukan tinjauan sistematis seluruh isi semua artikel.

## 3. Dua puluh lima kandidat

| Kelompok | Kandidat | Dasar |
| --- | --- | --- |
| Demografi | 1. Jumlah penduduk; 2. Kepadatan penduduk | R1; kepadatan per km² diadaptasi |
| Intensitas fasilitas | 3. Jumlah fasum regional; 4. Fasum per km² | R1; normalisasi kepadatan diadaptasi |
| Akses pusat dan jalan | 5. Jarak pusat kegiatan Solo; 6. Jarak subpusat; 7. Jarak arteri/kolektor; 8. Jarak gerbang tol; 9. Kepadatan jalan | R1–R3; subpusat dan kepadatan jalan merupakan adaptasi |
| Akses layanan | 10. Jarak pasar; 11. Rumah sakit; 12. Sekolah menengah; 13. Perguruan tinggi | R1–R4, R7–R8; jenjang dan agregasi ditetapkan penelitian ini |
| Transportasi | 14. Jarak stasiun penumpang; 15. Terminal bus | R5 untuk stasiun; terminal merupakan perluasan konsep R1/R5 |
| Tutupan dan aktivitas | 16. Proporsi terbangun; 17. Pertanian; 18. Tutupan pohon; 19. Intensitas cahaya malam | R1/R3/R7; definisi kelas raster adalah adaptasi |
| Topografi | 20. Rerata slope; 21. Proporsi lereng curam; 22. Rerata elevasi | R6 langsung untuk slope; proporsi dan elevasi merupakan perluasan hipotesis |
| Bahaya dan lingkungan | 23. Proporsi rawan banjir; 24. Jarak taman publik; 25. Proporsi kawasan industri | R1/R3/R7/R8 pada tingkat konsep; ukuran spesifik diadaptasi |

Variabel 22, 24, 25 serta beberapa ukuran alternatif mempunyai dukungan lebih tidak langsung; bukan prioritas yang setara dengan jarak jalan, rumah sakit, stasiun atau slope. Ambang lereng curam 15° pada registry adalah usulan operasional yang harus ditetapkan sebelum analisis, bukan ambang yang diklaim dibuktikan oleh R6. Arah hubungan industri atau akses transportasi dapat campuran karena manfaat akses dan gangguan lingkungan.

## 4. Prioritas pengumpulan dan sumber

Mulai dari sepuluh kandidat: kepadatan penduduk, fasum, jarak pusat kegiatan, jarak jalan utama, jarak pasar, jarak rumah sakit, jarak stasiun, proporsi terbangun, cahaya malam, dan rerata slope. Sepuluh ini adalah prioritas pengumpulan, bukan jumlah fitur yang wajib masuk model akhir.

| Sumber | Variabel | Status dan aturan tahun |
| --- | --- | --- |
| Lampiran Aziz + BPS SP2020 | Penduduk dan fasum; kepadatan turunan | Dua kolom baseline tersedia. Densitas memakai geometri arsip yang lebih baru harus diberi label proksi, bukan kepadatan resmi 2020. Rekonsiliasi fasum tetap diperlukan. |
| BIG/RBI, PUPR, BPJT, RTRW | Jalan, gerbang tol, pusat/subpusat | Kandidat penyedia, belum ada layer historis lengkap dalam proyek. Verifikasi objek aktif dan dokumen berlaku 2020. |
| Dinas terkait, Kemenkes, Dapodik, PDDikti, KAI/DJKA, Dishub | Lokasi fasilitas | Cari arsip 2020 dan tahun operasional, bukan mengambil daftar saat ini lalu memberi label 2020. Podes 2018/2021 tidak boleh otomatis dilabeli 2020. |
| [ESA WorldCover 2020 v100](https://esa-worldcover.org/en/data-access) | Terbangun, cropland, tree cover | Produk global 10 m tahun 2020 tersedia; belum diekstrak untuk 127 kecamatan. Cropland tidak sama dengan sawah, tree cover tidak sama dengan taman. |
| [GHSL GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php) | Permukaan terbangun | Alternatif WorldCover; periksa epoch dan metode pembentukan data. Luas permukaan bangunan tidak sama dengan luas kelas built-up. Jangan memasukkan kedua ukuran sebagai informasi independen tanpa pemeriksaan. |
| [EOG VIIRS](https://eogdata.mines.edu/products/vnl/) | Cahaya malam | Pilih komposit tahunan 2020, versi produk, band dan kualitas observasi. Belum diunduh untuk proyek. Radiansi bukan pendapatan atau PDRB yang diukur langsung. |
| [BIG DEMNAS](https://big.go.id/content/produk/demnas) | Elevasi dan slope | Produk tersedia; resolusi 0,27 arcsecond. Catat sumber/waktu akuisisi tile; bukan dataset observasi tunggal 2020. |
| BPBD/BNPB InaRISK | Paparan banjir | Layer sesuai periode belum tersedia dalam proyek. Pisahkan peta bahaya, risiko dan catatan kejadian; ketiganya berbeda. |

Untuk raster, hitung statistik zonal dalam poligon kecamatan dengan pembobot luas, mask NoData, dan catatan proporsi wilayah yang tercakup. Jangan mengisi piksel tanpa observasi dengan nol secara otomatis. Proporsi dihitung terhadap luas yang didefinisikan secara konsisten.

Untuk jarak, tetapkan satu metode utama sebelum melihat target: jarak garis lurus dalam CRS metrik dari titik representatif kecamatan ke objek yang relevan. Ini proksi akses wilayah, bukan rerata perjalanan penduduk. Jarak jaringan/waktu perjalanan adalah eksperimen berbeda dan memerlukan jaringan historis. Objek terdekat boleh berada di kecamatan/kabupaten sebelah; pembatasan administratif tidak boleh memotong akses secara arbitrer. Lokasi pusat ditetapkan dari dokumen independen, bukan dari kecamatan dengan harga tertinggi.

## 5. Rancangan korelasi dan seleksi yang dapat dipertanggungjawabkan

1. **Bekukan daftar kandidat dan definisi.** Catat hipotesis, sumber, tahun, cakupan, transformasi yang direncanakan, serta alasan kandidat tidak tersedia. Tabel kosong tetap kosong, bukan nol dan bukan nilai tebakan.
2. **Audit ketersediaan 127 wilayah.** Identitas, satuan, missingness dan jenis harga harus konsisten. Variabel kabupaten yang diulang pada kecamatan tidak menjadi 127 pengukuran independen. Bentuk persil, luas satu bidang, jumlah kamar dan sertifikat individu tidak cocok untuk target rata-rata kecamatan tanpa agregasi sumber yang sah.
3. **Bedakan eksplorasi dari inferensi.** Pearson mengukur hubungan linear; Spearman hubungan monoton. Tentukan Spearman sebagai layar eksplorasi utama dan Pearson sebagai sensitivitas sebelum melihat hasil. Laporkan koefisien, arah, jumlah pasangan tersedia, distribusi dan outlier; p-value kecil bukan ukuran besarnya hubungan.
4. **Tangani banyak pengujian.** Jika p-value eksploratif dihitung, laporkan p mentah dan koreksi Benjamini–Hochberg pada seluruh keluarga uji yang ditetapkan. Koreksi ini tidak memperbaiki p-value yang sejak awal tidak valid akibat ketergantungan spasial. Karena kecamatan berdekatan tidak independen, p-value standar hanya nominal/eksploratif; klaim inferensial memerlukan model atau prosedur resampling yang asumsi spasialnya dijelaskan. Tujuh blok membatasi presisi inferensi berbasis kelompok.
5. **Periksa kestabilan dan kolinearitas.** Bandingkan arah/kekuatan hubungan pada kelompok wilayah dan ketika satu wilayah dikeluarkan. Populasi dan kepadatan, fasum dan kepadatan fasum, serta berbagai ukuran urbanisasi dapat sangat berkorelasi. Gunakan matriks antarprediktor, VIF dan diagnostik desain lokal; jangan memasukkan semua proporsi tutupan yang menjumlah 100% bersama intersep. VIF bukan bukti kausal dan tidak menggantikan pemeriksaan GWR lokal.
6. **Seleksi untuk prediksi harus berada di dalam validasi.** Pertahankan tujuh lipatan luar. Imputasi, transformasi yang dipelajari, penyaringan korelasi dan pemilihan fitur dilakukan hanya pada bagian fit setiap lipatan dalam; parameter dan jumlah fitur dibandingkan berdasarkan MAE validasi dalam. Setelah dipilih, prosedur dipasang kembali pada seluruh data latih luar. Target uji luar tidak dipakai memilih fitur. Eksplorasi seluruh 127 baris, bila ditampilkan, tidak boleh diam-diam menentukan spesifikasi yang lalu diklaim diuji secara independen.
7. **Gunakan model parsimonious.** Mulai dari kelompok tematik yang ditentukan sebelumnya; jangan mencoba semua kombinasi 25 fitur. Ukuran sampel efektif GWR lokal dapat jauh di bawah 127. Periksa rank, kestabilan koefisien dan distribusi bobot; sekadar jumlah baris lebih besar dari jumlah parameter tidak menjamin estimasi lokal stabil.
8. **Laporkan semua hasil.** Tampilkan variabel yang kuat/lemah/tidak stabil, fitur terpilih per lipatan, serta MAE/RMSE di luar sampel. Korelasi bivariat kecil tidak meniadakan manfaat nonlinier atau interaksi pada KNN/Tree. Tidak ada jaminan model dengan p-value terkecil memberi prediksi terbaik.

Landasan pengujian berganda: Benjamini & Hochberg (1995), *Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing*, JRSS B 57(1), 289–300, [DOI](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x). Prosedur membutuhkan asumsi tentang distribusi p-value dan ketergantungan; jangan menyebutnya penyelesaian otomatis masalah spasial. Landasan validasi berstruktur: Roberts dkk. (2017), [DOI](https://doi.org/10.1111/ecog.02881).

## 6. Keluaran tahap berikutnya

Setelah data tambahan tersedia, hasil yang diperlukan adalah dataset versi baru dengan provenance per kolom, audit cakupan/tahun, tabel korelasi dan koreksi pengujian berganda dengan batas interpretasinya, matriks kolinearitas, serta eksperimen nested validation yang baru. Model baseline dua prediktor dipertahankan sebagai pembanding. Hingga saat itu, tidak ada klaim bahwa 25 variabel telah terkumpul atau bahwa salah satunya paling signifikan di Solo Raya.
