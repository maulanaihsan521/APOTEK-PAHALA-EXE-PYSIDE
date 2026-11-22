# Laporan Pengujian - Apotek Pahala

Dokumen ini merangkum pengujian yang dilakukan pada aplikasi dengan dataset
aktual Apotek Pahala.

## 1. Ringkasan Hasil

| Area | Hasil |
|---|---|
| Backend (pytest) | **17 passed** |
| API ekspor PDF/XLSX/CSV | Lulus untuk laporan, penjualan, stok, cuaca, pengadaan, prediksi |
| Backup dan restore | Lulus; restore membuat backup otomatis dan database dapat dipakai kembali |
| Import wizard | Preview dan commit duplikat lulus; data tidak berubah saat duplikat dilewati |
| Hak akses Admin/Petugas | Lulus; endpoint Admin mengembalikan 403 untuk Petugas |
| Desktop 8 modul | Lulus pada 1366×728 dan 1220×680; EXE 1525×850 fisik (dpr 1,25); tipografi 13 px dan ikon aksi 16 px tajam |
| Mobile 390×844 | Lulus pada mode terang dan gelap tanpa error konsol |
| Pemeriksaan data demo | Tidak ada label/nilai demo pada API, database, atau UI aktif |

## 2. Pengujian Backend

Perintah:

```bat
cd backend
python -m pytest tests -q
```

Hasil: **17 passed** (3,77 detik pada lingkungan pengembangan).

Cakupan pengujian otomatis:

- Login valid/tidak valid, profil, dan perubahan kata sandi.
- Dashboard, daftar obat, penjualan, cuaca, inventori, prediksi, pengadaan,
  laporan, pengaturan, notifikasi, dan aktivitas.
- Pembatasan endpoint Admin.
- Header keamanan dan CORS.
- Ekspor berkas.
- Import preview/commit.
- Backup/restore.

### Pengujian API tambahan

| Skenario | Hasil |
|---|---|
| `GET /health` | 200, database terhubung, 20 obat |
| `GET /api/reports/range` | 2022-01-10 s.d. 2026-09-14 |
| Laporan penjualan PDF | 25.107 byte, diawali `%PDF` |
| Laporan prediksi XLSX | 7.619 byte, diawali `PK` |
| Laporan evaluasi CSV | 4.269 byte, UTF-8 BOM |
| Ekspor penjualan XLSX | 187.014 byte |
| Ekspor stok CSV | 1.816 byte |
| Ekspor cuaca XLSX | 58.126 byte |
| Ekspor pengadaan PDF/XLSX | 26.644 / 7.641 byte |
| Ekspor prediksi PDF/XLSX/CSV | 23.606 / 6.547 / 201 byte |
| Backup database | 8,26 MB, tercatat di daftar backup |
| Restore database | 200, health check dan login berhasil setelah restore |
| Import preview | 1 baris valid, tanpa kolom wajib yang hilang |
| Import commit duplikat | 0 baris masuk, 1 baris dilewati |
| Petugas membuka `/inventory` | 200 |
| Petugas mengubah model | 403 |
| Petugas membuka backup | 403 |
| Petugas menyetujui pengadaan | 403 |

## 3. Pengujian Desktop

Lingkungan sumber: PySide6, jendela 1366×728 dan ukuran minimum 1220×680
(viewport 1070×632 dan 924×604). Lingkungan paket: PySide2/Qt5 pada
penskalaan Windows 125%, jendela 1525×850 fisik (sekitar 1220×680 unit
logis, dpr 1,25).

Halaman yang diperiksa:

1. Ringkasan
2. Prediksi Permintaan
3. Data Penjualan
4. Data Cuaca
5. Manajemen Stok
6. Rekomendasi Pengadaan
7. Laporan
8. Pengaturan (tab Profil, Tampilan, Model, Pengadaan, Database, Pengguna)

Yang diverifikasi:

- Login Admin dan Petugas, termasuk tema terang dan gelap.
- Navigasi seluruh modul dan pemuatan data dari API.
- Tidak ada overflow horizontal pada 1366×728 maupun 1220×680, baik pada
  source PySide6 maupun EXE PySide2.
