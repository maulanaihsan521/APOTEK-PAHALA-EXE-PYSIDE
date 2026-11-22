# Work Log - Apotek Pahala

Catatan pekerjaan yang dihubungkan ke graf kode Graphify. Setiap perubahan
kode besar diikuti `graphify update .` agar peta di `graph.json` tetap sesuai
dengan source terbaru. Log ini tidak memuat data pasien maupun kredensial.

Update terakhir: **2026-11-23 23.00 WIB**

## 2026-11-23

### 1. Deep review Desktop lanjutan
- Review ulang keseluruhan `desktop/`: tidak ada bug High; Medium utama terselesaikan.
- `ActivityDialog` Dashboard dialihkan ke `AsyncRunner` (`refresh` via worker).
- Perbaikan lanjutan: guard `stock._adjust_selected`, async Save di dialog lain via runner, prevent stuck busy di weather.
- Verifikasi: compileall, import modul desktop, `pytest backend/tests -q` -> 17 passed, health backend OK.

## 2026-11-22

### 1. Tinjauan desktop menyeluruh
- Delapan modul diuji ulang dengan data asli: Ringkasan, Prediksi Permintaan,
  Data Penjualan, Data Cuaca, Manajemen Stok, Rekomendasi Pengadaan, Laporan,
  dan Pengaturan.
- Alur GUI **26/26 lulus**: login Admin/Petugas, navigasi, notifikasi,
  pengaturan, backup, tema, ukuran font, logout, dan pembatasan Petugas.
- Dialog dan ekspor **18/18 lulus**: master obat, catatan permintaan,
  penyesuaian stok, cuaca, pengguna, edit pengadaan, serta ekspor CSV untuk
  enam jenis data.
- Database dikembalikan ke kondisi awal setelah pengujian: 20 obat,
  4.478 baris permintaan, 1.727 hari cuaca, 2 pengguna, tanpa data demo.

### 2. Keterbacaan dan tata letak
- Skala tampilan desktop dinaikkan sekitar 8-10%: font QSS, ukuran jendela,
  sidebar, topbar, kartu, dan tinggi baris tabel.
- Jendela minimum kini 1220×680; seluruh halaman diuji pada viewport
  1070×632 dan 924×604 tanpa overflow horizontal.
- Kolom nama obat, ID catatan, tanggal prakiraan, dan metrik model tidak lagi
  terpotong di ukuran minimum. Label tabel memakai elipsis hanya bila perlu
  dan menyimpan nama lengkap di tooltip.
- Baris kartu KPI responsif: empat kartu pada layar lebar, dua kartu pada
  layar sempit. Laporan memakai enam kartu ringkasan.
- Aksi sekunder pada prediksi, penjualan, cuaca, stok, dan pengadaan
  digabung ke baris filter/judul agar tidak memakan ruang vertikal.
- Dialog menyesuaikan tinggi layar. Dialog obat 560x597, wizard impor
  820x640, dan seluruh dialog muat pada layar 728 px.
- Halaman login mengikuti tema terang/gelap, status server tetap terbaca,
  dan tipografi diperbesar.
- Baris teknologi pada Pengaturan menampilkan runtime sebenarnya
  (`Python ... - Qt ...`), sehingga source dan EXE sama-sama jujur.
- Skala Qt5 disamakan dengan Qt6: `desktop/run.py` membaca `AppliedDPI`
  (120 = 125%) dan menetapkan `QT_SCALE_FACTOR` sebelum `QApplication`.
  EXE tampil pada 1525×850 piksel fisik (sekitar 1220×680 unit logis,
  dpr 1,25), sama dengan source, tanpa memperkecil tabel.
- Sidebar memakai wadah merek bertinggi tetap dan metrik navigasi yang
  lebih ringkas. Logo tidak lagi terkompresi menjadi teks "Apotek";
  logo sidebar, hero login, title bar, ikon jendela, header PDF, dan
  ikon EXE/installer dipertahankan.
- Tabel dirapikan agar tidak ada header terpotong: Penjualan 7 kolom
  dengan tanggal dan ID transaksi dalam satu sel dua baris; Stok 7 kolom
  dengan kategori menyatu di baris meta obat; Pengadaan memindahkan
  tombol aksi ke baris kedua; Prediksi memakai label RF/DT/LR dan legenda;
  kolom metrik serta kartu periode Laporan mengikuti isi.

### 3. Perbaikan bug
- Tujuh ikon SVG yang hilang ditambahkan: `folder-open`, `palette`,
  `table-2`, `trophy`, `user-plus`, `user-x`, dan `users`.
