## Instalasi Cepat
Jalankan perintah berikut sebagai `root` (atau gunakan `sudo -E bash`):

```bash
curl -fsSL https://raw.githubusercontent.com/kaccang/project-vpn/main/install.sh | bash
```

Variabel lingkungan opsional:
- `INSTALL_DIR=/opt/project-vpn` untuk menentukan lokasi pemasangan.
- `INSTALL_REPO`/`INSTALL_BRANCH` jika ingin memakai mirror atau branch lain.
- `INSTALL_SKIP_APT=1` untuk melewati instalasi paket (misal pada environment offline).

Setelah selesai, gunakan perintah `project-vpn-admin` untuk membuka dashboard admin.

## Prasyarat Manual
- Ubuntu 24.04 host dengan akses root.
- Docker Engine >= 24 (opsional tetapi disarankan untuk provisioning otomatis).
- Python 3.10+, curl, tar, dan vnstat pada host.
- Koneksi internet untuk menarik citra Ubuntu dan dependensi container.

## Langkah Instalasi Manual
1. **Kloning repositori**
   ```bash
   git clone https://github.com/kaccang/project-vpn.git
   cd project-vpn
   ```
2. **Siapkan dependensi host**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io python3-pip vnstat curl jq
   sudo systemctl enable --now docker
   ```
3. **Konfigurasi awal**
   - Pastikan file `/etc/xray/domain` berisi domain utama.
   - Salin `script/` ke lokasi yang akan dijalankan di dalam container (`/opt/project-vpn/script`).
   - Sesuaikan `config/config.json` bila ingin memodifikasi port/listener default.
4. **Bootstrap database**
   ```bash
   python3 admin/lib/profiles.py init
   ```
5. **Provision profile pertama**
   ```bash
   admin/menu-profile
   ```
   Pilih opsi *Tambah profile* dan ikuti wizard. Jika Docker tersedia, container Ubuntu 24.04 otomatis dibuat dengan nama `vpn-<username>` lengkap dengan batas CPU/RAM port SSH.
6. **Masuk ke container**
   Jalankan `admin/login-profile` dan pilih profile yang baru dibuat untuk memasang paket tambahan (nginx, supervisor, xray). Di dalam container jalankan:
   ```bash
   apt-get update
   apt-get install -y supervisor nginx xray vnstat curl
   ```
7. **Aktifkan menu otomatis**
   Tambahkan baris berikut pada `/root/.bashrc` di container:
   ```bash
   /opt/project-vpn/script/menu
   ```

## Pembaruan Sertifikat
Gunakan `config/cert` dari host untuk melakukan pembaruan Let’s Encrypt. Skrip otomatis menghentikan nginx melalui `supervisorctl` (jika tersedia) kemudian memasang sertifikat ke `/etc/xray/xray.crt`.