- Nama obat, ID catatan, tanggal prakiraan, dan metrik model tampil utuh pada
  lebar minimum; label yang sangat panjang memakai elipsis dan tooltip.
- Grafik laporan menampilkan nama obat lengkap dalam dua baris (tidak lagi
  terpotong menjadi 18 karakter).
- Tabel prediksi menampilkan status evaluasi dan model yang dipilih otomatis.
- Tabel Penjualan memakai 7 kolom: tanggal dan ID transaksi dalam satu sel
  dua baris; tombol ubah/hapus tetap berfungsi.
- Tabel Stok memakai 7 kolom: kategori tampil di baris meta obat
  (`kode · satuan · kategori`) sehingga tidak ada kolom sempit terpisah.
- Header Pengadaan (Stok, Prediksi, Aman, Usulan, Final, Subtotal, Urgensi)
  tampil utuh; tombol aksi berada pada baris terpisah.
- Tabel perbandingan prediksi memakai label RF/DT/LR, kolom MAE/RMSE/WAPE
  cukup lebar, dan legenda model dijelaskan pada catatan.
- Kartu periode Laporan dan Riwayat Pengadaan tidak terpotong.
- Logo sidebar, hero login, title bar, ikon jendela, dan header PDF tampil
  penuh pada source maupun EXE.
- Qt5 membaca `AppliedDPI` dan menetapkan `QT_SCALE_FACTOR` otomatis;
  tampilan EXE identik dengan source pada penskalaan 125%.
- Pengadaan menampilkan periode prakiraan yang sama untuk semua item.
- Ekspor PDF/Excel/CSV dari halaman laporan dan modul terkait.
- Dialog menyesuaikan tinggi layar; dialog obat 560×597 dan wizard impor
  820×640 muat pada layar 728 px.
- Alur GUI 26/26 lulus dan pengujian dialog/ekspor 18/18 lulus.
- Database dipulihkan ke kondisi awal setelah pengujian (20 obat, 4.478 baris
  permintaan, 1.727 hari cuaca, tanpa data demo).

### 3.1 Tinjauan tipografi dan ikon (22 November 2026)

- Ditemukan 24 deklarasi `font-size` pada QSS yang tidak valid (`$fspx`).
  Qt mengabaikannya dan memakai 11 pt bawaan, sehingga tabel terasa sempit.
  Token diperbaiki menjadi `${fs...}px`; ukuran yang sekarang aktif:
  teks dasar 15 px, judul halaman 28 px, KPI 30 px, sel tabel 13 px,
  meta tabel 12 px, dan header tabel 13 px.
- Ikon aksi pensil/hapus/riwayat/detail dirender dari SVG 2x lalu
  ditempatkan 16 px di dalam tombol 30 px, sehingga tidak lagi tampak
  buram pada penskalaan 125%.
- Kolom tabel diukur ulang pada viewport 824 px: Penjualan
  `[190, 214, 73, 72, 91, 106, 78]`, Stok
  `[214, 105, 89, 67, 91, 118, 140]`, Cuaca
  `[309, 95, 110, 110, 115, 85]`. Badge **Stok opname** (90 px) muat di
  kolom 106 px; empat tombol Stok (123 px) muat di kolom 140 px.
- Nama obat terpanjang `NA.DIKLOFENAK 50MG 50'S` (172 px) muat di kolom
  nama Penjualan (181 px isi); nama stok 173 px muat di 190 px.
- Kolom `Pekan` pada Rincian Prakiraan tidak lagi menampilkan `Peka...`;
  item bold kini mengikuti ukuran sel 13 px.
- Header `Tanggal` (Cuaca) dan kolom pertama Laporan rata kiri; hierarki
  nama/meta pada tabel Ringkasan disamakan (13 px/600 dan 12 px).
- Legenda grafik Tren/Backtest tidak lagi menimpa label sumbu X.
- QA offscreen `content.grab()` pada PySide2/Qt5, jendela 1220×680 logis
  (dpr 1,25), delapan halaman: lebar konten = viewport (924 px),
  `hmax=0` pada semua tabel, tidak ada badge/tombol terpotong, dan tidak
  ada scroll horizontal.
- `python -m compileall -q desktop\app desktop\run.py` lulus;
  `python -m pytest tests -q` -> **17 passed**.

