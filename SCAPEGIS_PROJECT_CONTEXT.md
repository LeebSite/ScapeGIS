# Konteks Project — ScapeGIS SaaS WebGIS & Spatial AI

> **Tujuan dokumen:** Memberikan konteks menyeluruh kepada AI coding assistant sebelum melakukan analisis, debugging, refactoring, atau pengembangan fitur ScapeGIS.
>
> **Instruksi utama:** Baca dokumen ini terlebih dahulu, kemudian periksa kode aktual pada repository GitHub sebelum memberikan solusi atau menulis kode. Dokumen ini adalah konteks proyek, bukan pengganti source code. Jika kondisi repository berbeda dari dokumen ini, prioritaskan source code aktual dan laporkan perbedaannya.

---

## 1. Latar Belakang

### 1.1 Identitas proyek

* **Nama proyek:** ScapeGIS
* **Jenis sistem:** SaaS (Software as a Service), WebGIS, dan AI-assisted spatial analysis.
* **Domain:** Geospatial Information System (GIS), spatial analytics, property development, dan artificial intelligence.
* **Status:** Development.
* **Target pengguna utama:** Developer properti, pengembang perumahan, pengelola proyek properti, serta pihak yang membutuhkan analisis lokasi untuk perencanaan pengembangan properti.
* **Lokasi pengembangan awal:** Pekanbaru, Riau, Indonesia.
* **Bahasa antarmuka yang direncanakan:** Bahasa Indonesia, dengan kemungkinan dukungan bahasa lain pada tahap selanjutnya.

ScapeGIS dikembangkan sebagai platform WebGIS berbasis langganan yang membantu pengembang properti memahami karakteristik suatu wilayah menggunakan data geospasial dan asisten AI.

### 1.2 Masalah yang ingin diselesaikan

Analisis lokasi untuk pengembangan properti memerlukan data spasial, perangkat GIS, pengetahuan teknis, dan proses analisis yang tidak selalu mudah dilakukan oleh pengguna non-GIS.

ScapeGIS bertujuan menyederhanakan proses tersebut melalui kombinasi:

1. Peta digital interaktif.
2. Dataset GIS yang dikelola oleh tim ScapeGIS.
3. Analisis spasial menggunakan PostGIS.
4. Asisten AI yang memahami pertanyaan terkait lokasi dan dapat memanggil fungsi analisis spasial.
5. Hasil analisis yang dapat ditelusuri kembali ke dataset dan layer sumbernya.

Contoh pertanyaan pengguna:

* Rumah sakit mana yang paling dekat dengan lokasi proyek?
* Berapa jarak lokasi proyek ke jalan arteri atau jalan utama?
* Fasilitas kesehatan apa saja yang berada dalam radius 3 kilometer?
* Apakah titik lokasi berada dalam area atau batas wilayah tertentu?
* Fasilitas apa saja yang berada di sekitar lokasi pengembangan?
* Bagaimana aksesibilitas suatu lokasi berdasarkan data jalan dan fasilitas publik yang tersedia?

AI harus menjawab berdasarkan data spasial yang tersedia dan hasil perhitungan sistem, bukan berdasarkan perkiraan model bahasa semata.

### 1.3 Nilai utama produk

**ScapeGIS = WebGIS + Spatial Analytics + AI Spatial Consultant.**

ScapeGIS bukan sekadar chatbot yang dapat menjelaskan GIS. Sistem harus mampu menghubungkan pertanyaan pengguna dengan data geospasial yang benar-benar tersedia, menjalankan analisis melalui backend, dan mengembalikan hasil yang dapat diverifikasi.

---

## 2. Konsep Produk dan Alur Pengguna

### 2.1 Peran pengguna

**Developer**

Pengguna utama yang berlangganan layanan ScapeGIS. Developer dapat membuat workspace dan proyek, menggunakan dataset yang telah diberikan aksesnya, melihat peta, serta bertanya kepada Spatial AI.

**Workspace Owner**

Developer yang membuat workspace dan memiliki peran owner dalam workspace tersebut. Owner mengelola workspace sesuai izin yang diberikan sistem.

**Workspace Member**

Anggota workspace yang memperoleh akses berdasarkan membership dan permission yang berlaku.

**Platform Admin**

Operator internal ScapeGIS yang mengelola pengguna, dataset GIS, akses dataset ke workspace, dan proses penyediaan data kepada pelanggan.

Admin platform berbeda dari workspace owner. Admin mengelola operasional platform, sedangkan owner mengelola workspace miliknya.

### 2.2 Alur bisnis utama

