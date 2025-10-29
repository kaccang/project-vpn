## Perangkat Keras
- CPU: 2 vCPU (minimal); untuk profil container disarankan 4 vCPU agar setiap profile dapat mengonsumsi hingga 200% (2 core) tanpa bottleneck.
- RAM: 4 GB minimal pada host; setiap container direkomendasikan ≥ 512 MB.
- Penyimpanan: 20 GB bebas untuk file backup (tar.gz), database sqlite, dan arsip konfigurasi.
- Koneksi: IP publik statis atau dynamic DNS untuk terminasi TLS (port 80/443 harus tersedia).

## Perangkat Lunak Host
- **Sistem Operasi:** Ubuntu 22.04/24.04 atau Debian 12 dengan kernel yang mendukung cgroupv2.
- **Docker Engine:** digunakan untuk menjalankan container perfil. Pastikan user admin memiliki akses sudo.
- **Python 3.10+:** dipakai oleh skrip admin (`admin/lib/profiles.py`) dan manajemen akun Xray (`script/lib/xray_accounts.py`).
- **Supervisorctl:** dianjurkan di dalam container menggantikan `systemctl`. Pastikan setiap container memiliki file konfigurasi supervisor untuk `xray`, `nginx`, dan cron job pengganti.
- **vnstat:** diperlukan oleh `script/bw-tele` dan penghitungan bandwidth di dashboard.
- **acme.sh:** dipakai oleh `config/cert` untuk perpanjangan sertifikat SSL.

## Container Profil
- **Image dasar:** `ubuntu:24.04`.
- **Paket minimum:** `supervisor`, `xray`, `nginx`, `curl`, `jq`, `vnstat`, `openssh-server`.
- **Direktori kerja:** `/opt/project-vpn` harus berisi `script/` dan `config/` agar menu otomatis berjalan.
- **Port:** SSH internal berjalan pada 22; host mengekspose port unik (2200–2333) per profile.
- **Pengelolaan resource:** skrip admin akan menerjemahkan CPU% menjadi parameter `--cpus` Docker dan RAM menjadi `--memory`.

## Dependensi Tambahan
- Akses ke API Telegram (opsional) untuk skrip `script/bw-tele`.
- Rclone (opsional) dan kredensial penyimpanan awan jika ingin mengunggah backup ke remote.
- Git untuk sinkronisasi kode saat melakukan deployment atau update.
