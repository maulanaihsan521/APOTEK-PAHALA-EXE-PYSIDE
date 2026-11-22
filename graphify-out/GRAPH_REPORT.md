# Graph Report - CAPSTON PITON  (2026-11-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1742 nodes · 5321 edges · 84 communities (40 shown, 44 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 593 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Mobile PWA App Shell
- Desktop Pages and Shared UI
- Settings and Backup API
- Desktop Utils and Stock Widgets
- Desktop Chart Components
- Desktop Sales, Reports, and Sale Dialog
- Desktop UI Primitives and Pages
- Export Documents Service
- Database Models and Test Fixtures
- Desktop Weather Loaders and Async Helpers
- Desktop Widgets
- Prediction ML Pipeline
- Prediction API and Service
- Sales and Dashboard API
- Desktop Dashboard Page
- Windows 7 Build Transform
- Procurement and Activity API
- Mobile Frontend Dependencies
- API Schemas and Authentication
- Backend Models and Core APIs
- Reports Export Service
- Desktop API Client
- Import Wizard API
- Backend Startup and Health
- TypeScript Config
- Real Dataset Importer and ML Training
- Desktop Theme
- User Guide Documentation
- Async Worker
- Windows 7 Documentation
- Architecture Documentation
- Asset Copy Scripts
- README and Project Overview
- Testing Documentation
- Community 87
- Work Log 2026-11-21
- Windows Run Guide
- Project Documentation Index
- Login Documentation
- Community 89

## God Nodes (most connected - your core abstractions)
1. `User` - 109 edges
2. `SettingsPage` - 63 edges
3. `ThemedButton` - 59 edges
4. `Medicine` - 57 edges
5. `StockPage` - 46 edges
6. `ProcurementPage` - 45 edges
7. `log_activity()` - 45 edges
8. `cn()` - 44 edges
9. `SalesPage` - 42 edges
10. `WeatherPage` - 40 edges

## Surprising Connections (you probably didn't know these)
- `6. Alur Desktop` --references--> `ApiClient`  [INFERRED]
  docs/ARSITEKTUR.md → desktop/app/core/api.py
- `3. Skema Database` --references--> `notifications()`  [INFERRED]
  docs/ARSITEKTUR.md → backend/app/api/activity.py
- `2. Struktur Backend` --references--> `ensure_schema()`  [INFERRED]
  docs/ARSITEKTUR.md → backend/app/database/database.py
- `4. Autentikasi dan Otorisasi` --references--> `get_current_user()`  [INFERRED]
  docs/ARSITEKTUR.md → backend/app/core/deps.py
- `4. Autentikasi dan Otorisasi` --references--> `require_admin()`  [INFERRED]
  docs/ARSITEKTUR.md → backend/app/core/deps.py

## Import Cycles
- None detected.

## Communities (84 total, 44 thin omitted)

### Community 0 - "Mobile PWA App Shell"
Cohesion: 0.05
Nodes (146): dependencies, lucide-react@^0.548.0, react@^19.1.0, react-dom@^19.1.0, recharts@^3.2.1, SHELL, App(), NotFound() (+138 more)

### Community 1 - "Database Models and Test Fixtures"
Cohesion: 0.11
Nodes (14): activities(), mark_all(), mark_read(), notifications(), get_current_user(), require_admin(), create_access_token(), decode_token() (+6 more)

### Community 4 - "Desktop Pages and Shared UI"
Cohesion: 0.07
Nodes (20): ConfirmDialog, PageBase, Badge, BrandMark, IconButton, refresh_style(), downloads_dir(), _device_ratio() (+12 more)

### Community 5 - "Desktop Chart Components"
Cohesion: 0.05
Nodes (13): BarChart, ChartBase, DonutChart, FeatureBars, _font(), ForecastChart, GroupedBarChart, MiniBars (+5 more)

### Community 6 - "Desktop UI Primitives and Pages"
Cohesion: 0.11
Nodes (13): Card, InlineBanner, SectionHeader, SegmentedControl, StatTile, Table, ThemedButton, icon_button() (+5 more)

### Community 8 - "Desktop Widgets"
Cohesion: 0.07
Nodes (7): EmptyState, hand_cursor(), ResponsiveCardRow, SearchInput, set_variant(), SoftCard, Spinner

### Community 9 - "Prediction API and Service"
Cohesion: 0.17
Nodes (24): comparison(), evaluation_summary(), export_prediction(), feature_importance(), history(), latest(), model_status(), predict() (+16 more)

### Community 10 - "Settings and Backup API"
Cohesion: 0.07
Nodes (45): app_info(), backup_database(), backups(), get_app_info(), get_settings(), list_backups(), restore_database(), update_display() (+37 more)

