# Hosting atlas pada GitHub Pages

Situs statis berasal dari `web/landpredict`. Workflow `.github/workflows/pages.yml` memeriksa aset, kecocokan dataset dan sintaks JavaScript, lalu mengunggah hanya folder tersebut. Paper, PDF lampiran, raster mentah dan bagian repository lain tidak masuk artefak situs.

URL tujuan standar: https://sqiftree.github.io/LandPredict/ (baru aktif setelah deployment berhasil).

Aktivasi awal oleh administrator repository jika belum aktif:

1. Buka https://github.com/sqiftree/LandPredict/settings/pages.
2. Pada **Build and deployment → Source**, pilih **GitHub Actions**.
3. Buka https://github.com/sqiftree/LandPredict/actions/workflows/pages.yml lalu **Run workflow** pada `main`, atau jalankan ulang workflow yang gagal sebelum aktivasi.

Sesudah aktif, perubahan pada folder peta di `main` memicu deployment otomatis. Workflow juga dapat dijalankan manual. Tidak memerlukan token pribadi atau secret tambahan; izin deployment menggunakan `GITHUB_TOKEN` dan OIDC bawaan Actions. Token bawaan tersebut tidak dapat mengaktifkan Pages pertama kali; pengaturan awal tetap memerlukan akses administrasi Pages.

Semua URL aset dan permintaan GeoJSON relatif, sehingga mendukung subpath `/LandPredict/`. Peta dasar OSM opsional memerlukan internet; poligon dan Leaflet disertakan dalam situs. GitHub Pages ini ditujukan sebagai situs publik. Situs privat terdahulu tidak otomatis dihapus.

Untuk memperbarui data, jalankan pipeline pengolahan, salin empat keluaran dari `data/processed` ke `web/landpredict`, lalu jalankan:

```bash
python3 scripts/check_web_export.py
node --check web/landpredict/app.js
```

Dokumentasi GitHub: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages.
