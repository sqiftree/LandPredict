# Penelusuran BHUMI dan ATLAS untuk penelitian harga tanah

Tanggal akses: 18 November 2026. Unit penelitian: 127 kecamatan Solo Raya, tahun 2020. Status: inventaris sumber dan rancangan penggunaan, bukan hasil ekstraksi geometri atau variabel numerik. Daftar terstruktur: `data/inventaris_bhumi.csv` (sembilan dataset/fitur, tidak berarti sembilan variabel independen).

## Bukti dan batas akses

Penelusuran dilakukan melalui hasil indeks pencarian halaman resmi, percobaan pembukaan halaman, dan permintaan HTTPS publik. Halaman BHUMI utama/Unsur Peta gagal HTTP 502; Katalog Data dan ATLAS mengalami timeout pada pembukaan langsung. Curl dari sandbox gagal DNS; percobaan jaringan di luar sandbox gagal verifikasi issuer sertifikat lokal. Verifikasi TLS tidak dinonaktifkan. Karena itu, dokumen ini tidak mengklaim pemeriksaan aplikasi live, skema atribut live, unduhan zona, atau cakupan kecamatan. Kegagalan akses tidak membuktikan bahwa portal maupun data tersebut tidak tersedia bagi pengguna lain.

Dokumentasi resmi terindeks memberi bukti berikut:

| Sumber | Temuan yang didukung | Yang belum dibuktikan |
| --- | --- | --- |
| [Katalog Data BHUMI](https://bhumi.atrbpn.go.id/bantuan/katalog_data) | Menyebut bidang tanah, batas administrasi, ZNT; memperkenalkan ATLAS serta kategori dataset utama/turunan/eksternal | Daftar lengkap layer Solo Raya, tahun, skema, izin dan endpoint unduhan |
| [ATLAS ATR/BPN](https://atlas.atrbpn.go.id/) | Katalog terindeks menampilkan LBS Parsial Pulau Jawa, keterjangkauan kesehatan, kawasan bencana gunung api, dan lokasi kantor pertanahan | Detail dataset, tahun pengukuran, CRS, versi, cakupan Solo Raya, format unduh dan lisensi |
| [Toolbox BHUMI](https://bhumi.atrbpn.go.id/bantuan/fitur_toolbox) | Dokumentasi routing, isochrone, pengukuran dan legenda pola ruang | Jaringan yang berlaku 2020, kecepatan/model routing dan layer RTRW lokal |
| [Infografis BHUMI](https://bhumi.atrbpn.go.id/bantuan/fitur_infografis) | Penghitungan bidang pada area administratif atau poligon unggahan | Kelengkapan bidang, cakupan historis, dan validitas indikator kepadatan |
| [Panduan overlay](https://bhumi.atrbpn.go.id/panduan/tata_cara_overlay) | Impor file sendiri dan layanan WMS ke peta | Kemampuan ekspor massal layer sumber; impor GeoJSON bukan bukti unduhan GeoJSON |
| [Landing/disclaimer](https://bhumi.atrbpn.go.id/bantuan/landing) | Dokumentasi menyatakan data tidak dijamin sepenuhnya akurat/mutakhir/lengkap; acuan resmi melalui pelayanan informasi publik | Validasi primer 127 harga tahun 2020 |

Hasil pencarian arsip ZNT 2020 dan nama beberapa wilayah Solo Raya pada domain ATLAS tidak menghasilkan metadata historis yang dapat dipakai dalam sesi ini. Tidak menyimpulkan seluruh katalog hanya memiliki tujuh dataset meskipun halaman terindeks menampilkan tujuh sumber. Tidak menggunakan mirror pihak ketiga sebagai pengganti bukti resmi.

## Kaitan dengan paper dan prioritas variabel

Kode R1–R8 mengacu kepada daftar jurnal dan batas interpretasi di `docs/PENGEMBANGAN_VARIABEL.md`. Temuan portal adalah sumber kandidat data; bukan bukti bahwa variabel memengaruhi harga.

1. **Proporsi sawah — prioritas penelusuran metadata.** LBS Parsial Pulau Jawa berpotensi mendukung konsep penggunaan lahan R1/R3. Setelah cakupan dan tahun sah, hitung luas irisan sawah dengan kecamatan dibagi luas kecamatan dalam CRS metrik yang sesuai. Ini alternatif khusus sawah, bukan sinonim kelas cropland WorldCover. Wilayah yang tidak tercakup diberi missing, bukan nol. Metadata perlu membedakan area benar-benar bukan sawah dengan area yang belum dipetakan.
2. **Akses layanan kesehatan — prioritas penelusuran metadata.** Mendukung konsep akses fasilitas R2/R8. Jika tersedia indeks keterjangkauan, periksa arah skala dan cara pembentukannya sebelum agregasi berbobot luas atau penduduk. Jangan menjadikannya jarak rumah sakit dalam km. Indeks berbobot penduduk juga dapat mengulang informasi prediktor penduduk; periksa kolinearitas. Daftar fasilitas dan jaringan mesti sesuai 2020.
3. **Paparan bahaya gunung api — kandidat tambahan bersyarat.** Relevan sebagai adaptasi konsep bencana R3/R8, belum merupakan dukungan langsung efek spesifik gunung api di Solo Raya. Jika peta KRB beserta edisinya diperoleh, hitung proporsi wilayah pada kelas yang ditetapkan sebelum melihat harga. Pisahkan dari banjir; peta bahaya bukan data kejadian maupun kerugian. Cari referensi empiris khusus sebelum menjadikannya variabel utama.
4. **Pola ruang — pisahkan rencana dan realisasi.** Dokumen RTRW berlaku 2020 dapat membantu menentukan pusat/subpusat secara independen dari harga atau proporsi zona industri yang direncanakan. Itu berbeda dengan prediktor penggunaan industri aktual yang sudah direncanakan. Jangan mengganti keduanya tanpa mengubah definisi hipotesis.
5. **Routing/isochrone — metode alternatif.** Dapat membantu konsep akses jalan/fasilitas/stasiun R2/R3/R5 jika jaringan, moda dan periode diketahui. Fitur aplikasi saat ini tidak memvalidasi waktu perjalanan tahun 2020. Metode utama jarak geometris yang tercatat dalam rencana tetap terpisah dari eksperimen jaringan.
6. **Bidang terpetakan dan jarak kantor pertanahan — tidak diprioritaskan.** Belum ada dukungan langsung dari registry jurnal saat ini. Kepadatan bidang terpetakan dapat lebih mencerminkan kemajuan pemetaan daripada intensitas pembangunan. Jangan menambah variabel hanya karena tampil di katalog.

Penduduk, fasum, lokasi pasar/sekolah/kampus/stasiun, radiansi malam, dan slope belum diperoleh dari penelusuran BHUMI ini. Sumber alternatif yang sudah dicatat (BPS/dinas, WorldCover 2020, VIIRS 2020, BIG DEMNAS) tetap diperlukan; label sumber kandidat tidak berarti datanya sudah diunduh.

## ZNT sebagai pemeriksaan target

Artikel Aziz mengatribusikan harga ke BHUMI 2020, tetapi layer, sampel, dan rumus perataan belum diperoleh. Jangan menyatakan target pasti hasil agregasi ZNT. Jangan menggunakan nilai/rentang ZNT atau rata-rata harga satu kabupaten sebagai prediktor apabila informasi tersebut berasal dari target yang sama atau melibatkan kabupaten uji. Itu berisiko kebocoran target dan merusak pertanyaan penelitian leave-kabupaten-out.

Apabila kelak ada nilai skalar zona yang sah, salah satu calon ringkasan wilayah ialah rata-rata berbobot luas irisan:

`nilai_wilayah = sum(nilai_zona * luas_irisan) / sum(luas_irisan_valid)`

Rumus ini usulan ukuran penelitian, bukan rumus Aziz yang telah diverifikasi; hasilnya nilai zona berbobot luas pada area tercakup, bukan rata-rata harga transaksi. Laporkan cakupan `luas_irisan_valid / luas_kecamatan`, tangani zona bertumpuk dan celah. Jika hanya kelas/rentang tersedia, jangan mengambil titik tengah lalu menyebutnya nilai resmi, terlebih untuk kelas terbuka.

Koordinat GWR tetap satu titik di dalam poligon kecamatan yang diperoleh secara geometris. Harga tidak menentukan titik tersebut. Klik pada BHUMI menunjukkan lokasi yang dipilih pengguna; titik klik bukan otomatis lokasi sampel transaksi atau pusat kecamatan.

## Syarat sebelum data masuk eksperimen

- Identitas layer/versi, produsen, URL metadata dan unduhan, waktu akses, tahun observasi, definisi atribut/satuan, CRS dan lisensi harus tercatat. Seluruh atribut ini saat ini masih belum tersedia untuk kandidat ATLAS.
- Arsip berkas dan hash; cocokkan 127 kunci serta batas 2020, periksa cakupan dan missingness. Data setelah 2020 harus diberi label proksi atau eksperimen periode berbeda, bukan diam-diam mengganti data 2020.
- Untuk fasilitas, simpan bukti beroperasi pada 2020. Untuk tata ruang, simpan tanggal berlaku; untuk hazard, simpan edisi model; untuk raster, simpan mask NoData dan tahun observasi.
- Jangan memasukkan hasil harga BHUMI sebagai fitur target turunan. Seleksi variabel, imputasi, dan standardisasi tetap dilakukan hanya pada bagian latih validasi bersarang.
- Informasi yang dapat diminta kepada penyedia/penulis: layer ZNT historis 2020 untuk tujuh kabupaten/kota, metadata tahun/satuan, metode perataan harga kecamatan, edisi LBS/KRB/akses kesehatan yang relevan, cakupan dan izin penggunaan. Belum ada pesan atau permohonan yang dikirim.

Kesimpulan penelusuran: ada sumber kandidat yang lebih konkret untuk mengembangkan variabel, tetapi belum ada kolom observasi baru yang aman diklaim sebagai data Solo Raya 2020. Dataset, prediktor baseline dan hasil eksperimen dipertahankan.
