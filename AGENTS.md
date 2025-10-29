# Repository Guidelines

## Project Structure & Module Organization
- `admin/`: rencana skrip CLI semi-GUI untuk manajemen profile/container (add, list, extend, backup). Implementasi baru harus membaca catatan pada setiap file.
- `config/`: konfigurasi layanan yang berjalan di container (`config.json`, `nginx.conf`) serta utilitas seperti `cert` dan `backup`. Pastikan perubahan tetap kompatibel dengan lingkungan tanpa `systemctl` dan `crontab`.
- `script/`: kumpulan skrip bash yang dieksekusi di dalam container Ubuntu 24.04 untuk mengelola akun Xray (vmess, vless, trojan). Jaga struktur komentar marker (`###`, `#&`, `#!`) karena parser mengandalkannya.
- `docs/`: dokumentasi publik; lengkapi sebelum rilis. `NOTE.MD` dan `RULES.MD` bersifat internal—pastikan tetap terabaikan oleh Git sesuai permintaan pemilik.

## Build, Test, and Development Commands
- `curl -fsSL https://raw.githubusercontent.com/kaccang/project-vpn/main/install.sh | bash`: instalasi cepat pada host baru (opsional variabel `INSTALL_*` untuk override lokasi).
- `bash script/menu`: membuka dashboard utama; jalankan dari dalam container atau lingkungan terisolasi yang menyerupai container.
- `bash config/backup`: membuat arsip konfigurasi dan mengunggah via rclone/Telegram (sesuaikan token dan mekanisme layanan non-systemd terlebih dahulu).
- `sqlite3 data/app.db`: gunakan untuk memeriksa atau memperbarui metadata profile ketika database sudah terisi.
- `bash tests/run_tests.sh`: rangkaian uji CLI (manipulasi akun Xray dan helper admin) menggunakan file konfigurasi dan database sementara.
- Saat menambahkan dependensi, gunakan manajer paket yang kompatibel dengan container (mis. `apt-get`) dan siapkan alternatif supervisord untuk layanan yang sebelumnya memakai `systemctl`.

## Coding Style & Naming Conventions
- Semua skrip menggunakan Bash; pertahankan indentasi dua atau empat spasi konsisten dan hindari tab.
- Upayakan ASCII saja kecuali file sudah memakai karakter lain.
- Variabel lingkungan sensitif (token, chat ID) harus dipindah ke `.env` atau file konfigurasi yang tidak dilacak Git.
- Marker akun di `config/config.json` wajib mempertahankan prefiks (`###`, `#&`, `#!`) agar skrip tetap dapat parsir.

## Testing Guidelines
- Saat ini tidak ada kerangka uji otomatis; prioritaskan pengujian manual: jalankan skrip penambahan akun, cek, dan penghapusan untuk setiap protokol.
- Simulasikan kondisi batas: username duplikat (case-insensitive), masa aktif habis, bandwidth tersisa 0, dan koneksi websocket.
- Dokumentasikan hasil uji di `MEMORY.MD` atau catatan tim, termasuk perbaikan yang diperlukan.

## Commit & Pull Request Guidelines
- Gunakan pesan ringkas dalam bahasa Indonesia atau Inggris, pola `feat:`, `fix:`, `docs:` dsb. Sertakan referensi file penting (`script/add-vmess`, `config/config.json`) agar reviewer mudah menelusuri.
- Per PR, jelaskan tujuan, langkah pengujian, dan dampak pada container (mis. kebutuhan regenerasi sertifikat atau restart supervisord).
- Lampirkan screenshot/terminal output bila perubahan memengaruhi UI CLI.
- Pastikan `.md` internal (selain `docs/`) tetap diabaikan Git; perbarui `.gitignore` jika menambah file serupa.