## 4. Pengujian Mobile

Lingkungan: Chromium mobile emulation, viewport 390×844, perangkat sentuh,
locale `id-ID`.

Halaman yang diperiksa:

- Login, Beranda, Prediksi, Penjualan, Cuaca, Stok, Pengadaan, Laporan,
  Lainnya, Pengaturan, Aktivitas.

Hasil:

- Tidak ada scroll horizontal (`scrollWidth = 390`).
- Tidak ada error halaman/konsol.
- Mode terang: seluruh halaman terbaca, badge sumber **Stok opname** muncul.
- Mode gelap: judul halaman, tooltip grafik, badge status, kartu ringkasan,
  dan tabel model memiliki kontras yang memadai.
- Kontrol Admin muncul untuk Admin: parameter model, asumsi pengadaan,
  penyesuaian stok, persetujuan pengadaan, backup/restore.
- Kontrol Admin tidak muncul untuk Petugas.
- Laporan memakai rentang data aktual; default 30 hari terakhir dan tombol
  **Semua** memakai tanggal paling awal.

## 5. Pengujian Data dan Model

Dataset aktif:

| Item | Jumlah |
|---|---|
| Obat | 20 |
| Baris permintaan mingguan | 4.478 |
| Hari cuaca | 1.727 |
| Total unit permintaan | 1.864.312 |
| Periode permintaan | 2022-01-10 – 2026-09-14 |
| Periode cuaca | 2022-01-01 – 2026-09-23 |

Model terpilih:

| Model | Jumlah obat |
|---|---|
| Random Forest Regression | 14 |
| Linear Regression | 5 |
| Decision Tree Regression | 1 |

Metrik 6 obat prioritas (model utama):

| Obat | WAPE |
|---|---|
| AMLODIPINE 10MG 30'S | 13,42% |
| AMLODIPINE 5MG 30'S | 8,08% |
| DEXTEEM PLUS 100'S | 10,03% |
| METFORMIN 500MG | 10,98% |
| METHYLPREDNISOLON 4MG | 12,97% |
| VOLTADEX 50MG 50'S | 5,67% |
| **Rata-rata** | **10,19%** |

Akurasi indikatif dashboard = 100 − WAPE = **89,81%** untuk 6 obat prioritas.
Rata-rata WAPE seluruh 20 obat pada laporan prediksi = **12,38%**.

Catatan: angka ini adalah evaluasi pada data historis yang tersedia, bukan
jaminan akurasi masa depan.

## 6. Regresi dan Perbaikan yang Diverifikasi

- **Label laporan terpotong.** `reports_service.py` memotong nama obat menjadi
  18 karakter; kini nama lengkap dikirim dan grafik desktop membungkusnya.
- **Header mobile tidak terbaca di mode gelap.** Overlay `bg-canvas/90` belum
  memiliki aturan gelap; ditambahkan bersama warna teks yang sesuai.
- **Tooltip grafik putih di mode gelap.** Tooltip diubah memakai latar gelap.
- **Baris model terpilih tidak terbaca.** Latar `#F4FBF8` dan `#F0FAF6` kini
  memiliki varian gelap.
- **Badge status terlalu terang.** Warna pastel dan teksnya disesuaikan untuk
  mode gelap.
- **Kartu pengaturan Admin tidak muncul.** Pengecekan role dibuat
  case-insensitive (`role?.toLowerCase() === 'admin'`).
- **Laporan mobile kosong.** Ditambahkan endpoint `/api/reports/range` dan
  rentang default berbasis data aktual.
- **Istilah teknis di UI.** "Penjualan" pada konteks data turunan diganti
  "estimasi permintaan"; sumber `stok_opname` ditampilkan sebagai
  **Stok opname**.
- **Kotak insight dashboard di mode gelap.** Latar `bg-white/80` pada kartu
  prakiraan tetap terang dan membuat teks sulit dibaca. Ditambahkan override
  gelap untuk `bg-white/70`, `bg-white/80`, dan border `#D8EFE6`.
- **Label data demo di API.** Label kondisional `DEMO` di dashboard, laporan,
  dan status model dihapus; API kini selalu mengembalikan label **AKTUAL**.
