# Tugas build untuk coding agent

Bangun dan verifikasi eksperimen estimasi harga tanah rata-rata per m² tingkat kecamatan Solo Raya tahun 2020. Mulai dari kode dan CSV dalam folder ini. Deliverable utama adalah hasil eksperimen GWR yang dapat direproduksi untuk paper.

1. Jalankan tiga baseline sesuai README. Cocokkan MAE gabungan setelah dibulatkan ke rupiah dengan Linear 739.020, KNN 732.073 dan Decision Tree 756.462. Jika berbeda, periksa versi pustaka dan CSV.
2. Lengkapi data spasial. Prioritaskan layer kecamatan BIG pada README atau poligon administratif tepercaya yang memuat 127 kecamatan. Simpan URL, tanggal pengambilan, versi/tahun geometri, CRS, kolom identitas, dan padanan nama di data/SUMBER_KOORDINAT.md. Periksa kecocokan wilayah dengan 2020. Laporkan setiap pemekaran, perubahan batas, atau padanan ambigu. Jika data resmi tidak dapat diakses, cari sumber alternatif yang mendokumentasikan batas dan tahun; rekam keterbatasannya.
3. Ekspor wilayah Jawa Tengah sebagai GeoJSON WGS84. Jalankan siapkan_koordinat.py dengan nama kolom sebenarnya. Program menghitung satu titik di dalam gabungan poligon kecamatan. Periksa pada peta bahwa semua titik berada di kecamatan yang dimaksud. Jangan memasukkan angka koordinat tebakan.
4. Jalankan empat model pada tujuh lipatan luar kabupaten/kota yang sama. Standardisasi, pemilihan k, kedalaman, dan bandwidth hanya memakai bagian latih. Gunakan bobot Gaussian untuk GWR serta prediktor populasi dan fasilitas umum regional pada keempat model.
5. Verifikasi 127 kunci unik, 127 prediksi uji per model, tujuh blok per model, dan 28 baris hasil per wilayah. Hitung ulang MAE dan RMSE langsung dari prediksi. Jelaskan kasus ketika GWR gagal karena regresi lokal singular. Pertahankan catatan parameter dan keterbatasan yang ditemukan.
6. Serahkan berkas koordinat dengan sumber, tiga CSV keluaran, dan ringkasan hasil serta cara reproduksinya. Jika geometri masih belum terverifikasi, sampaikan wilayah yang belum cocok dan berikan hasil tiga baseline yang sudah tersedia. Laporkan MAE dan RMSE dalam Rp/m². Interpretasi hanya mencakup rata-rata kecamatan tahun 2020.

Pertanyaan paper: apakah kedekatan geografis membantu memperkirakan rata-rata harga tanah suatu kecamatan ketika seluruh kabupaten/kotanya dikeluarkan dari data latih?