### Community 11 - "Mobile Frontend Dependencies"
Cohesion: 0.09
Nodes (28): @fontsource-variable/inter@^5.2.8, description, devDependencies, autoprefixer@^10.4.21, postcss@^8.5.6, tailwindcss@^3.4.17, @types/react@^19.1.0, @types/react-dom@^19.1.0 (+20 more)

### Community 12 - "Sales and Dashboard API"
Cohesion: 0.13
Nodes (16): overview(), create_sale(), delete_sale(), export_sales(), _filters(), get_sale(), list_sales(), sale_payload() (+8 more)

### Community 13 - "Backend Models and Core APIs"
Cohesion: 0.13
Nodes (17): adjust_stock(), export_inventory(), inventory_summary(), list_inventory(), list_movements(), medicine_history(), categories(), create_medicine() (+9 more)

### Community 14 - "Desktop Utils and Stock Widgets"
Cohesion: 0.07
Nodes (21): _as_date(), _as_datetime(), change_type_label(), compact_rupiah(), dict_get(), format_date(), format_date_long(), format_datetime() (+13 more)

### Community 15 - "Windows 7 Build Transform"
Cohesion: 0.12
Nodes (13): main(), _add_typing_import(), AnnotationTransformer, _convert_subscript_slice(), _convert_unions(), copy_tree(), _flatten_union(), main() (+5 more)

### Community 16 - "Export Documents Service"
Cohesion: 0.07
Nodes (16): data_range(), export(), summary(), types(), export_weather(), _bar_chart(), csv_response(), excel_response() (+8 more)

### Community 17 - "Real Dataset Importer and ML Training"
Cohesion: 0.26
Nodes (9): _create_medicines(), _create_messages(), _create_movements(), _create_sales(), _create_settings(), _create_users(), _create_weather(), seed_from_dataset() (+1 more)

### Community 22 - "Procurement and Activity API"
Cohesion: 0.18
Nodes (18): update_medicine(), approve(), cancel(), edit_item(), export_recommendation(), generate(), get_recommendation(), latest_recommendation() (+10 more)

### Community 23 - "Desktop API Client"
Cohesion: 0.17
Nodes (3): ApiClient, ApiError, _detail_message()

### Community 25 - "Prediction ML Pipeline"
Cohesion: 0.11
Nodes (14): add_calendar(), build_dataset(), climatic_weather(), DatasetBundle, _feature_row(), forecast_recursive(), InsufficientDataError, load_weather_weekly() (+6 more)

### Community 27 - "Desktop Dashboard Page"
Cohesion: 0.10
Nodes (7): IconBox, KpiCard, activity_icon(), ActivityDialog, DashboardPage, PeriodDialog, ItemDetailDialog

### Community 28 - "Import Wizard API"
Cohesion: 0.16
Nodes (12): commit_import(), download_template(), import_history(), _load_medicine_lookup(), preview_import(), _read_file(), _slug(), _suggest_mapping() (+4 more)

### Community 31 - "Backend Startup and Health"
Cohesion: 0.13
Nodes (6): ensure_schema(), health(), _lan_ip(), landing(), lifespan(), public_app_info()

### Community 33 - "Desktop Sales, Reports, and Sale Dialog"
Cohesion: 0.08
Nodes (15): ChangePasswordDialog, FormDialog, _label(), MedicineDialog, ProcurementEditDialog, _readonly_row(), SaleDialog, ServerDialog (+7 more)

### Community 34 - "Reports Export Service"
Cohesion: 0.11
Nodes (13): create_weather(), delete_weather(), list_weather(), update_weather(), weather_summary(), Base, WeatherData, auth() (+5 more)

### Community 36 - "TypeScript Config"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+9 more)

### Community 38 - "Desktop Weather Loaders and Async Helpers"
Cohesion: 0.07
Nodes (20): _load_secret(), aggregate_observations(), aggregate_purchases(), build_dataset(), dbf_date(), derive_weekly(), export_dataset(), _load_export() (+12 more)

### Community 39 - "Desktop Theme"
Cohesion: 0.15
Nodes (4): build_palette(), build_qss(), _ensure_theme_assets(), ThemeManager

### Community 40 - "User Guide Documentation"
Cohesion: 0.12
Nodes (16): 10. Import Data, 11. Backup dan Restore, 12. Notifikasi dan Aktivitas, 13. Pemasangan PWA (Mobile), 14. Pemecahan Masalah, 15. Batasan Data, 2. Ringkasan Dashboard, 3. Prediksi Permintaan (+8 more)

### Community 43 - "Async Worker"
Cohesion: 0.16
Nodes (3): AsyncRunner, Worker, WorkerSignals

### Community 44 - "Asset Copy Scripts"
Cohesion: 0.15
Nodes (7): here, missing, names, readNode(), root, sourceDir, targetDir