- **Nama obat dan tanggal terpotong di ukuran minimum.** Lebar kolom tabel
  penjualan, stok, pengadaan, dan prediksi disesuaikan; label memakai elipsis
  dengan tooltip hanya bila ruang benar-benar habis.
- **Ikon SVG hilang.** Tujuh ikon yang dipakai halaman pengaturan, laporan,
  dan pengguna ditambahkan ke `desktop/app/assets/icons`.
- **Dialog keluar layar.** Tinggi dialog dibatasi otomatis dan isi formulir
  dapat digulir pada layar 728 px.

## 7. Pengujian Paket Windows 7 SP1 x64

Paket dibangun ulang pada 22 November 2026 dengan Python 3.8.10 x64,
PySide2 5.15/Qt5, PyInstaller 5.13.2, dan Inno Setup 6.2.2. Database yang
dibundel adalah database asli (20 obat, 4.478 baris permintaan, 1.727 hari
cuaca) tanpa jejak pengujian.

| Pemeriksaan | Hasil |
|---|---|
| Ekstraksi ZIP portabel | 1.297 berkas terekstrak, struktur lengkap |
| `backend/storage/apotek_pahala.db` | 20 obat, 4.478 penjualan, 1.727 cuaca, 0 demo |
| `secret.key` di paket | Tidak ada; kunci dibuat saat pertama jalan |
| Backend portabel `:8010` | Health OK, database connected, 20 obat, login Admin/Petugas |
| Desktop `ApotekPahala.exe` | Jendela terbuka, backend `:8000` health OK |
| Tampilan EXE 125% | 1525×850 fisik, dpr 1,25, tanpa overflow horizontal |
| Delapan modul di EXE | Lulus; tabel Penjualan/Stok/Pengadaan/Prediksi/Laporan utuh |
| Database EXE | 20 obat, 4.478 baris permintaan, 1.727 cuaca, 0 demo |
| Tampilan EXE vs source | Skala, navigasi, tabel, dan dialog konsisten |
| Installer senyap | Exit 0, 1.299 berkas terpasang |
| Aplikasi terpasang, profil bersih | Health `200`, database seed, login Admin |
| Uninstall senyap | Exit 0, folder aplikasi dan kunci registry terhapus |
| Data pengguna setelah uninstall | `%LOCALAPPDATA%\ApotekPahala` tetap ada |

Artefak:

| Berkas | Keterangan |
|---|---|
| `ApotekPahala-Setup-1.0.0-win7-x64.exe` | Installer Inno Setup |
| `ApotekPahala-1.0.0-win7-x64-portable.zip` | Arsip portabel |

Verifikasi final memakai profil `%LOCALAPPDATA%` bersih. EXE dijalankan dari
folder portabel final dan dari folder hasil installer; health backend `200`,
database seed tersalin, login Admin berhasil, dan delapan halaman dibuka
tanpa error. Spec backend tidak lagi membundel `secret.key`, sehingga kunci
JWT selalu dibuat baru di profil pengguna.

Ukuran dan checksum SHA-256 hasil build terakhir dicatat di
`build/win7/SHA256SUMS.txt`. Nilai tersebut tidak disalin ke dokumen ini agar
tidak basi setelah build ulang.

Catatan build: `Compress-Archive` sempat gagal dengan pesan
"user-mapped section open" saat membuat ZIP. Skrip build diganti memakai
`System.IO.Compression.ZipFile.CreateFromDirectory`, lalu ZIP dibuat ulang
dan diperiksa jumlah entri serta isinya.

## 8. Keterbatasan

- Tidak ada mesin/VM Windows 7 fisik untuk validasi akhir OS; pengujian
  dilakukan pada Windows 10/11 dan paket diperiksa secara statis serta
  dijalankan di lingkungan build.
- Sumber data tidak memiliki transaksi kasir; permintaan adalah estimasi.
- Lokasi cuaca default Bandung; curah hujan periode Jul–Sep 2026 sangat rendah
  menurut NASA POWER dan tidak dapat dikoreksi secara independen.
- Build 64-bit tidak mendukung Windows 7 32-bit.
- Hasil model dapat berubah setelah import data baru dan pelatihan ulang.