1. Pengguna mendaftar dan login.
2. Pengguna membuat workspace dan otomatis menjadi owner workspace tersebut.
3. Pengguna membuat proyek properti di dalam workspace.
4. Pengguna yang belum berlangganan memperoleh akses ke dataset demo Pekanbaru sesuai batasan paket Free.
5. Pengguna mengajukan subscription untuk wilayah kota/kabupaten yang dibutuhkan.
6. Tim ScapeGIS memproses atau menyiapkan dataset GIS melalui perangkat seperti QGIS.
7. Admin mengunggah atau mendaftarkan hasil dataset yang telah diproses dan memberikan akses kepada workspace yang berhak.
8. Developer memperoleh akses terhadap dataset sesuai subscription dan entitlement.
9. Developer menggunakan peta dan Spatial AI untuk melakukan analisis lokasi.
10. Sistem mencatat sumber data dan hasil tool yang mendukung jawaban AI.

**Penting:** Developer tidak mengunggah dataset GIS sendiri sebagai bagian dari alur bisnis utama yang direncanakan. Dataset disiapkan dan dikelola oleh tim ScapeGIS.

### 2.3 Rencana paket berlangganan

| Paket        | Kuota AI yang direncanakan | Akses GIS                                 |
| ------------ | -------------------------: | ----------------------------------------- |
| Free         |            10 prompt/bulan | Dataset demo Pekanbaru                    |
| Basic        |            50 prompt/bulan | Wilayah kota/kabupaten sesuai entitlement |
| Professional |           100 prompt/bulan | Wilayah kota/kabupaten sesuai entitlement |
| Enterprise   |           200 prompt/bulan | Wilayah kota/kabupaten sesuai entitlement |

Angka di atas merupakan rancangan produk yang telah dibahas. Jangan menganggap seluruh billing, quota enforcement, pembayaran, dan entitlement sudah selesai diimplementasikan. Periksa repository untuk mengetahui fitur yang benar-benar aktif.

---

## 3. Arsitektur dan Technology Stack

### 3.1 Gambaran arsitektur

ScapeGIS menggunakan arsitektur frontend dan backend yang terpisah dalam satu repository.

* **Frontend:** Next.js dan React dengan TypeScript.
* **Backend:** FastAPI berbasis Python.
* **Database:** PostgreSQL dengan ekstensi PostGIS.
* **ORM:** SQLAlchemy.
* **Database migration:** Alembic.
* **Spatial processing:** PostGIS dan layanan analisis spasial di backend.
* **AI provider:** Gemini API melalui abstraksi provider Spatial AI.
* **Cache dan supporting services:** Redis.
* **Object storage:** MinIO.
* **Containerization:** Docker dan Docker Compose.

Versi dependency, konfigurasi deployment, dan detail runtime harus diperiksa langsung melalui file manifest dan konfigurasi repository. Jangan menebak versi hanya berdasarkan dokumen ini.

### 3.2 Struktur repository

Struktur tingkat atas yang digunakan:

```text
ScapeGIS/
├── backend/
├── frontend/
└── docs/
```

Struktur di atas merupakan struktur utama yang diketahui. Periksa repository untuk mengetahui direktori dan file aktual di setiap bagian.

