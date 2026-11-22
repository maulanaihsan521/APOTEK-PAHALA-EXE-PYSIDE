# Apotek Pahala — Pharmacy Intelligence

Aplikasi capstone analitik persediaan obat untuk **Apotek Pahala**. Proyek ini
menggabungkan satu backend FastAPI + SQLite dengan dua antarmuka yang memakai
database yang sama:

- **Desktop** (PySide6) — dashboard analitik lengkap dengan 8 modul.
- **Mobile web** (React + TypeScript + Tailwind, PWA) — antarmuka responsif
  untuk Beranda, Prediksi, Stok, dan modul lainnya.

> **Sumber data:** folder `DATA APOTEK PAHALA` berisi 1.085 berkas stok opname
> dan 2.894 berkas pembelian. Folder tersebut **tidak memiliki tabel transaksi
> kasir**. Karena itu angka "permintaan" pada aplikasi adalah estimasi yang
> dihitung dari perubahan stok opname ditambah pembelian bersih, bukan
> penjualan harian mentah. Metode lengkapnya dijelaskan di bagian
> [Model Prediksi](#model-prediksi).

---

## Fitur Utama

| Modul | Desktop | Mobile | Keterangan |
|---|---|---|---|
| Ringkasan Dashboard | ✅ | ✅ | KPI, tren permintaan, prakiraan, stok kritis, aktivitas |
| Prediksi Permintaan | ✅ | ✅ | Pemilihan model otomatis per obat, evaluasi kronologis, ekspor |
| Data Penjualan | ✅ | ✅ | Riwayat estimasi permintaan, filter, ekspor |
| Data Cuaca | ✅ | ✅ | Suhu, curah hujan, kelembapan harian, ekspor |
| Manajemen Stok | ✅ | ✅ | Stock opname, penyesuaian, riwayat pergerakan |
| Rekomendasi Pengadaan | ✅ | ✅ | Formula transparan, edit jumlah, approve/cancel |
| Laporan | ✅ | ✅ | PDF, Excel, CSV untuk 6 jenis laporan |
| Pengaturan | ✅ | ✅ | Profil, model, pengadaan, tampilan, backup/restore, pengguna |

Fitur lintas aplikasi:

- Login JWT dengan dua peran: **Admin** dan **Petugas**.
- Tema terang/gelap/otomatis dan skala font (desktop).
- Import wizard CSV/Excel dengan pemetaan kolom dan validasi.
- Notifikasi dan jejak aktivitas.
- Backup dan restore database (Admin).
- PWA: manifest, service worker, dapat dipasang di layar utama; shell tetap
  terbuka saat offline, sedangkan data API memerlukan koneksi.
- Label **DATA AKTUAL** pada dashboard, laporan, dan ekspor.

---

## Akun Bawaan

| Peran | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Petugas | `petugas` | `petugas123` |

> Ganti kata sandi bawaan melalui **Pengaturan → Keamanan** setelah login
> pertama, terutama jika aplikasi dipakai di jaringan kantor.

Hak akses utama:

- **Admin:** seluruh fitur, termasuk master obat/cuaca, pengguna, import,
  persetujuan pengadaan, pengaturan model, backup/restore.
- **Petugas:** dashboard, prediksi, penjualan, cuaca (baca), stok, membuat draf
  pengadaan, laporan, dan profil sendiri.

---

## Teknologi

- **Backend:** Python 3.14 pada lingkungan pengembangan, FastAPI, SQLAlchemy 2,
  SQLite, PyJWT, pandas, NumPy, scikit-learn, ReportLab, OpenPyXL.
- **Desktop:** PySide6 6.12 pada lingkungan pengembangan; paket Windows 7
  memakai PySide2 5.15/Qt5 dan Python 3.8.10.
- **Mobile:** React 19, TypeScript, Vite 7, Tailwind CSS, Recharts, Lucide.
- **Model:** Random Forest Regression, Decision Tree Regression, dan Linear
  Regression. Mode `auto` melatih ketiganya lalu memilih model dengan **WAPE
  data uji terendah** untuk setiap obat. Evaluasi memakai pemisahan kronologis
  (tanpa pengacakan).

---

## Struktur Proyek

```
CAPSTON PITON/
├── backend/
│   ├── app/                 # API, model ORM, layanan ML, importer data aktual
│   ├── tests/               # pengujian integrasi API
│   ├── run.py               # entrypoint uvicorn
│   └── requirements.txt
├── desktop/
│   ├── app/                 # jendela, halaman, komponen, tema
│   ├── run.py               # entrypoint desktop
│   └── requirements.txt
├── mobile-web/
│   ├── src/                 # halaman, komponen, API client
│   ├── public/              # manifest, service worker, ikon PWA
│   └── dist/                # hasil build, disajikan backend
├── datasets/
│   ├── real/                # CSV data aktual + metadata.json
│   └── template_*.csv       # template import
├── models/                  # artefak model (bila ada)
├── storage/                 # database SQLite, upload, secret
├── backups/                 # backup database
├── docs/                    # arsitektur, panduan pengguna, pengujian, Windows 7
├── packaging/               # build installer Windows 7 (PySide2/PyInstaller/Inno)
├── scripts/                 # utilitas aset
├── run_backend.bat
├── run_desktop.bat
├── run_mobile.bat
└── build_mobile.bat
```

---

## Menjalankan Aplikasi (Windows)

### 1. Prasyarat

- Python 3.11+ (proyek diuji dengan Python 3.14).
- Node.js 20+ dan npm.
- Windows 10/11 untuk pengembangan.

### 2. Pasang dependensi

```bat
python -m pip install -r requirements.txt
cd mobile-web
npm install
```

### 3. Jalankan backend

```bat
run_backend.bat
```

Atau manual:

```bat
cd backend
python run.py --host 0.0.0.0 --port 8000
```

- API: <http://127.0.0.1:8000/api>
- Dokumentasi API (Swagger): <http://127.0.0.1:8000/api/docs>
- Health check: <http://127.0.0.1:8000/health>
- Mobile hasil build: <http://127.0.0.1:8000/>

Saat database kosong, backend otomatis membaca `datasets/real/`, menyiapkan
20 obat, 4.478 baris permintaan mingguan, 1.727 hari cuaca, lalu melatih model
dan membuat rekomendasi awal. Proses pertama dapat memakan waktu beberapa
menit. Aplikasi tidak memiliki fallback ke data demonstrasi: bila dataset
aktual tidak ditemukan, database dibiarkan kosong dan error dicatat di log.

### 4. Jalankan desktop

```bat
run_desktop.bat
```

Desktop akan mendeteksi backend di `http://127.0.0.1:8000`. Jika belum berjalan,
desktop mencoba menjalankan `backend/run.py` secara otomatis dan menunggu
health check. Alamat server juga dapat diubah dari halaman login.

### 5. Jalankan mobile (mode pengembangan)

```bat
run_mobile.bat
```

Buka <http://localhost:5173>. Vite memproksikan `/api` ke backend port 8000.
Untuk mencoba dari ponsel di jaringan yang sama, gunakan alamat LAN yang
ditampilkan Vite, misalnya `http://192.168.x.x:5173`.

### 6. Build mobile untuk produksi

```bat
build_mobile.bat
```

Hasil build masuk ke `mobile-web/dist` dan langsung disajikan backend di
<http://127.0.0.1:8000/>. Tidak perlu menjalankan Vite pada mode ini.

### 7. Paket native Windows 7

Tersedia paket installer dan portabel 64-bit yang membundel desktop (PySide2/
Qt5), backend, database aktual, dan PWA. Paket dibuat untuk **Windows 7 SP1
64-bit** tanpa perlu Python/Node.js di komputer target.

- Installer: `build/win7/installer/ApotekPahala-Setup-1.0.0-win7-x64.exe`
- Portabel: `build/win7/ApotekPahala/` atau
  `build/win7/ApotekPahala-1.0.0-win7-x64-portable.zip`
- Checksum: `build/win7/SHA256SUMS.txt`

Panduan lengkap, persyaratan pembaruan Windows 7, lokasi data, troubleshooting,
dan cara membangun ulang ada di
[`docs/WINDOWS7.md`](docs/WINDOWS7.md).

Build ulang:

```powershell
$env:APOTEK_PY38 = "C:\path\ke\python38\Scripts\python.exe"
$env:APOTEK_ISCC = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
powershell -ExecutionPolicy Bypass -File packaging\build_win7.ps1
```

---

## Menyiapkan Ulang Data Aktual

Hentikan backend terlebih dahulu, lalu dari folder `backend`:

```bat
python -m app.seed.real_data --reset
```

Perintah ini membaca ulang `datasets/real/` (bukan folder DBF sumber),
menghapus database aktif, membuat akun, menyimpan data, melatih seluruh model,
dan membuat rekomendasi awal. Gunakan `--skip-train` bila hanya ingin data
tanpa pelatihan. Untuk membaca ulang DBF sumber dan mengekspor CSV baru:

```bat
python -m app.seed.real_data --reset --refresh-cache
```

> Backup database yang sudah ada terlebih dahulu dari menu **Pengaturan →
> Database**, karena reset akan menimpa database aktif.

---

## Pengujian

```bat
cd backend
python -m pytest tests -q
```

Pemeriksaan tambahan yang sudah dijalankan pada data aktual:

- Login Admin/Petugas dan pembatasan endpoint Admin (403 untuk Petugas).
- Dashboard, prediksi, penjualan, cuaca, stok, pengadaan, laporan, dan
  pengaturan pada desktop 1366×728 dan ukuran minimum 1220×680.
- EXE Windows 7 pada penskalaan 125% (1525×850 fisik, dpr 1,25) dengan
  tabel Penjualan/Stok/Pengadaan/Prediksi/Laporan yang tidak terpotong.
- Tipografi desktop 15 px/13 px/12 px dan ikon aksi 16 px di tombol 30 px;
  delapan halaman diuji offscreen tanpa overflow horizontal dan tanpa
  badge/tombol terpotong.
- Mobile 390×844: seluruh halaman utama, mode terang dan gelap, tanpa scroll
  horizontal dan tanpa error konsol.
- Ekspor PDF/XLSX/CSV untuk laporan, penjualan, stok, cuaca, pengadaan, dan
  hasil prediksi.
- Backup, restore, dan import wizard (preview + commit duplikat).
- Pemeriksaan bahwa database dan API aktif tidak berisi label/data demo.

---

## Model Prediksi

Pipeline utama:

1. **Estimasi permintaan mingguan.** Untuk setiap interval antar stock opname:
   `permintaan = ST_PC(t1) + pembelian_bersih(t1..t2] − ST_PC(t2)`.
   Hasil dipecah merata ke hari interval. Bila negatif, dipakai `ST_PHISIC`;
   bila tetap negatif, interval dianggap hilang dan minggu yang tidak tercakup
   penuh diinterpolasi. Baris duplikat (kode + tanggal) digabung.
2. **Agregasi mingguan** dari estimasi harian, termasuk pekan tanpa transaksi.
3. **Fitur:** lag 1–4 dan 52 pekan, rata-rata bergulir 4/8/12 pekan,
   simpangan baku, pekan ISO, bulan, suhu, curah hujan, dan kelembapan.
4. **Pemisahan kronologis** data latih/uji (tanpa acak).
5. **Pelatihan tiga model** (Random Forest, Decision Tree, Linear Regression).
6. **Pemilihan otomatis** model dengan WAPE uji terendah per obat.
7. **Prakiraan rekursif** 1–12 pekan dengan batas ketidakpastian.
8. **Evaluasi** memakai MAE, RMSE, WAPE, dan MAPE. WAPE menjadi ukuran utama
   karena lebih stabil ketika permintaan mingguan rendah. MAPE hanya menghitung
   pekan dengan aktual > 0; jumlah pekan yang dilewati dicatat terpisah.

Model dilatih ulang saat pengguna menjalankan prediksi atau pelatihan massal.
Hasil dan metrik disimpan di database sehingga dashboard, laporan, dan
pengadaan memakai prakiraan yang sama. Semua prakiraan dimulai pada Senin
setelah tanggal data terakhir, sehingga setiap obat memakai jendela yang sama.

Parameter model (jumlah pohon, kedalaman, rasio uji, dan lainnya) dapat diubah
Admin di **Pengaturan → Model**. Default: `auto`, 300 pohon, kedalaman 4,
`min_samples_leaf=3`, rasio uji 0,2.

---

## Catatan Data Aktual

- **Obat:** 20 jenis, termasuk 6 obat prioritas:
  AMLODIPINE 5MG 30'S, VOLTADEX 50MG 50'S, DEXTEEM PLUS 100'S,
  AMLODIPINE 10MG 30'S, METFORMIN 500MG, METHYLPREDNISOLON 4MG.
- **Permintaan:** 4.478 baris mingguan, periode 10 Jan 2022 – 14 Sep 2026.
- **Cuaca:** 1.727 hari, 1 Jan 2022 – 23 Sep 2026, NASA POWER MERRA-2.
  Lokasi acuan **Bandung** (`-6.9175, 107.6191`); lokasi ini dapat diganti di
  data cuaca bila apotek berada di kota lain.
- **Harga:** harga jual dan harga pokok per tablet/kapsul dari data sumber.
  Estimasi biaya pengadaan memakai median `ST_COST`; bila tidak tersedia,
  dipakai harga jual.
- **Model terpilih (pelatihan terakhir):** Random Forest 14 obat,
  Linear Regression 5 obat, Decision Tree 1 obat.
- **WAPE 6 obat prioritas:** sekitar **10,19%** (akurasi indikatif 89,81%)
  pada dashboard 4 pekan terakhir.
- **WAPE seluruh 20 obat:** sekitar **12,38%**.
- **Rincian prioritas:** Amlodipine 10mg 13,42%; Amlodipine 5mg 8,08%;
  Dexteem Plus 10,03%; Metformin 10,98%; Methylprednisolon 12,97%;
  Voltadex 5,67%.

Angka di atas adalah evaluasi model pada data aktual yang tersedia, bukan
jaminan akurasi masa depan. Data historis dapat berubah bila stock opname
baru diimpor dan model dilatih ulang.

---

## Keamanan dan Operasional

- Password disimpan sebagai hash PBKDF2; token JWT berlaku 12 jam.
- Endpoint Admin dilindungi pemeriksaan peran di server, bukan hanya
  penyembunyian tombol di UI.
- Import, backup, dan restore hanya untuk Admin.
- Restore memvalidasi integritas file SQLite dan membuat backup otomatis
  sebelum menimpa database aktif. Setelah restore, pengguna harus login ulang.
- File upload dibatasi 15 MB dan hanya menerima CSV/XLS/XLSX.
- Jangan menyimpan `storage/secret.key` atau database produksi di repositori.

---

## Peta Kode dengan Graphify

Repositori ini terhubung ke **Graphify**. Peta kode (AST, tanpa data sensitif)
berada di `graphify-out/` dan dapat dipakai untuk menelusuri keterkaitan modul:

```bat
graphify query "bagaimana alur prediksi dari data penjualan?"
graphify god-nodes
graphify explain "run_prediction"
```

Buka `graphify-out/graph.html` untuk melihat graf interaktif, atau baca
`graphify-out/GRAPH_REPORT.md` untuk ringkasan komunitas dan koneksi penting.
Riwayat pekerjaan dan hasil verifikasi terbaru dicatat di
[`docs/WORK_LOG.md`](docs/WORK_LOG.md) dan ikut diindeks ke graf. Graf ini hanya memuat
kode sumber; dokumen, gambar, dan dataset mentah tidak diindeks agar hasilnya
deterministik dan tidak memuat data pasien.

## Dokumentasi Lanjutan

- [`docs/ARSITEKTUR.md`](docs/ARSITEKTUR.md) — arsitektur, alur data, skema DB,
  endpoint, dan pipeline ML.
- [`docs/PANDUAN_PENGGUNA.md`](docs/PANDUAN_PENGGUNA.md) — panduan langkah demi
  langkah untuk desktop dan mobile.
- [`docs/PENGUJIAN.md`](docs/PENGUJIAN.md) — cakupan dan hasil pengujian.
- [`docs/WINDOWS7.md`](docs/WINDOWS7.md) — paket dan instalasi Windows 7.
- [`docs/PANDUAN_FRAMEWORK_DAN_METODE_DATA.pdf`](docs/PANDUAN_FRAMEWORK_DAN_METODE_DATA.pdf)
  — penjelasan framework/library, fungsi tiap teknologi, serta metode input,
  pembersihan, validasi, feature engineering, dan evaluasi model.
  Sumber dokumen: [`scripts/generate_framework_pdf.py`](scripts/generate_framework_pdf.py).

---

## Lisensi dan Kredit

Proyek capstone Design Sistem Informasi, Universitas Telkom, 2026.
Data cuaca bersumber dari NASA POWER MERRA-2. Ikon antarmuka memakai
Lucide (ISC License).