- Status eksklusif tombol tema disinkronkan agar hanya satu pilihan aktif.
- Badge demo yang tersisa pada dashboard dihapus.
- Overflow filter/aksi Laporan dan lebar tabel minimum diperbaiki.
- Tooltip sel tabel ditambahkan agar teks panjang tetap dapat dibaca.

### 4. Paket Windows 7
- Paket final dibangun ulang setelah seluruh perbaikan UI dengan Python
  3.8.10 x64, PySide2 5.15/Qt5, PyInstaller 5.13.2, dan Inno Setup 6.2.2.
- Database yang dibundel adalah database asli tanpa jejak pengujian:
  20 obat, 4.478 baris permintaan, 1.727 hari cuaca, 2 pengguna, 0 data demo.
- EXE diuji dengan profil `%LOCALAPPDATA%` bersih: login Admin, delapan
  modul, tabel Penjualan/Stok/Pengadaan/Prediksi/Laporan, logo, dan health
  backend `200` dengan 20 obat. Jendela 1525×850 fisik pada skala 125%.
- ZIP portabel diuji lewat ekstraksi bersih (1.297 berkas) dan backend
  health di port 8010 dengan login Petugas. Installer diuji pasang senyap
  (1.299 berkas), aplikasi terpasang dijalankan pada profil bersih, lalu
  uninstall senyap; folder aplikasi dan kunci registry bersih, data pengguna
  tetap ada.
- Ukuran dan SHA-256 artefak final dicatat di
  `build/win7/SHA256SUMS.txt`.
- Spec backend dibatasi hanya membundel `apotek_pahala.db`. `secret.key`
  tidak pernah ikut dipaketkan; kunci JWT dibuat baru di
  `%LOCALAPPDATA%\ApotekPahala` saat aplikasi pertama dijalankan.

### 5. Dokumentasi dan Graphify
- `README.md`, `docs/PENGUJIAN.md`, `docs/WINDOWS7.md`, dan work log ini
  diperbarui dengan hasil akhir tinjauan, perbaikan DPI/tabel, dan
  verifikasi paket 22 November 2026.
- Graf Graphify diperbarui setelah perubahan kode dan dokumen. Jumlah
  node/edge terbaru tersedia di `graphify-out/GRAPH_REPORT.md`.

### 6. Tipografi, ikon aksi, dan QA tabel
- Ditemukan 24 deklarasi `font-size` QSS yang tidak valid (`$fspx`): Qt
  mengabaikan seluruh ukuran font dan memakai 11 pt bawaan. Token
  dikembalikan ke bentuk `${fs...}px`; ukuran kini benar-benar diterapkan:
  teks dasar 15 px, judul halaman 28 px, KPI 30 px, sel tabel 13 px,
  meta tabel 12 px, dan header tabel 13 px.
- Ikon aksi (pensil, hapus, riwayat, detail) dirender dari SVG pada 2x
  supersampling, lalu ditempatkan 16 px di dalam tombol 30 px. Hasilnya
  tajam pada penskalaan Windows 125%.
- Kolom tabel diseimbangkan ulang agar badge dan tombol tidak terpotong.
  Lebar terukur pada viewport tabel 824 px: Penjualan
  `[190, 214, 73, 72, 91, 106, 78]`, Stok
  `[214, 105, 89, 67, 91, 118, 140]`, dan Cuaca
  `[309, 95, 110, 110, 115, 85]`.
- Hierarki dua baris disamakan: nama obat 13 px/600 dan meta 12 px,
  termasuk tabel "Permintaan Tertinggi" di Ringkasan yang sebelumnya
  terbalik (nama 12 px, satuan 13 px).
- Header `Tanggal` pada Data Cuaca dan kolom pertama Laporan dibuat rata
  kiri mengikuti isi selnya.
- Kolom `Pekan` pada Rincian Prakiraan tidak lagi terpotong: item bold
  memakai ukuran sel 13 px, bukan 11 pt bawaan yang mengalahkan QSS.
- Legenda grafik Tren/Backtest diberi ruang vertikal sendiri sehingga tidak
  menimpa label sumbu X.
- QA offscreen PySide2 pada 1220x680 logis (dpr 1,25) untuk delapan
  halaman: lebar konten = viewport (924 px), `hmax=0` pada semua tabel,
  tidak ada badge/tombol terpotong, dan tidak ada scroll horizontal.
- `python -m compileall -q desktop\app desktop\run.py` lulus dan
  `python -m pytest tests -q` kembali **17 passed** setelah perubahan.

### 7. Validasi paket final
- Stage dibersihkan dari sisa QA: hanya `apotek_pahala.db` yang dibundel,
  tanpa `secret.key`, `-wal`, atau `-shm`.