#### Backend

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/
│   ├── spatial/
│   ├── spatial_ai/
│   │   ├── providers/
│   │   ├── prompts/
│   │   └── tools/
├── tests/
├── alembic/
├── .env.example
└── ...
```

Pohon direktori tersebut merupakan peta konseptual dari struktur yang telah dibahas. Jangan mengasumsikan seluruh nama atau penempatan file persis sama tanpa memeriksa source code.

Tanggung jawab utama:

* `app/api/`: routing dan endpoint API.
* `app/core/`: konfigurasi, security, dan komponen inti aplikasi.
* `app/spatial/`: semantic GIS, akses dataset, serta analisis spasial.
* `app/spatial_ai/`: kontrak tool AI, context builder, provider, prompt, agent, dan integrasi Spatial AI.
* `tests/`: unit test, integration test, dan pengujian otorisasi.
* `alembic/`: migration schema database.
* `.env.example`: template konfigurasi environment tanpa secret aktif.

#### Frontend

Frontend menggunakan Next.js, React, dan TypeScript.

Tanggung jawab yang direncanakan:

* Authentication dan protected routes.
* Dashboard developer dan admin.
* Workspace dan project management.
* Subscription dan dataset access.
* Peta interaktif.
* Panel Spatial AI.
* Visualisasi hasil analisis dan map actions.
* Pengelolaan state dan integrasi API.

Struktur aktual frontend, library peta, state management, dan endpoint yang sudah terhubung harus diperiksa sebelum mengubah implementasi.

#### Dokumentasi

Direktori `docs/` digunakan untuk dokumentasi arsitektur dan keputusan teknis. Salah satu dokumen yang dilaporkan telah dibuat adalah:

`docs/SPATIAL_AI_ARCHITECTURE.md`

Dokumen ini menjelaskan batas antara LLM, controlled spatial tools, dan sumber data spasial.

---

## 4. Prinsip Arsitektur yang Tidak Boleh Dilanggar

### 4.1 PostGIS adalah sumber kebenaran spasial

LLM tidak boleh menjadi sumber utama fakta spasial.

* Jarak harus diperoleh dari perhitungan spasial.
* Fitur terdekat harus diperoleh melalui query spasial.
* Jumlah fasilitas harus berasal dari hasil query.
* Status containment harus diperoleh dari pengujian geometri.
* Batas wilayah harus berasal dari data geospasial yang tersedia.

AI boleh memahami bahasa alami, memilih tool yang sesuai, dan menjelaskan hasilnya. AI tidak boleh mengarang nilai jarak, jumlah objek, koordinat, atau batas wilayah.

### 4.2 LLM tidak boleh menjalankan arbitrary SQL

LLM tidak diperbolehkan menghasilkan dan mengeksekusi SQL bebas terhadap database.

Semua operasi spasial harus melewati controlled tools yang telah didefinisikan, divalidasi, dan dibatasi di backend.

Alur yang diharapkan:

```text
User Question
    ↓
Spatial AI Agent
    ↓
Tool Selection
    ↓
Validated Tool Arguments
    ↓
Spatial Tool Registry
    ↓
Authorization and Semantic Resolution
    ↓
Spatial Analysis Service
    ↓
PostGIS
    ↓
Structured Results and Provenance
    ↓
LLM Explanation
    ↓