### Community 48 - "Work Log 2026-11-21"
Cohesion: 0.22
Nodes (9): 1. Dataset asli menggantikan data demo, 2026-11-21, 2. Model dan prediksi, 3. Perbaikan backend, 4. UI desktop, 5. UI mobile (PWA), 6. Dokumentasi, 7. Graphify (+1 more)

### Community 49 - "Login Documentation"
Cohesion: 0.50
Nodes (4): 1. Masuk dan Keluar, Akun bawaan, Desktop, Mobile

### Community 54 - "Windows 7 Documentation"
Cohesion: 0.13
Nodes (15): 1. Siapkan environment build Python 3.8, 2. Build, Apotek Pahala untuk Windows 7 (64-bit), Artefak, Instalasi, Lokasi data dan troubleshooting, Membangun ulang paket, Mengapa PySide2/Qt5 dan Python 3.8? (+7 more)

### Community 56 - "README and Project Overview"
Cohesion: 0.15
Nodes (13): Akun Bawaan, Apotek Pahala — Pharmacy Intelligence, Catatan Data Aktual, Dokumentasi Lanjutan, Fitur Utama, Keamanan dan Operasional, Lisensi dan Kredit, Menyiapkan Ulang Data Aktual (+5 more)

### Community 58 - "API Schemas and Authentication"
Cohesion: 0.14
Nodes (13): change_password(), login(), logout(), me(), user_payload(), create_user(), deactivate_user(), list_users() (+5 more)

### Community 59 - "Architecture Documentation"
Cohesion: 0.13
Nodes (15): 10. Backup, Restore, dan Reset, 11. Keputusan Teknis Penting, 1. Gambaran Umum, 2. Struktur Backend, 3. Skema Database, 5.1 Fitur, 5.2 Pelatihan dan evaluasi, 5.3 Prakiraan (+7 more)

### Community 79 - "Testing Documentation"
Cohesion: 0.18
Nodes (11): 1. Ringkasan Hasil, 2. Pengujian Backend, 3.1 Tinjauan tipografi dan ikon (22 November 2026), 3. Pengujian Desktop, 4. Pengujian Mobile, 5. Pengujian Data dan Model, 6. Regresi dan Perbaikan yang Diverifikasi, 7. Pengujian Paket Windows 7 SP1 x64 (+3 more)

### Community 81 - "Windows Run Guide"
Cohesion: 0.25
Nodes (8): 1. Prasyarat, 2. Pasang dependensi, 3. Jalankan backend, 4. Jalankan desktop, 5. Jalankan mobile (mode pengembangan), 6. Build mobile untuk produksi, 7. Paket native Windows 7, Menjalankan Aplikasi (Windows)

### Community 83 - "Project Documentation Index"
Cohesion: 0.25
Nodes (8): 1. Tinjauan desktop menyeluruh, 2026-11-22, 2. Keterbacaan dan tata letak, 3. Perbaikan bug, 4. Paket Windows 7, 5. Dokumentasi dan Graphify, 6. Tipografi, ikon aksi, dan QA tabel, 7. Validasi paket final

### Community 87 - "Work Log - Apotek Pahala"
Cohesion: 0.20
Nodes (4): Keterbatasan, Status akhir (2026-11-21), Verifikasi akhir, Work Log - Apotek Pahala

### Community 89 - "9. Pengaturan"
Cohesion: 0.50
Nodes (4): 9. Pengaturan, Desktop - tab, Mobile, Tema

## Knowledge Gaps
- **44 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Arsitektur Sistem - Apotek Pahala` connect `Architecture Documentation` to `Database Models and Test Fixtures`, `Work Log - Apotek Pahala`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Are the 85 inferred relationships involving `User` (e.g. with `activities()` and `mark_all()`) actually correct?**
  _`User` has 85 INFERRED edges - model-reasoned connections that need verification._
- **Should `Mobile PWA App Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.053663570691434466 - nodes in this community are weakly interconnected._
- **Why does `ApiClient` connect `Desktop API Client` to `Desktop Shell and Navigation`, `Desktop Pages and Shared UI`, `Desktop Main Window`, `.__init__`, `Architecture Documentation`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SettingsPage` (e.g. with `AppShell` and `ChangePasswordDialog`) actually correct?**
  _`SettingsPage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `Database Models and Test Fixtures` be split into smaller, more focused modules?**
  _Cohesion score 0.10545790934320073 - nodes in this community are weakly interconnected._
- **Why does `User` connect `API Schemas and Authentication` to `Database Models and Test Fixtures`, `Reports Export Service`, `Prediction API and Service`, `Settings and Backup API`, `Sales and Dashboard API`, `Backend Models and Core APIs`, `Export Documents Service`, `Real Dataset Importer and ML Training`, `Procurement and Activity API`, `Import Wizard API`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._