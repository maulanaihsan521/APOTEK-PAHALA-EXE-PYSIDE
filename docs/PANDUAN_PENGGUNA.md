# Panduan Pengguna - Apotek Pahala

Panduan ini ditujukan untuk Admin dan Petugas Apotek Pahala. Aplikasi tersedia
dalam dua bentuk yang memakai data yang sama:

- **Desktop** — tampilan lengkap untuk analisis dan pekerjaan administrasi.
- **Mobile web/PWA** — tampilan ringkas untuk ponsel atau tablet.

> Angka permintaan pada aplikasi adalah **estimasi** dari stock opname dan
> pembelian, karena data sumber tidak memiliki transaksi kasir. Baca catatan
> metode pada setiap halaman sebelum mengambil keputusan.

## 1. Masuk dan Keluar

### Desktop

1. Jalankan `ApotekPahala.exe` atau `run_desktop.bat`.
2. Periksa alamat server. Default: `http://127.0.0.1:8000`.
3. Masuk dengan akun yang diberikan Admin.
4. Gunakan tombol **Keluar** di pojok kanan atas untuk mengakhiri sesi.

### Mobile

1. Buka alamat server, misalnya `http://192.168.1.10:8000`.
2. Masukkan username dan kata sandi.
3. Aplikasi dapat dipasang ke layar utama melalui menu browser
   **Tambahkan ke layar utama**.

### Akun bawaan

| Peran | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Petugas | `petugas` | `petugas123` |

Ganti kata sandi bawaan setelah login pertama melalui **Pengaturan →
Keamanan**.

## 2. Ringkasan Dashboard

Dashboard menampilkan:

- **Estimasi nilai permintaan** pada periode terpilih.
- **Jumlah permintaan** dan perbandingan dengan periode sebelumnya.
- **Obat prioritas** yang dipantau model.
- **Akurasi prediksi** (100 − WAPE) untuk obat prioritas.
- Grafik tren aktual dan prediksi.
- Obat terlaris, status stok, dan aktivitas terbaru.

Pilih rentang 1, 2, atau 3 bulan. Tombol **Segarkan** memuat ulang data.
Badge **Data Aktual** menunjukkan bahwa angka berasal dari dataset apotek,
bukan data contoh.

## 3. Prediksi Permintaan

1. Pilih obat pada daftar.
2. Pilih algoritma:
   - **Otomatis (WAPE terkecil)** — disarankan; sistem memilih model terbaik
     untuk obat tersebut.
   - Random Forest, Decision Tree, atau Linear Regression — untuk membandingkan.
3. Pilih horizon 1–12 pekan.
4. Klik **Jalankan Prediksi**.

Hasil menampilkan total prakiraan, MAE, RMSE, WAPE, grafik per pekan, evaluasi
pada data uji, perbandingan algoritma, dan faktor yang paling berpengaruh.
Gunakan tombol **PDF**, **Excel**, atau **CSV** untuk mengunduh hasil.

Catatan:

- WAPE lebih rendah berarti lebih baik. WAPE dipakai karena lebih stabil saat
  permintaan mingguan rendah.
- MAPE hanya menghitung pekan dengan aktual > 0.
- Prakiraan adalah estimasi, bukan kepastian.

## 4. Data Penjualan / Permintaan

Halaman ini menampilkan riwayat **estimasi permintaan mingguan** per obat.

- Gunakan kotak pencarian untuk mencari nama atau kode obat.
- Gunakan **Rentang tanggal** untuk memfilter periode.
- Badge **Stok opname** menunjukkan sumber data.
- Admin dapat menambah catatan permintaan melalui tombol **Catat**.
- Gunakan **Excel** atau **CSV** untuk mengunduh data.

Angka rupiah dihitung dari harga jual terakhir pada master obat.

## 5. Data Cuaca

Halaman cuaca menampilkan suhu, curah hujan, dan kelembapan harian dari NASA
POWER MERRA-2.

- Lokasi acuan default: **Bandung** (`-6.9175, 107.6191`).
- Jika apotek berada di kota lain, ganti lokasi pada data cuaca agar konteks
  iklimnya sesuai.
- Grafik mingguan membantu melihat pola cuaca yang dipakai sebagai fitur model.
- Gunakan **Ekspor Excel/CSV** untuk mengunduh data.

Cuaca adalah faktor pendukung, bukan ramalan cuaca resmi.

## 6. Manajemen Stok

Ringkasan menunjukkan jumlah obat, total unit, stok fisik, stok sistem,
selisih, dan tanggal opname terakhir.

Status stok:

- **Aman** — di atas 1,5 × stok minimum.
- **Perlu perhatian** — di bawah 1,5 × stok minimum.
- **Kritis** — sama dengan atau di bawah stok minimum.

Admin dapat membuka detail obat lalu mengisi **Penyesuaian stok**. Simpan
perubahan; sistem mencatat riwayat pergerakan. Petugas hanya dapat melihat.