Structured AI Response
```

### 4.3 Semantic GIS harus generik

AI tidak boleh mengandalkan nama layer yang di-hardcode untuk satu kota tertentu.

Sistem menggunakan semantic mapping untuk menghubungkan konsep pengguna dengan layer GIS yang tersedia, misalnya:

* hospital → rumah sakit
* health facility → fasilitas kesehatan
* arterial road → jalan arteri
* school → sekolah
* administrative boundary → batas administratif

Contoh tersebut hanya ilustrasi. Semantic mapping yang benar harus berasal dari konfigurasi layer, dataset, dan semantic service aktual.

Penambahan kota atau dataset baru seharusnya dilakukan melalui konfigurasi dan metadata yang sesuai, bukan dengan membuat ulang seluruh logic AI.

### 4.4 Tenant isolation dan authorization wajib

Setiap request yang mengakses workspace, project, dataset, atau layer harus memvalidasi hak akses pengguna.

Prinsip yang harus dipertahankan:

* Pengguna hanya mengakses workspace yang diizinkan.
* Project harus termasuk dalam workspace yang benar.
* Dataset harus diberikan akses melalui entitlement yang valid.
* Layer yang dipakai harus berasal dari dataset yang diizinkan.
* Admin privilege tidak boleh diberikan hanya karena frontend mengirimkan role tertentu.
* Validasi authorization harus dilakukan di backend.

Jangan menghapus atau melemahkan authorization hanya untuk membuat demo berhasil.

### 4.5 Data provenance harus dipertahankan

Hasil Spatial AI perlu dapat ditelusuri ke sumbernya.

Informasi provenance yang dirancang meliputi dataset, layer, kategori semantik, operasi spasial, dan jumlah hasil apabila relevan.

Jika data yang diperlukan tidak tersedia, agent harus menyampaikan keterbatasan tersebut, bukan membuat jawaban yang terdengar meyakinkan tetapi tidak memiliki dasar data.

---

## 5. Status Pengembangan per Modul

> Status berikut merupakan ringkasan berdasarkan laporan implementasi yang tersedia. Ini bukan audit langsung terhadap repository terbaru. Selalu verifikasi source code, migration, test, dan hasil runtime sebelum menyatakan fitur production-ready.

### Module 1 — Spatial Knowledge Foundation

**Status: Dilaporkan telah diimplementasikan.**

Komponen yang dilaporkan tersedia:

* Semantic GIS layer model dan tabel `gis_layer_semantics`.
* Semantic constants dan preset untuk dataset Pekanbaru.
* Semantic service untuk resolusi konsep GIS.
* Spatial analysis service.
* Spatial context builder.
* API untuk operasi spasial.
* Operasi nearest feature, radius search, containment, intersection, dan multi-domain context.
* Workspace/dataset authorization.
* Frontend `SpatialAnalysisPanel` untuk verifikasi analisis spasial.
* Pemilihan koordinat melalui interaksi peta.

Pengujian yang pernah dilaporkan:

* 25 spatial tests.
* Backend suite berjumlah 33 test pada tahap tersebut.

Angka tersebut adalah hasil historis yang dilaporkan. Jangan menganggapnya sebagai jumlah test terkini.

### Module 2A — Spatial AI Context and Tool Contract

**Status: Dilaporkan selesai dengan pengujian otomatis.**

File dan komponen yang dilaporkan dibuat:

* `backend/app/spatial_ai/exceptions.py`
* `backend/app/spatial_ai/schemas.py`
* `backend/app/spatial_ai/context.py`
* `backend/app/spatial_ai/tools/base.py`
* `backend/app/spatial_ai/tools/spatial_tools.py`
* `backend/app/spatial_ai/tool_registry.py`
* `backend/tests/test_spatial_ai_tools.py`
* `docs/SPATIAL_AI_ARCHITECTURE.md`

Kontrak utama:

* `SpatialProvenance`
* `ToolIntent`
* `MapAction`
* `SpatialFact`
* `SpatialAIResponse`

Lima controlled tools yang dilaporkan tersedia:

1. `get_spatial_context`
2. `find_nearest`
3. `search_radius`
4. `check_containment`
5. `find_intersections`

Kemampuan registry:

* Menemukan tool yang tersedia.
* Mengekspor tool definitions untuk provider AI.
* Memvalidasi argumen tool.
* Mendispatch tool ke implementasi backend.

Spatial AI context membatasi layer yang dapat digunakan berdasarkan `ai_enabled`, authorization, dataset, dan workspace.

Map actions yang didefinisikan mencakup:

* `show_layer`
* `hide_layer`
* `highlight_feature`
* `fit_bounds`
* `show_marker`
* `clear_highlight`

Pengujian yang dilaporkan ketika Module 2A selesai:

* 48 test untuk Spatial AI tools/context.
* Backend suite 81 test pada tahap tersebut, termasuk spatial tests dan GIS access tests.
* Working tree dilaporkan bersih.
* Branch yang dilaporkan: `feature/module-2a-spatial-ai-tools`.

Commit yang dilaporkan:

* `548afb3 docs(spatial-ai): document tool architecture and llm boundary`
* `7b0bd46 test(spatial-ai): add spatial ai tool and context tests`
* `ddfc525 feat(spatial-ai): add controlled spatial tool contracts`

Periksa Git history aktual sebelum menggunakan informasi commit tersebut sebagai bukti keadaan repository saat ini.

### Module 2B — Gemini Spatial Reasoning Agent

**Status: Implementasi dilaporkan telah dibuat, tetapi verifikasi integrasi nyata masih menjadi gate penting.**

Komponen yang dilaporkan:

* `backend/app/spatial_ai/providers/base.py`
* `backend/app/spatial_ai/providers/gemini_provider.py`
* `backend/app/spatial_ai/prompts/system_prompt.py`
* `backend/app/spatial_ai/agent.py`
* `backend/app/api/v1/endpoints/spatial_ai.py`
* `backend/tests/test_gemini_spatial_agent.py`
* Konfigurasi Gemini di `backend/app/core/config.py`
* Template environment di `backend/.env.example`
* Pembaruan dokumentasi arsitektur.

Fungsi yang dirancang:

* Abstraksi provider AI.
* Provider Gemini.
* Tool/function calling.
* Multi-tool reasoning loop.
* Validasi tool calls.
* Pembatasan jumlah pemanggilan tool.
* Pengubahan hasil tool menjadi fakta dan provenance.
* Penyusunan map actions.
* Endpoint analisis Spatial AI yang menggunakan authentication dan tenant authorization.

Endpoint yang dilaporkan:

`POST /api/v1/spatial-ai/analyze`

Konfigurasi yang dilaporkan diperkenalkan:

* `GEMINI_API_KEY`
* `GEMINI_MODEL`
* `GEMINI_TIMEOUT_SECONDS`
* `SPATIAL_AI_MAX_TOOL_CALLS`

**Hal yang wajib diverifikasi:**

1. Apakah SDK Gemini yang terpasang kompatibel dengan implementasi provider.
2. Apakah model yang dikonfigurasi benar-benar tersedia untuk API key dan endpoint yang digunakan.
3. Apakah format tool/function calling cocok dengan versi SDK aktual.
4. Apakah seluruh test suite berjalan pada repository terbaru.
5. Apakah request berhasil melewati Gemini, registry, spatial service, dan PostGIS.
6. Apakah hasil jawaban benar-benar menyertakan fakta dan provenance yang berasal dari hasil tool.
7. Apakah authorization dan tenant isolation tetap berlaku ketika request dikirim langsung ke API.
8. Apakah secret tidak muncul dalam log atau response error.

Nama model dan versi SDK dalam laporan implementasi belum dianggap terverifikasi hanya berdasarkan laporan tersebut.

Jika live smoke test belum dijalankan karena API key, database, dataset, atau model tidak tersedia, tandai sebagai `BLOCKED` atau `NOT RUN`, bukan `PASSED`.

### Module 2C — Spatial AI Chat API

**Status: Tahap berikutnya yang direncanakan; jangan menganggap sudah selesai.**

Fokus yang direncanakan adalah kontrak percakapan backend yang akan digunakan frontend.

Ruang lingkup yang perlu ditentukan setelah Module 2B lolos verifikasi:

* Kontrak request/response percakapan.
* Validasi input pengguna.
* Penanganan konteks workspace dan project.
* Batas history atau conversation context.
* Error handling yang konsisten.
* Authentication dan authorization.
* Batas penggunaan dan integrasi quota jika sesuai dengan arsitektur yang sudah ada.
* Integrasi dengan agent dan tool registry yang telah dibuat.

Jangan langsung mencampurkan seluruh implementasi frontend chat, streaming, persistent conversation storage, map UI, dan subscription billing dalam satu perubahan besar. Pecah menjadi modul terpisah sesuai kondisi repository.

### Modul berikutnya yang masih perlu dipetakan

Fitur-fitur berikut merupakan bagian dari arah produk atau pekerjaan yang perlu diaudit, bukan klaim bahwa semuanya telah selesai:

* Persistent AI conversations.
* Frontend AI chat panel.
* Integrasi AI dengan peta interaktif.
* Eksekusi dan rendering map actions di frontend.
* Dashboard developer dan admin yang terintegrasi penuh.
* Workflow administrasi dataset.
* Subscription dan entitlement enforcement end-to-end.
* Prompt quota enforcement.
* Logging, observability, dan audit trail.
* Production deployment dan security hardening.

---

## 6. Dataset dan Analisis Spasial

### 6.1 Dataset awal

Dataset awal yang digunakan dalam pengembangan adalah data GIS Pekanbaru.

Nama arsip yang pernah digunakan:

`pekanbaru_gis_v1.zip`

Dataset dilaporkan memiliki sekitar 40 layer. Angka dan daftar layer aktual harus dikonfirmasi dari file dataset atau database.

Sumber data spasial dapat berupa hasil pemrosesan QGIS dan format GIS seperti GeoJSON, Shapefile, CSV dengan koordinat, atau format lain yang didukung pipeline ingestion.

### 6.2 Prinsip pemrosesan data

* Dataset harus diregistrasikan melalui mekanisme backend yang sesuai.
* Metadata layer harus dapat dipetakan ke semantic categories.
* Layer yang tidak memiliki data atau semantic mapping yang sesuai tidak boleh diperlakukan sebagai fakta yang tersedia.
* Data geometry dan spatial reference harus divalidasi.
* Operasi jarak harus memperhatikan sistem koordinat dan satuan yang benar.
* Hasil analisis harus mencatat sumber data yang relevan.
* Akses dataset mengikuti workspace entitlement.
* Penambahan dataset baru tidak boleh memerlukan perubahan hardcoded pada agent.

### 6.3 Penanganan ketidaktersediaan data

AI harus membedakan antara:

* Tidak ditemukan hasil pada dataset yang tersedia.
* Dataset atau layer yang dibutuhkan tidak tersedia.
* Layer tersedia tetapi belum dapat digunakan oleh AI.
* Akses terhadap dataset tidak diberikan.
* Operasi gagal dijalankan.

Kondisi tersebut tidak boleh semuanya disederhanakan menjadi klaim bahwa objek atau fasilitas tidak ada di dunia nyata.

---

## 7. Cara Menjalankan dan Menguji

**Bagian ini wajib dikonfirmasi melalui repository aktual sebelum digunakan.** Perintah di bawah adalah pola umum yang dapat disesuaikan; bukan jaminan bahwa seluruh command persis sama dengan konfigurasi terkini.

### 7.1 Prasyarat

* Git.
* Python dan dependency backend sesuai versi proyek.
* Node.js dan package manager yang digunakan frontend.
* Docker dan Docker Compose.
* PostgreSQL dengan PostGIS, atau service database melalui Docker Compose.
* API key Gemini untuk pengujian provider live.
* Dataset GIS yang sesuai untuk integration testing.

### 7.2 Environment configuration

Gunakan `.env.example` sebagai referensi dan siapkan environment lokal sesuai konfigurasi proyek.

Variabel yang pernah diperkenalkan untuk Spatial AI:

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=your_verified_gemini_model
GEMINI_TIMEOUT_SECONDS=30
SPATIAL_AI_MAX_TOOL_CALLS=8
```

