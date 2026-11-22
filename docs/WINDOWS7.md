# Apotek Pahala untuk Windows 7 (64-bit)

Paket ini menyediakan aplikasi desktop, backend, database aktual, dan PWA
mobile yang dapat dijalankan di **Windows 7 SP1 64-bit** tanpa memasang Python
atau Node.js.

## Artefak

| Berkas | Keterangan |
|---|---|
| `ApotekPahala-Setup-1.0.0-win7-x64.exe` | Installer Inno Setup |
| `ApotekPahala/` | Folder portabel siap jalan |
| `ApotekPahala-1.0.0-win7-x64-portable.zip` | Arsip portabel |
| `SHA256SUMS.txt` | Checksum SHA-256 hasil build terakhir |

Ukuran dan checksum tidak ditulis di dokumen ini agar tidak basi setelah
build ulang. Selalu periksa `SHA256SUMS.txt` di folder distribusi dan
verifikasi dengan:

```powershell
Get-FileHash .\ApotekPahala-Setup-1.0.0-win7-x64.exe -Algorithm SHA256
Get-FileHash .\ApotekPahala-1.0.0-win7-x64-portable.zip -Algorithm SHA256
```

## Persyaratan Windows 7

- Windows 7 **SP1 64-bit**.
- Pembaruan Windows yang disarankan:
  - KB2533623 (API set / DLL loading).
  - KB2999226 (Universal C Runtime).
  - KB4474419 dan KB4490628 (SHA-2 code signing).
  - KB4534310 (rollup terakhir, bila tersedia).
- Minimal 2 GB RAM dan 500 MB ruang disk.
- Koneksi jaringan lokal untuk membuka PWA dari ponsel.

Windows 7 32-bit **tidak didukung** oleh paket ini.

## Tampilan dan penskalaan

- Pada Windows dengan text scaling (misalnya 125%), Qt5 membaca
  `AppliedDPI` dan menetapkan `QT_SCALE_FACTOR` otomatis sebelum aplikasi
  dimulai. Tidak perlu mengatur variabel lingkungan secara manual.
- Jendela default memakai sekitar 1220×680 unit logis; pada skala 125%
  tampil sekitar 1525×850 piksel fisik. Tabel, dialog, dan sidebar
  mengikuti ukuran tersebut tanpa overflow horizontal.
- Tipografi desktop memakai teks dasar 15 px, judul halaman 28 px, KPI
  30 px, sel tabel 13 px, meta tabel 12 px, dan header tabel 13 px.
  Ikon aksi 16 px dirender 2x di dalam tombol 30 px agar tetap tajam.
- Seluruh tabel di delapan modul diuji pada viewport 924 px: tidak ada
  badge, tombol aksi, atau teks nama obat yang terpotong.

## Instalasi

1. Salin installer ke komputer target.
2. Klik dua kali installer.
3. Ikuti wizard, lalu selesaikan instalasi.
4. Jalankan **Apotek Pahala** dari Start Menu atau desktop.

Jika SmartScreen/keamanan Windows menanyakan izin, pilih **Allow/Yes**.

### Menjalankan versi portabel

1. Ekstrak `ApotekPahala-1.0.0-win7-x64-portable.zip`.
2. Buka folder hasil ekstrak.
3. Jalankan `ApotekPahala.exe`.

Jangan memindahkan hanya `ApotekPahala.exe`; seluruh folder `backend`, `app`,
dan `PySide2` harus tetap satu paket.

## Penggunaan pertama

1. Aplikasi desktop terbuka dan backend berjalan otomatis.
2. Tunggu pesan **"Server terhubung — 20 obat — database connected"**.
3. Masuk dengan akun bawaan:
   - Admin: `admin` / `admin123`
   - Petugas: `petugas` / `petugas123`
4. Ganti kata sandi melalui **Pengaturan → Keamanan**.
5. Periksa **Pengaturan → Database** untuk memastikan database aktif.

Data pengguna disimpan di:

```
%LOCALAPPDATA%\ApotekPahala\storage\apotek_pahala.db
```

Folder tersebut juga memuat unggahan import dan kunci JWT. Database yang
dibundel disalin ke lokasi ini hanya jika belum ada, sehingga data pengguna
tidak tertimpa saat aplikasi diperbarui.

## PWA mobile dari perangkat lain