## 7. Rekomendasi Pengadaan

1. Buka menu **Rekomendasi Pengadaan**.
2. Periksa periode, lead time, dan safety stock.
3. Klik **Buat** untuk membuat draf baru, atau buka draf terbaru.
4. Tinjau setiap item: stok, kebutuhan, saran, jumlah final, dan urgensi.
5. Admin dapat mengubah jumlah final lalu menyetujui atau membatalkan draf.
6. Unduh PDF/Excel untuk dibawa ke rapat pengadaan.

Rumus: prakiraan kebutuhan + safety stock + kebutuhan lead time − stok fisik.
Angka adalah usulan, bukan pesanan otomatis.

## 8. Laporan

Tersedia enam jenis laporan:

1. Penjualan/permintaan
2. Permintaan
3. Prediksi
4. Evaluasi model
5. Stok
6. Pengadaan

Pilih jenis dan rentang tanggal, lalu unduh **PDF**, **Excel**, atau **CSV**.
Pada mobile, rentang awal mengikuti data yang tersedia dan default 30 hari
terakhir. Tombol **Semua** memakai tanggal paling awal data.

## 9. Pengaturan

### Desktop - tab

- **Profil** — nama, email, dan kata sandi.
- **Tampilan** — tema terang/gelap/otomatis dan skala font.
- **Model** — model utama, jumlah pohon, kedalaman, min sampel daun, rasio uji,
  horizon default (Admin).
- **Pengadaan** — lead time, safety stock, pembulatan, horizon default (Admin).
- **Database** — ukuran database, backup, restore (Admin).
- **Pengguna** — tambah/ubah/nonaktifkan akun (Admin).

### Mobile

Pengaturan mencakup profil, tema, parameter model dan pengadaan (Admin),
informasi database, backup/restore (Admin), serta daftar pengguna (Admin).

### Tema

Mode **Otomatis** mengikuti preferensi sistem. Tema juga diterapkan pada
aplikasi mobile.

## 10. Import Data

Import tersedia untuk Admin.

1. Buka **Pengaturan → Import** (desktop) atau menu import yang tersedia.
2. Pilih jenis data: obat, penjualan/permintaan, cuaca, atau stok.
3. Unduh template bila perlu.
4. Unggah CSV/XLS/XLSX.
5. Periksa pemetaan kolom dan pesan validasi.
6. Klik **Proses Import**.

Aturan penting:

- Format tanggal: `YYYY-MM-DD`.
- Kode obat harus sudah ada di master obat.
- Baris duplikat dilewati bila opsi **Lewati duplikat** aktif.
- Maksimal 50.000 baris dan 15 MB per berkas.

## 11. Backup dan Restore

### Backup

**Pengaturan → Database → Buat Backup**. Berkas `.db` tersimpan di folder
`backups/`.

### Restore

1. Pilih berkas `.db` yang valid.
2. Centang konfirmasi.
3. Klik **Restore**.

Sistem memvalidasi integritas database dan membuat backup otomatis sebelum
menimpa database aktif. Setelah restore, login ulang.

## 12. Notifikasi dan Aktivitas

- Ikon lonceng menampilkan notifikasi stok kritis, import, prediksi, dan
  pengadaan.
- Halaman **Aktivitas** mencatat login, perubahan stok, import, backup, dan
  tindakan penting lain.

## 13. Pemasangan PWA (Mobile)

1. Buka aplikasi di Chrome/Edge.
2. Buka menu browser.
3. Pilih **Install app / Tambahkan ke layar utama**.
4. Ikon Apotek Pahala muncul di layar utama.

Shell aplikasi tetap terbuka saat offline, tetapi data terbaru memerlukan
koneksi ke backend.

## 14. Pemecahan Masalah

| Masalah | Solusi |
|---|---|
| Login gagal | Periksa username/password dan koneksi ke backend. |
| Data tidak muncul | Klik **Segarkan**; pastikan backend berjalan. |
| Prediksi gagal | Pastikan data permintaan cukup dan model sudah dilatih. |
| Ekspor gagal | Periksa izin folder unduhan dan koneksi. |
| Halaman mobile terpotong | Perbesar/redupkan tampilan; gunakan mode potret. |
| Lupa password Admin | Pulihkan dari backup atau minta Admin lain mereset akun. |
| Backend tidak merespons | Jalankan ulang backend dan periksa port 8000. |

## 15. Batasan Data

- Sumber data tidak memiliki transaksi kasir; permintaan adalah estimasi dari
  stock opname dan pembelian.
- Lokasi cuaca default Bandung; ganti bila apotek berada di kota lain.
- Hasil prediksi bergantung pada kualitas dan kelengkapan stock opname.
- Angka akurasi adalah evaluasi pada data historis, bukan jaminan masa depan.
- Aplikasi bukan alat diagnosis medis dan tidak menggantikan keputusan apoteker.