Nama model di atas sengaja menggunakan placeholder. Periksa konfigurasi dan kompatibilitas SDK/API aktual sebelum menentukan nilai.

Jangan memasukkan API key ke Git, source code, prompt yang dipublikasikan, screenshot, atau log.

### 7.3 Menjalankan backend

Periksa README dan Docker Compose terlebih dahulu.

Contoh pola command yang mungkin digunakan:

```bash
docker compose up -d
```

Jika repository menggunakan executable `docker-compose` versi lama, ikuti konvensi yang berlaku pada proyek.

Migration database menggunakan Alembic. Sebelum menjalankan migration, periksa konfigurasi database, status migration, dan apakah database berisi data yang harus dipertahankan.

Jangan menggunakan perintah yang menghapus volume database sebagai langkah debugging rutin.

### 7.4 Menjalankan frontend

Masuk ke direktori `frontend/`, periksa `package.json`, dan gunakan package manager yang dikunci oleh repository.

Pola umum:

```bash
npm install
npm run dev
```

Command aktual dapat berbeda jika proyek menggunakan `pnpm`, `yarn`, atau script lain.

### 7.5 Menjalankan test

Backend:

```bash
pytest
```

Frontend: periksa script yang tersedia pada `frontend/package.json` sebelum menjalankan test, lint, type check, atau build.