1. Pastikan ponsel dan komputer berada di jaringan yang sama.
2. Cari alamat LAN komputer, misalnya `http://192.168.1.10:8000`.
3. Buka alamat tersebut di Chrome/Edge ponsel.
4. Pilih **Tambahkan ke layar utama**.

Backend mendengarkan `0.0.0.0:8000` pada paket desktop. Jika firewall Windows
meminta izin, izinkan akses untuk jaringan privat.

## Lokasi data dan troubleshooting

| Masalah | Pemeriksaan |
|---|---|
| Backend tidak mau start | Pastikan port 8000 tidak dipakai aplikasi lain; jalankan sebagai Administrator sekali untuk izin firewall. |
| Desktop "Backend tidak merespons" | Tunggu 10–20 detik; periksa `%LOCALAPPDATA%\ApotekPahala\storage\` dan log backend. |
| Data lama masih muncul | Hapus/rename folder `%LOCALAPPDATA%\ApotekPahala` **setelah backup**, lalu jalankan ulang. |
| Tampilan terpotong | Gunakan resolusi minimal 1280×720; desktop mendukung scroll. |
| PWA tidak terbuka dari ponsel | Periksa alamat LAN, firewall, dan pastikan kedua perangkat satu jaringan. |
| Installer diblokir | Pastikan pembaruan SHA-2 sudah terpasang; klik **More info → Run anyway** bila perlu. |
| Database rusak | Restore dari backup melalui **Pengaturan → Database** (Admin). |

## Membangun ulang paket

### Prasyarat build

- Windows 10/11 untuk mesin build.
- Python 3.8.10 **x64** dengan `packaging/requirements-win7.txt`.
- Python modern (3.14) dengan `libcst` untuk `prepare_win7.py`.
- Node.js 20+ untuk build mobile.
- Inno Setup 6.2.2 (opsional; tanpa ini hanya folder portabel yang dibuat).

### 1. Siapkan environment build Python 3.8

```powershell
py -3.8 -m venv C:\build\win7venv
C:\build\win7venv\Scripts\python.exe -m pip install -r packaging\requirements-win7.txt
```

### 2. Build

```powershell
$env:APOTEK_PY38 = "C:\build\win7venv\Scripts\python.exe"
$env:APOTEK_ISCC = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
powershell -ExecutionPolicy Bypass -File packaging\build_win7.ps1
```

Hasil:

- `build\win7\ApotekPahala\` — folder portabel.
- `build\win7\ApotekPahala-1.0.0-win7-x64-portable.zip`.
- `build\win7\installer\ApotekPahala-Setup-1.0.0-win7-x64.exe`.
- `build\win7\SHA256SUMS.txt`.

Build script akan:

1. Menyalin source ke staging.
2. Menjalankan `prepare_win7.py` untuk kompatibilitas Python 3.8/PySide2.
3. Membundel `datasets/real/` dan database aktual.
4. Membangun executable desktop dan backend dengan PyInstaller.
5. Membuat ZIP portabel dan installer Inno Setup.

### Mengapa PySide2/Qt5 dan Python 3.8?

PySide6/Qt6 tidak mendukung Windows 7. PySide2 5.15 + Qt5 adalah kombinasi
terakhir yang masih berjalan di Windows 7 SP1 x64. Python 3.8.10 adalah versi
Python terakhir yang mendukung Windows 7.

## Validasi dan batasan

Yang diperiksa sebelum paket dirilis:

- Ekstraksi ZIP portabel.
- Menjalankan `ApotekPahala.exe` dan health check backend.
- Login Admin/Petugas.
- Pembukaan PWA dan API dari luar aplikasi desktop.
- Instalasi dan uninstall installer.
- Checksum SHA-256.
- Verifikasi final 22 November 2026: EXE dengan profil bersih, delapan
  modul, penskalaan 125%, ekstraksi ZIP, instalasi, dan uninstall.

Keterbatasan:

- Tidak ada mesin Windows 7 fisik pada lingkungan pengembangan; validasi OS
  akhir perlu dilakukan di komputer target.
- Build 64-bit tidak mendukung Windows 7 32-bit.
- Data cuaca memakai lokasi acuan Bandung; ganti bila apotek berada di kota lain.
- Hasil prediksi adalah estimasi, bukan kepastian.