- Spec backend dikunci agar `secret.key` tidak pernah ikut walaupun ada di
  folder stage.
- Backend portabel pada profil kosong menyalin database seed dan membuat
  `secret.key` baru; health `200`, 20 obat, login Admin dan Petugas lulus.
- EXE desktop dan aplikasi terpasang diuji dengan `%LOCALAPPDATA%` bersih:
  backend lokal siap, health `200`, dan login Admin lulus.
- ZIP 1.297 berkas, installer 1.299 berkas; uninstall exit 0, folder aplikasi
  dan kunci registry terhapus, data pengguna tidak dihapus.
- Ukuran dan hash SHA-256 final ada di `build/win7/SHA256SUMS.txt`.

### 8. Dokumentasi PDF framework dan metode data
- Menambahkan `docs/PANDUAN_FRAMEWORK_DAN_METODE_DATA.pdf` (16 halaman):
  penjelasan framework/library per lapisan, alur input DBF dan import wizard,
  aturan pembersihan/validasi, feature engineering, model, metrik, perintah
  reproduksi, batasan, glosarium, dan bukti validasi.
- Menambahkan generator `scripts/generate_framework_pdf.py` agar dokumen dapat
  dibangun ulang dari kode dan data aktual.
- PDF memakai font Segoe UI/Consolas, daftar isi otomatis, dan bookmark per
  bagian; tidak memuat token, secret, database produksi, atau data pasien.

### 8. Auto-update data cuaca BMKG Banjar
- Desktop `WeatherPage` menambahkan `QTimer` selama halaman Data Cuaca terbuka.
- Interval auto-update: **30 menit**; hanya Admin, dan tidak boleh ganda.
- Setiap timer tick memanggil **Backend → `POST /weather/bmkg/banjar`** untuk fetch+upsert BMKG Banjarnegara.
- Flag `_bmkg_busy` mencegah sesi BMKG melakukan overstacking; timer berhenti saat halaman tersembunyi.
- Terverifikasi: import Desktop OK, `compileall` OK, `pytest` 17 passed, relaunch Desktop berhasil.

## 2026-11-21

### 1. Dataset asli menggantikan data demo
- Sumber: folder `DATA APOTEK PAHALA` (DBF `ST` dan `BL`), bukan data sintetis.
- Importer `backend/app/seed/real_data.py` membaca DBF, menggabungkan baris
  kode/tanggal duplikat, dan menurunkan permintaan mingguan:
  `ST_PC(d1) + net BL_JML(d1..d2] - ST_PC(d2)`.
- Interval negatif dicoba ulang memakai `ST_PHISIC`; bila tetap negatif,
  dianggap hilang lalu diinterpolasi.
- Hasil ekspor: `datasets/real/obat.csv`, `permintaan_mingguan.csv`,
  `cuaca_harian.csv`, dan `metadata.json`.
- Database aktif berisi 20 obat, 4.478 baris permintaan, 1.727 hari cuaca,
  dan 2 pengguna. Tidak ada `is_demo=1`.

### 2. Model dan prediksi
- `primary_model = auto`: Random Forest, Decision Tree, dan Linear Regression
  dilatih; model dengan WAPE uji terendah dipilih per obat.
- RF disetel `max_depth=4`, `min_samples_leaf=3`.
- Semua prakiraan mulai Senin setelah tanggal penjualan terakhir:
  **2026-09-21**.
- Hasil: 14 Random Forest, 5 Linear Regression, 1 Decision Tree.
- WAPE 6 obat prioritas: 5,67%-13,42%; rata-rata 10,19% (akurasi indikatif
  89,81%). WAPE seluruh 20 obat 12,38%.
- Pengadaan `PRC-20261121-001`: 20 item, 35.652 unit, estimasi biaya
  15.108.197, periode 2026-09-21 s.d. 2026-10-18.

### 3. Perbaikan backend
- Label `DEMO` dihapus dari dashboard, laporan, prediksi, dan status model;
  API selalu mengembalikan `AKTUAL`.
- `reports/range` ditambahkan agar mobile memakai rentang data aktual.
- Nama obat pada grafik laporan tidak lagi dipotong 18 karakter.
- Biaya pengadaan memakai `ST_COST` (median) dengan fallback harga jual.
- Label aktivitas, ekspor, dan seeding diselaraskan dengan data asli.
- Fixture pytest dibersihkan dari flag demo; asersi dashboard diperbarui.