Sebelum menyatakan suatu modul selesai, laporkan:

* Command yang dijalankan.
* Jumlah test yang lulus dan gagal.
* Error yang masih ada.
* Apakah test menggunakan mock atau service nyata.
* Apakah database dan dataset nyata digunakan.
* Apakah live AI smoke test benar-benar dilakukan.

Test unit dengan mock tidak membuktikan bahwa Gemini API, PostGIS, dan keseluruhan integrasi bekerja di lingkungan nyata.

---

## 8. Aturan Main untuk AI Coding Assistant

### 8.1 Sebelum menulis kode

1. Baca dokumen konteks ini.
2. Periksa repository aktual dan branch aktif.
3. Identifikasi implementasi yang sudah ada.
4. Baca file yang berkaitan dengan tugas.
5. Periksa test dan migration terkait.
6. Jelaskan pendekatan implementasi secara singkat sebelum membuat perubahan yang luas.
7. Jangan mengulang implementasi yang sebenarnya sudah tersedia.

### 8.2 Batasan perubahan

Jangan mengubah atau menghapus komponen berikut tanpa alasan teknis yang jelas dan analisis dampak:

* Authentication dan authorization.
* Workspace membership dan tenant isolation.
* Dataset entitlement.
* Semantic GIS resolution.
* Controlled spatial tools dan tool registry.
* Spatial provenance.
* Pydantic request/response schemas.
* Database migration yang telah diterapkan.
* Environment configuration dan secret handling.
* Test yang melindungi behavior existing.

Jika perubahan pada komponen tersebut memang diperlukan, jelaskan alasannya, dampaknya, dan test yang diperlukan.

### 8.3 Konvensi arsitektur

* Ikuti struktur, naming, type hints, dan coding style yang sudah ada.
* Gunakan Pydantic schemas untuk validasi data pada batas API dan tool sesuai pola proyek.
* Gunakan service layer yang sudah ada, bukan menduplikasi spatial logic di endpoint.
* Gunakan SQLAlchemy dan pola database access yang sudah diterapkan.
* Gunakan Alembic untuk perubahan schema database.
* Jangan membuat migration baru untuk perubahan yang tidak memerlukan perubahan schema.
* Jangan mengubah kontrak API secara breaking tanpa menjelaskan dampaknya.
* Hindari duplikasi logic.
* Hindari dependency baru jika library yang tersedia sudah mencukupi.
* Tambahkan test untuk behavior baru dan regression risk.
* Jangan menyembunyikan exception penting dengan fallback yang menghasilkan jawaban palsu.
* Jangan menganggap test lulus jika belum benar-benar dijalankan.

