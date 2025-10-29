# Repository Guidelines

## Project Structure & Module Organization
- `admin/`: kumpulan utilitas semi-GUI untuk administrasi akun dan kontainer; baca komentar setiap skrip sebelum modifikasi karena menyimpan catatan alur.
- `config/`: konfigurasi layanan Xray, nginx, sertifikat, dan backup; skrip harus tetap berjalan di lingkungan tanpa `systemctl` atau `crontab`.
- `script/`: skrip Bash inti (vmess, vless, trojan) yang dipanggil menu utama; pertahankan marker komentar `###`, `#&`, `#!` agar parser internal tidak rusak.
- `docs/`: dokumentasi publik yang siap dibagikan; berkas internal seperti `NOTE.MD` dan `RULES.MD` wajib tetap terabaikan Git.
- `tests/` dan `data/`: skenario uji CLI serta database SQLite (`data/app.db`) untuk metadata profil; gunakan salinan sementara saat pengembangan.

## Build, Test, and Development Commands
- `curl -fsSL https://raw.githubusercontent.com/kaccang/project-vpn/main/install.sh | bash`: installer satu langkah untuk host baru; dukung override lokasi melalui variabel `INSTALL_*`.
- `bash script/menu`: membuka dashboard interaktif di dalam container Ubuntu 24.04 atau lingkungan yang menyerupai.
- `bash config/backup`: membuat arsip konfigurasi dan mengunggah via rclone/Telegram; sesuaikan token di `.env` lokal.
- `sqlite3 data/app.db`: inspeksi atau perbarui metadata akun secara manual.
- `bash tests/run_tests.sh`: menjalankan rangkaian uji CLI dengan file konfigurasi dan basis data sementara.

## Coding Style & Naming Conventions
- Seluruh kode menggunakan Bash; jaga indentasi 2 atau 4 spasi secara konsisten, tanpa tab.
- Gunakan ASCII kecuali berkas sudah memakai karakter lain; beri komentar singkat hanya untuk blok yang kompleks.
- Simpan kredensial (TOKEN, CHAT_ID, UUID) di `.env` atau konfigurasi non-tracked lalu referensikan melalui variabel lingkungan.
- Ikuti pola penamaan skrip `verb-protocol` (`add-vmess`, `renew-trojan`) dan pertahankan prefiks marker di `config/config.json`.

## Testing Guidelines
- Jalankan `bash tests/run_tests.sh` setelah menambah fitur, lalu lanjutkan uji manual untuk skenario penambahan, perpanjangan, dan penghapusan tiap protokol.
- Verifikasi kasus tepi: username duplikat (abaikan kapital), masa aktif habis, kuota 0, serta koneksi websocket; catat hasilnya di `MEMORY.MD`.
- Saat mengubah installer, lakukan uji `curl … | bash` pada VPS bersih atau container baru untuk memastikan dependensi otomatis terpasang.

## Commit & Pull Request Guidelines
- Gunakan format pesan singkat `feat:`, `fix:`, `docs:` dengan menyebut file kunci; contoh `feat: tambah script/user-vless untuk provisioning`.
- Setiap PR harus memuat ringkasan perubahan, langkah uji, serta dampak pada kontainer (mis. butuh regenerasi sertifikat atau restart supervisord).
- Lampirkan tangkapan terminal bila UI CLI berubah dan pastikan berkas internal (`NOTE.MD`, `RULES.MD`, `MEMORY.MD`) tetap berada dalam `.gitignore`.
