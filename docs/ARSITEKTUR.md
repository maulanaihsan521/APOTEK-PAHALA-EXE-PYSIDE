# Arsitektur Sistem - Apotek Pahala

Dokumen ini menjelaskan arsitektur, alur data, skema database, pipeline model,
dan keputusan teknis aplikasi Apotek Pahala.

## 1. Gambaran Umum

Apotek Pahala memakai satu backend sebagai sumber kebenaran data. Desktop dan
mobile web tidak menyimpan database sendiri; keduanya memanggil API yang sama.

```
┌────────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│ Desktop PySide6    │ ──────────────────────► │ FastAPI                  │
│ 8 modul            │ ◄────────────────────── │ JWT + SQLAlchemy         │
└────────────────────┘                         │                          │
┌────────────────────┐        HTTP/JSON        │ SQLite (storage/)        │
│ Mobile PWA React   │ ──────────────────────► │ 20 obat, 4.478 baris    │
│ Beranda/Prediksi/  │ ◄────────────────────── │ permintaan, 1.727 cuaca  │
│ Stok/Lainnya       │                         └──────────────────────────┘
└────────────────────┘
```

- **Backend** menyajikan REST API dan hasil build PWA.
- **Desktop** memakai `QThreadPool` agar panggilan API tidak memblokir UI.
- **Mobile** memakai API client yang sama dan service worker untuk shell PWA.
- **Database** SQLite berada di `storage/apotek_pahala.db`. Pada paket Windows,
  data disalin ke `%LOCALAPPDATA%\ApotekPahala\storage\apotek_pahala.db`.

## 2. Struktur Backend

```
backend/app/
├── api/             # endpoint FastAPI per domain
├── core/            # konfigurasi, keamanan, util, tema desktop
├── database/        # engine, session, migrasi ringan
├── ml/              # trainer, service prediksi, fitur
├── models/          # model SQLAlchemy
├── seed/            # importer data aktual + ekspor CSV
├── services/        # dashboard, laporan, pengadaan, inventori
└── main.py          # aplikasi FastAPI + startup seeding
```

Startup backend:

1. Membuat tabel yang belum ada dan menjalankan `ensure_schema()`.
2. Jika tabel `medicines` kosong, membaca `datasets/real/` dan menjalankan
   seeding + pelatihan model.
3. Jika dataset tidak tersedia, database dibiarkan kosong dan error dicatat.
   Tidak ada fallback ke data demonstrasi.

## 3. Skema Database

| Tabel | Isi utama |
|---|---|
| `roles` | Admin, Petugas |
| `users` | Akun, hash password, role, preferensi tema |
| `medicines` | 20 obat, kode, nama, kategori, satuan, harga jual, harga pokok, stok minimum, safety stock, prioritas |
| `inventory` | Stok sistem, stok fisik, tanggal opname terakhir |
| `inventory_movements` | Riwayat penyesuaian/import stok |
| `sales` | Baris permintaan mingguan hasil estimasi (sumber `stok_opname`) |
| `weather_data` | Cuaca harian NASA POWER untuk lokasi acuan |
| `prediction_runs` | Satu run pelatihan/prakiraan per obat dan horizon |
| `prediction_results` | Deret prakiraan, batas bawah/atas |
| `model_evaluations` | MAE/RMSE/WAPE/MAPE per obat dan algoritma |
| `procurement_recommendations` | Header rekomendasi pengadaan |
| `procurement_items` | Item, stok, prediksi, safety stock, jumlah final, subtotal |
| `application_settings` | Pengaturan model, pengadaan, tampilan |
| `notifications`, `activity_logs` | Notifikasi dan jejak aktivitas |
| `import_batches` | Riwayat import wizard |

Catatan penting:

- `sales` menyimpan **estimasi permintaan mingguan**, bukan transaksi kasir.
  Nilai `source` adalah `stok_opname` untuk data hasil impor aktual.
- `ST_PC` adalah ukuran stok utama; `ST_PHISIC` dipakai sebagai fallback saat
  interval menghasilkan permintaan negatif.
- Baris dengan kode obat dan tanggal yang sama digabung sebelum disimpan.

## 4. Autentikasi dan Otorisasi

- Login memakai OAuth2 password form; password di-hash PBKDF2.
- Token JWT berlaku 12 jam dan disimpan di client.
- Role diperiksa di server melalui dependency `require_admin`/`get_current_user`.
- Admin: master data, pengguna, import, persetujuan pengadaan, pengaturan model,
  backup/restore.
- Petugas: operasi harian dan pembacaan data; tidak dapat mengubah pengaturan
  model atau menyetujui pengadaan.

## 5. Pipeline Machine Learning

### 5.1 Fitur

- Lag permintaan 1–4 dan 52 pekan.
- Rata-rata bergulir 4/8/12 pekan dan simpangan baku.
- Pekan ISO, bulan, dan pola musiman sinus/cosinus.
- Suhu rata-rata, curah hujan, dan kelembapan harian yang diagregasi mingguan.

### 5.2 Pelatihan dan evaluasi

- Data diurutkan kronologis; data uji adalah bagian akhir (default 20%).
- Tiga model dilatih: Random Forest, Decision Tree, dan Linear Regression.
- Mode `auto` memilih model dengan WAPE uji terendah **per obat**.
- Metrik disimpan: MAE, RMSE, WAPE, MAPE, jumlah data uji.
- WAPE = total |aktual − prediksi| / total aktual × 100%. WAPE dipakai sebagai
  ukuran utama karena tetap bermakna saat permintaan mingguan rendah.