### 8.4 Aturan khusus Spatial AI

* Jangan membiarkan LLM mengeksekusi arbitrary SQL.
* Jangan hardcode nama kota atau layer ke logic inti agent.
* Jangan memberikan akses dataset berdasarkan input frontend saja.
* Jangan mengarang jarak, jumlah, koordinat, fasilitas, atau hasil geometri.
* Validasi seluruh argumen tool.
* Batasi jumlah tool calls dan tangani loop yang tidak berakhir.
* Tangani provider errors secara eksplisit.
* Jangan mengembalikan API key, stack trace sensitif, atau secret kepada pengguna.
* Pertahankan provenance dari hasil tool.
* Jika data tidak cukup, sampaikan keterbatasannya.
* Jangan mengklaim analisis spasial berhasil jika tool gagal atau tidak dijalankan.

### 8.5 Aturan database dan migration

* Jangan menghapus volume database secara otomatis.
* Jangan menjalankan `docker compose down -v` pada database yang datanya perlu dipertahankan.
* Jangan menghapus migration yang sudah diterapkan tanpa rencana pemulihan yang benar.
* Periksa `alembic_version` dan schema aktual ketika menemukan migration error.
* Perhatikan idempotency dan konflik ketika membuat PostgreSQL enum, extension, index, atau table.
* Jangan menyelesaikan migration error dengan menghapus data tanpa persetujuan eksplisit.

### 8.6 Aturan Git

* Periksa branch dan working tree sebelum mengubah file.
* Jangan menimpa perubahan pengguna yang belum di-commit.
* Hindari perubahan di luar scope modul.
* Pisahkan pekerjaan menjadi commit logis jika diminta.
* Jangan mengklaim sudah commit, push, atau menjalankan test jika tidak dilakukan.
* Laporkan file yang berubah dan ringkasan diff.
* Jangan menganggap perubahan yang dibuat AI sudah otomatis berada di GitHub.

### 8.7 Cara memberikan solusi kepada pengguna

Pengguna proyek sedang mempelajari software engineering dan menggunakan AI untuk membantu development.

Karena itu:

* Jelaskan keputusan teknis dengan bahasa yang jelas.
* Berikan kode lengkap untuk file yang diminta jika bekerja secara manual.
* Sebutkan path file yang tepat.
* Jelaskan dependency dan perubahan konfigurasi.
* Berikan langkah implementasi dan test.
* Hindari jawaban berupa potongan kode tanpa menjelaskan letak dan cara integrasinya.
* Jangan mengubah banyak modul sekaligus tanpa kebutuhan yang jelas.

---

## 9. Peran Muse AI dan Antigravity

### Muse AI

Muse AI digunakan sebagai coding assistant berbasis pembacaan repository dan pemberian rekomendasi atau kode untuk diterapkan secara manual.

Tugas yang cocok:

* Code review.
* Analisis bug.
* Pemeriksaan arsitektur.
* Menyusun implementasi untuk file tertentu.
* Memeriksa keamanan dan error handling.
* Membuat unit test.
* Membandingkan beberapa pendekatan teknis.
* Menjelaskan kode existing.
* Mengidentifikasi gap antara requirement dan implementasi.

Muse AI tidak boleh mengasumsikan bahwa kode yang direkomendasikannya sudah diterapkan atau diuji. Setelah kode diterapkan, periksa diff dan jalankan test.

### Antigravity

Antigravity digunakan sebagai coding agent yang dapat membantu melakukan perubahan langsung pada workspace atau repository sesuai kemampuan dan izin lingkungan yang digunakan.

Tugas yang cocok:

* Implementasi modul yang terdefinisi.
* Perubahan lintas file.
* Menjalankan test dan memperbaiki error.
* Memeriksa integrasi pada repository.
* Melakukan verification gate.
* Menyiapkan laporan perubahan dan status Git.

Jangan menganggap suatu aksi otomatis berhasil hanya karena agent menyatakan telah melakukannya. Verifikasi output, test, dan repository.

### Cara keduanya bekerja bersama

1. Tetapkan requirement dan acceptance criteria.
2. Minta Muse AI melakukan review atau menyusun alternatif solusi.
3. Evaluasi usulan berdasarkan arsitektur ScapeGIS.
4. Implementasikan melalui Antigravity atau terapkan kode secara manual.
5. Jalankan test.
6. Minta review ulang jika terdapat perubahan arsitektur atau security-sensitive code.
7. Perbarui status modul dan dokumentasi.

---

