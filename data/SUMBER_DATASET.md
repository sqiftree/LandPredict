# Audit sumber dataset untuk presentasi

Tanggal pemeriksaan: 17 November 2026. Dataset: `harga_tanah_2020.csv`, 127 kecamatan, tahun acuan 2020. Kesimpulan: dapat dipakai sebagai eksperimen atas data sekunder yang dapat ditelusuri, tetapi belum layak disebut dataset transaksi tanah resmi yang seluruh angka dan definisinya telah divalidasi ke produsen primer.

## 1. Rantai sumber dan tingkat bukti

| Komponen | Sumber yang benar-benar dipakai | Bukti dan batas verifikasi |
| --- | --- | --- |
| Tiga kolom numerik CSV | Lampiran A penelitian Salim Aziz, Repositori UNS, dokumen 111483 | 127 kunci dan 381 nilai cocok dengan ekstraksi indeks publik. Belum dibandingkan visual dengan PDF asli. |
| Harga rata-rata kecamatan | Lampiran tersebut; artikel Aziz, Rahayu, Istanabi (2023) menyebut Bhumi ATR-BPN 2020 pada Gambar 4–5, hlm.147 | Atribusi primer masih melalui penulis sumber; arsip layer harga, jenis harga, sampel dan rumus perataan belum tersedia. |
| Jumlah penduduk | Lampiran tersebut | Artikel mengacu BPS; belum ada pencocokan langsung seluruh 127 angka ke tabel BPS. Lima angka Surakarta cocok dengan Gambar 1.10 laporan pemerintah kota. |
| Fasilitas regional | Lampiran tersebut | Artikel Tabel 3 hlm.149 menyebut observasi peneliti 2023 menggunakan data tahun 2020. Total antarsumber tidak konsisten. |
| Koordinat | Poligon administratif BIG yang diolah program | Bukan koordinat objek transaksi. Sumber, CRS, alias dan keterbatasan historis ada di SUMBER_KOORDINAT.md. |

Sumber langsung dan lokasi bukti:

- [Lampiran UNS](https://digilib.uns.ac.id/dokumen/download/111483/NzEwODU3/Potensi-Struktur-Ruang-Wilayah-Polisentris-Lampiran_Salim-Aziz.pdf): judul tabel Lampiran A, tahun 2020. Akses unduhan langsung saat audit mengembalikan HTML permintaan login, bukan PDF. Snapshot `sumber/lampiran_uns_index.txt` menyimpan hanya baris data faktual dari indeks pencarian; bukan salinan PDF asli. Penomoran halaman pada CSV belum diaudit visual.
- [Artikel Aziz dkk. (2023), DOI 10.14710/jpk.11.2.140-154](https://ejournal2.undip.ac.id/index.php/jpk/article/download/21331/pdf): PDF penerbit dapat diunduh. Tabel 1 hlm.145, Gambar 4–5 hlm.147, Tabel 3 hlm.149. Artikel merupakan pembanding, bukan otomatis versi yang identik dengan lampiran.
- [Laporan Pemerintah Kota Surakarta](https://dlh.surakarta.go.id/web/file/20220714104304.pdf): Gambar 1.10, hlm.i-20, kolom 2020, mencantumkan BPS Kota Surakarta 2021. Angka Laweyan 88.524, Serengan 47.778, Pasar Kliwon 78.517, Jebres 138.775, Banjarsari 168.770; jumlah 522.364. Ini pemeriksaan terbatas atas grafik tersebut, bukan pengesahan seluruh tabel dalam laporan.

## 2. Temuan yang harus disampaikan

Pencocokan transkripsi lulus: harga, penduduk, dan fasum pada seluruh 127 kecamatan sama dengan indeks lampiran. Ini memperkecil kemungkinan salah salin, tetapi tidak membuktikan pengukuran awalnya benar. Seluruh hasil komputasi tetap memakai CSV asli, SHA-256 `b86e3c363db243a4cbb7ccfe38f6868bd3300898f1eeea6eee38752b57f0ae66`.

Total fasilitas berbeda di semua wilayah. Penjumlahan enam kategori pada Tabel 3 artikel memperlakukan tanda minus sebagai nol.

| Wilayah | CSV/lampiran | Artikel | Selisih CSV − artikel |
| --- | --- | --- | --- |
| Surakarta | 26 | 25 | +1 |
| Boyolali | 9 | 11 | −2 |
| Sukoharjo | 14 | 11 | +3 |
| Karanganyar | 13 | 12 | +1 |
| Wonogiri | 9 | 8 | +1 |
| Sragen | 10 | 11 | −1 |
| Klaten | 17 | 15 | +2 |

Total penduduk juga berbeda untuk Surakarta (CSV 522.364; artikel 576.412), Sukoharjo (911.966; 907.587), dan Karanganyar (938.808; 931.963). Empat wilayah lain cocok. Pembanding artikel adalah penjumlahan urban dan rural pada Tabel 1. Perbedaan ini belum dapat ditentukan sebagai salah ketik, beda versi data, beda definisi atau beda cakupan. Jangan mengganti angka kecamatan dengan membagi total artikel secara proporsional: itu akan menciptakan data yang tidak diamati.

Untuk harga, rata-rata sederhana CSV Surakarta dan Boyolali, dibulatkan ke rupiah, cocok dengan angka yang dibahas artikel. Kecocokan agregat ini belum memvalidasi metode pembentukan harga tiap kecamatan. Jangan menyebut label sebagai harga transaksi, NJOP, harga penawaran, atau nilai zona tertentu sebelum memperoleh metadata primernya.

Ejaan Sidoarjo pada Wonogiri memang muncul pada indeks lampiran, sehingga bukan kesalahan transkripsi CSV. Pemadanan ke Sidoharjo di geometri harus tetap dijelaskan sebagai alias yang memerlukan dukungan identitas administratif; keberadaan satu padanan nama saja bukan bukti batas historis.

Kolom tambahan luas terbangun pada indeks perlu audit sebelum digunakan. Contohnya Jebres 1.391,1 dibanding luas kecamatan 1.258, dan Laweyan 892,2 dibanding 864. Luas terbangun melebihi luas kecamatan jika unit dan cakupannya sama. Ada pula luas terbangun sangat kecil pada beberapa kecamatan. Ini tanda untuk memeriksa unit, delimiter, cakupan dan PDF asli; bukan alasan mengoreksi angka dengan tebakan. Kolom tersebut belum dipakai sebagai prediktor eksperimen.

## 3. Jawaban yang aman saat presentasi

**Dari mana datasetnya?** Dataset sekunder tingkat kecamatan ditranskripsi dari Lampiran A penelitian Salim Aziz di UNS, tahun acuan 2020. Kami mengaudit 127 identitas dan 381 nilai terhadap indeks publik lampiran. Artikel pendukung tersedia di jurnal penerbit. Verifikasi ke seluruh data primer belum selesai.

**Apakah titik ditentukan oleh harga tanah?** Tidak. Program menggabungkan poligon tiap kecamatan, memproyeksikan ke UTM 49S, lalu mengambil point-on-surface dan mengekspor longitude/latitude WGS84. Harga tidak dipakai dalam konstruksi titik. Nilai harga adalah label agregat kecamatan, bukan harga sebidang tanah pada titik itu. Semua 127 titik berada dalam poligon padanannya; poligon yang lebih baru belum terbukti sama dengan batas 2020.

**Mengapa memilih penduduk dan fasum?** Keduanya tersedia bersama target dan dapat diuji sebagai prediktor aktivitas wilayah. Dasar konseptual bukan bukti bahwa hubungan bersifat kausal. KNN memakai jarak antarfitur yang distandardisasi; GWR memakai jarak geografis untuk bobot regresi lokal. Perbandingan dilakukan pada blok kabupaten/kota yang sama.

**Apakah hasil dapat dipertanggungjawabkan?** Prosedur komputasi dan sumber sekundernya dapat ditelusuri. Validitas substantif label masih bersyarat pada mutu sumber awal. Temuan saat ini adalah GWR belum unggul konsisten untuk dataset dan spesifikasi ini; bukan bukti universal bahwa geografi tidak berpengaruh.

## 4. Bukti yang masih perlu dilengkapi tim

1. Dapatkan PDF asli Lampiran A melalui akses sah UNS/penulis, simpan hash dan tanggal akses, lalu cocokkan tabel dan halaman secara visual.
2. Minta atau temukan metadata/arsip harga 2020 yang dipakai penulis: nama layer, definisi nilai, unit, cakupan, metode agregasi ke kecamatan dan pembobotan. Akses Bhumi saat ini saja tidak membuktikan kondisi 2020.
3. Rekonsiliasi fasum dengan daftar objek, kategori, tahun dan identitas kecamatan. Konfirmasi tiga selisih penduduk dengan tabel resmi BPS 2020; jangan mencampur SP2020, registrasi penduduk, dan proyeksi tanpa penjelasan.
4. Validasi batas administratif 2020, termasuk kecamatan hasil pemekaran Boyolali dan kedua alias nama. Untuk eksperimen pengembangan, jalankan ulang seluruh model setelah dataset tervalidasi; jangan menimpa versi acuan.

## 5. Reproduksi audit

Jalankan `python3 scripts/audit_dataset.py` dari akar repositori. Tidak memerlukan jaringan atau pustaka tambahan. Hasil disimpan di `artifacts/data_audit/`: perbandingan 381 sel, perbandingan fasum, perbandingan penduduk, serta JSON ringkasan dan hash. Skrip menguji konsistensi terhadap snapshot yang diarsipkan; tidak mengautentikasi dokumen primer dan tidak menyelesaikan perbedaan definisi antarsumber.

## 6. Koreksi referensi pada draf terbaru

Metadata penerbit untuk DOI 10.14710/jgundip.2019.25155 mencantumkan Oktaviani Arumingtyas, Sawitri Subiyanto, dan Hana Firdaus, volume 8(4), halaman 165–174. Draf sebelumnya menuliskan penulis dan halaman berbeda; sudah dikoreksi mengikuti [laman penerbit](https://ejournal3.undip.ac.id/index.php/geodesi/article/view/25155/0). Referensi Janssen dkk. (2022) terverifikasi judul dan bibliografinya; penggunaannya dipersempit menjadi konteks pemilahan spasial, tanpa mengklaim dukungan spesifik variabel harga yang belum diperiksa.