- MAPE hanya menghitung pekan dengan aktual > 0; pekan nol dicatat pada
  `mape_zero_actual`.

Parameter default:

| Parameter | Nilai |
|---|---|
| `primary_model` | `auto` |
| `n_estimators` | 300 |
| `max_depth` | 4 |
| `min_samples_leaf` | 3 |
| `test_ratio` | 0,2 |
| `horizon_weeks` | 4 |

### 5.3 Prakiraan

- Prakiraan dibuat rekursif untuk horizon 1–12 pekan.
- Awal prakiraan otomatis adalah Senin setelah tanggal data terakhir. Semua
  obat memakai awal yang sama agar dashboard, laporan, dan pengadaan konsisten.
- Batas ketidakpastian dihitung dari residual model.
- Hasil disimpan sehingga tidak perlu menghitung ulang setiap kali halaman
  dibuka.

### 5.4 Pengadaan

```
kebutuhan        = prakiraan permintaan selama lead time + safety stock
rekomendasi      = max(0, kebutuhan − stok fisik)
jumlah final     = pembulatan ke atas sesuai rounding_unit
subtotal         = jumlah final × harga pokok (median ST_COST)
```

Nilai `ST_COST` dipakai bila tersedia; bila tidak, dipakai harga jual. Angka
adalah usulan yang harus ditinjau manajemen.

## 6. Alur Desktop

- `AppShell` menangani navigasi 8 modul, notifikasi, timer refresh, dan tema.
- Setiap halaman memanggil API melalui `ApiClient` di thread terpisah.
- Grafik QPainter menggambar tren, bar, donat, dan garis; label panjang
  dibungkus maksimal dua baris dan dielipsis bila perlu.
- Halaman Pengaturan memiliki tab Profil, Tampilan, Model, Pengadaan,
  Database, dan Pengguna (Admin).

## 7. Alur Mobile Web

- React Router dengan hash route agar aman saat dibuka dari file/back-end.
- `AuthContext` menyimpan token dan menerapkan tema terang/gelap/otomatis.
- Halaman utama: Beranda, Prediksi, Penjualan, Cuaca, Stok, Pengadaan,
  Laporan, Lainnya, Pengaturan, Aktivitas.
- Kontrol Admin disembunyikan untuk Petugas **dan** endpoint tetap dilindungi
  di server.
- Service worker menyimpan shell; data tetap memerlukan koneksi ke backend.

## 8. API Utama

| Area | Endpoint |
|---|---|
| Auth | `POST /api/auth/login`, `GET /api/auth/me` |
| Dashboard | `GET /api/dashboard/overview` |
| Obat | `GET/POST/PUT/DELETE /api/medicines` |
| Penjualan | `GET /api/sales`, `POST/PUT/DELETE`, `GET /api/sales/export` |
| Cuaca | `GET /api/weather`, `GET /api/weather/summary`, `GET /api/weather/export` |
| Stok | `GET /api/inventory`, `POST /api/inventory/{id}/adjust`, `GET /api/inventory/export` |
| Prediksi | `POST /api/predictions/run`, `GET /api/predictions/latest`, `GET /api/predictions/series`, `POST /api/predictions/train-all` |
| Pengadaan | `GET /api/procurement/latest`, `POST /api/procurement/generate`, `POST /{id}/approve`, `GET /{id}/export` |
| Laporan | `GET /api/reports/types`, `/range`, `/summary`, `/export` |
| Pengaturan | `GET/PUT /api/settings`, backup/restore, pengguna |
| Import | `GET /api/imports/template/{type}`, `POST /preview`, `POST /commit` |

## 9. Ekspor dan Berkas

- PDF dibuat dengan ReportLab; tabel panjang dipotong 80 baris dan diberi
  catatan agar pembaca tahu bahwa Excel memuat data lengkap.
- Excel dibuat dengan OpenPyXL; CSV memakai UTF-8 BOM agar terbaca benar di
  Excel Indonesia.
- Semua ekspor mencantumkan periode, label data aktual, dan catatan metode.
- Nama berkas menyertakan jenis laporan dan tanggal.

## 10. Backup, Restore, dan Reset

- Backup membuat salinan SQLite konsisten melalui API `sqlite3.backup`.
- Restore memvalidasi ekstensi, ukuran, integritas SQLite, dan tabel wajib
  (`users`, `medicines`, `sales`). Backup otomatis dibuat sebelum menimpa.
- Reset data aktual: `python -m app.seed.real_data --reset` dari folder
  `backend`. Perintah ini membaca `datasets/real/`, bukan data demo.

## 11. Keputusan Teknis Penting

1. **Satu database untuk dua antarmuka.** Desktop dan mobile selalu melihat
   angka yang sama.
2. **Data aktual sebagai sumber kebenaran.** Tidak ada data demo atau angka
   rekaan di alur aktif.
3. **Permintaan adalah estimasi.** Tidak ada tabel kasir pada sumber; metode
   estimasi didokumentasikan dan ditampilkan di UI.
4. **WAPE sebagai metrik utama.** MAPE tetap disimpan sebagai pembanding.
5. **Model otomatis per obat.** Satu model tidak selalu terbaik untuk semua
   pola permintaan.
6. **Jendela prakiraan global.** Semua obat mulai pada tanggal yang sama agar
   rekomendasi pengadaan dapat dibandingkan.
7. **Windows 7 x64 memakai PySide2/Qt5 + Python 3.8** karena PySide6/Qt6 tidak
   mendukung Windows 7.