## 10. Tugas Kali Ini

Bagian ini harus diperbarui setiap kali memulai sesi development baru.

**Jangan langsung mengerjakan fitur hanya berdasarkan judul tugas.** Periksa repository dan pahami konteks file yang terlibat terlebih dahulu.

### Template tugas

* **Nama modul:**
* **Tujuan:**
* **Masalah yang ingin diselesaikan:**
* **File yang relevan:**
* **Dependency terhadap modul lain:**
* **Perilaku existing yang harus dipertahankan:**
* **Perubahan yang diperbolehkan:**
* **Perubahan yang tidak diperbolehkan:**
* **Acceptance criteria:**
* **Test yang harus dijalankan:**
* **Definisi selesai:**

### Prosedur implementasi

1. Audit implementasi existing.
2. Laporkan temuan dan gap.
3. Ajukan solusi dengan scope minimal.
4. Implementasikan sesuai pola arsitektur existing.
5. Tambahkan atau perbarui test.
6. Jalankan test yang relevan.
7. Periksa regression risk dan authorization.
8. Laporkan file yang berubah, test, keterbatasan, dan pekerjaan tersisa.

Jangan melanjutkan ke modul berikutnya sebelum acceptance criteria modul saat ini terpenuhi atau blocker didokumentasikan dengan jelas.

---

## 11. Tugas Development Saat Ini

**Prioritas yang diketahui: Verifikasi Module 2B — Gemini Spatial Reasoning Agent.**

Sebelum melanjutkan ke Module 2C:

1. Periksa integrasi provider Gemini terhadap SDK yang benar-benar terpasang.
2. Verifikasi model yang digunakan benar-benar tersedia dan kompatibel.
3. Jalankan test Module 2B, Module 2A, Module 1, GIS authorization, dan full backend suite.
4. Verifikasi authorization pada endpoint Spatial AI.
5. Jika environment memungkinkan, lakukan live smoke test menggunakan dataset Pekanbaru.
6. Pastikan alur tool calling sampai PostGIS dan provenance benar-benar berjalan.
7. Catat semua test yang gagal, blocker, dan hasil yang belum diverifikasi.
8. Jangan melaporkan live test berhasil jika hanya menggunakan mock.
9. Jangan memulai Module 2C sebelum status verification gate dilaporkan.

Jika seluruh verification gate lulus, tahap selanjutnya adalah merancang dan mengimplementasikan Module 2C, dengan fokus pada kontrak API percakapan Spatial AI. Implementasi frontend chat, persistent conversation, streaming, dan integrasi map actions harus ditentukan sebagai scope terpisah apabila belum termasuk kontrak yang disepakati.

---

## 12. Format Laporan Setelah Setiap Pekerjaan

Setiap pekerjaan harus ditutup dengan laporan yang dapat diverifikasi.

### Ringkasan

* Modul yang dikerjakan:
* Hasil utama:
* Status: PASS / PARTIAL / BLOCKED / FAIL.

### Perubahan kode

* File baru:
* File diubah:
* Migration:
* Dependency:
* API contract yang berubah:

### Pengujian

* Command:
* Unit test:
* Integration test:
* Full suite:
* Live provider test:
* Database/dataset yang digunakan:

### Keamanan dan arsitektur

* Authorization:
* Tenant isolation:
* Secret handling:
* Spatial provenance:
* Regression risk:

### Git

* Branch:
* Working tree:
* Commit, jika benar-benar dibuat:
* Perubahan yang belum di-commit:

### Pekerjaan tersisa

* Blocker:
* Risiko:
* Hal yang belum diverifikasi:
* Rekomendasi langkah berikutnya:

---

## 13. Prinsip Akhir

ScapeGIS harus dikembangkan sebagai sistem SaaS geospasial yang aman, modular, dapat diuji, dan dapat dipelihara.

Prioritas utama:

1. Kebenaran data spasial.
2. Keamanan dan tenant isolation.
3. Integritas database dan migration.
4. Kontrak API yang konsisten.
5. Pemisahan tanggung jawab antar-layer.
6. Test yang benar-benar dijalankan.
7. AI yang dapat ditelusuri sumber faktanya.
8. Pengembangan bertahap tanpa merusak fitur existing.

**Instruksi untuk AI:** Jangan sekadar menghasilkan kode yang terlihat benar. Pastikan solusi sesuai dengan repository aktual, requirement, arsitektur, security boundary, dan acceptance criteria. Jika informasi belum cukup, lakukan pemeriksaan atau nyatakan asumsi secara eksplisit sebelum mengimplementasikan perubahan.