### 4. UI desktop
- 8 modul dipertahankan: Ringkasan, Prediksi Permintaan, Data Penjualan,
  Data Cuaca, Manajemen Stok, Rekomendasi Pengadaan, Laporan, Pengaturan.
- Istilah "penjualan" pada data turunan diganti "estimasi permintaan".
- Badge sumber `stok_opname` tampil sebagai **Stok opname**.
- Tabel prediksi menampilkan model terpilih dan tanggal prakiraan otomatis.
- Grafik laporan membungkus nama obat lengkap; periode pengadaan seragam.
- Pesan login, stok, dan pengaturan memakai bahasa awam.

### 5. UI mobile (PWA)
- Semua halaman memakai data backend yang sama; default laporan mengikuti
  `/api/reports/range`.
- Pemeriksaan role Admin dibuat case-insensitive.
- Mode gelap: override `bg-white/70`, `bg-white/80`, border `#D8EFE6`,
  tooltip grafik, dan badge status.
- Diuji pada 390x844: 10 halaman + modal stok, tanpa overflow horizontal
  dan tanpa error konsol. Build produksi `index-CFoZt4I6.css`.

### 6. Dokumentasi
- `README.md`, `docs/ARSITEKTUR.md`, `docs/PANDUAN_PENGGUNA.md`,
  `docs/PENGUJIAN.md`, dan `docs/WINDOWS7.md` memakai angka dataset asli,
  metode estimasi, hasil WAPE, dan alur build Windows 7.
- Peta Graphify dan Work Log ini ditautkan dari README.

### 7. Graphify
- Graf kode dibuat di `graphify-out/` (AST + dokumen, tanpa file sensitif):
  **1.704 node, 5.230 edge, 80 komunitas**.
- Work log ini (`docs/WORK_LOG.md`) ikut diindeks sebagai 13 node, sehingga
  riwayat pekerjaan terhubung ke graf.
- `graph.html` dan `GRAPH_REPORT.md` tersedia untuk navigasi. Label komunitas
  dirapikan dengan `graphify-out/relabel_step.py` karena pelabelan LLM tidak
  tersedia di lingkungan build.
- `secret.key`, dataset mentah DBF, dan file sensitif tidak diindeks.
- Perintah pembaruan: `graphify update .` lalu
  `graphify cluster-only . --no-label` dan `python graphify-out/relabel_step.py`.

### 8. Paket Windows 7 SP1 x64
- Build memakai Python 3.8.10 x64, PySide2, PyInstaller 5.13.2, dan
  Inno Setup 6.2.2.
- `secret.key` tidak dibundel; kunci JWT dibuat baru di
  `%LOCALAPPDATA%\ApotekPahala` saat pertama dijalankan.
- Database asli dibundel di `backend/storage/apotek_pahala.db` dan disalin
  hanya jika database pengguna belum ada.
- ZIP portabel dibuat ulang dengan `ZipFile.CreateFromDirectory` setelah
  `Compress-Archive` gagal karena file EXE/DLL terkunci.
- Verifikasi bersih: ekstrak ZIP 1.290 berkas, backend health OK, 20 obat,
  4.478 penjualan, 1.727 cuaca, 0 demo; desktop health OK pada port 8000.
- Installer: exit 0, 1.292 berkas, uninstall exit 0, folder aplikasi bersih,
  data pengguna di `%LOCALAPPDATA%` tetap ada.
- Dokumentasi di dalam paket mencakup README, panduan pengguna, arsitektur,
  pengujian, Windows 7, dan work log ini.
- Checksum SHA-256 tercatat di `build/win7/SHA256SUMS.txt`.

## Status akhir (2026-11-21)
- Paket siap distribusi: installer dan ZIP portabel berisi dataset asli.
- Checksum dan ukuran final ada di `build/win7/SHA256SUMS.txt`.
- Work log ini disertakan di dalam paket pada `docs/WORK_LOG.md`.
- Verifikasi paket dilakukan ulang setiap kali artefak dibangun ulang.

## Verifikasi akhir
- `python -m pytest tests -q` -> **17 passed**.
- API: login Admin/Petugas, ekspor PDF/XLSX/CSV, backup/restore, import
  preview/commit duplikat, dan pembatasan role Petugas -> lulus.
- Tidak ada label/nilai demo pada API, database, atau UI aktif.

## Keterbatasan
- Tidak ada transaksi kasir; permintaan adalah estimasi dari stok opname dan
  pembelian.
- Lokasi apotek belum diketahui; cuaca memakai acuan Bandung dan
  didokumentasikan terbuka.
- Tidak ada mesin/VM Windows 7 fisik untuk validasi akhir OS.
- Build x64 tidak mendukung Windows 7 32-bit.
