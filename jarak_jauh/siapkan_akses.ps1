<#
Menyiapkan akses jarak jauh untuk Lyra ke laptop ini (Windows 11). JALANKAN SEKALI, sebagai Administrator.
Apa yang dilakukan (baca dulu sebelum menjalankan):
  1. Memasang Tailscale (jaringan privat) lewat winget. Setelah itu LOGIN dengan akun yang disebut Zhou.
  2. Memasang dan menyalakan OpenSSH Server, dengan login KATA SANDI DIMATIKAN (hanya kunci).
  3. Membuat akun Windows terbatas "lyra" (bukan administrator) dengan sandi acak yang TIDAK disimpan; login hanya lewat kunci.
  4. Memasukkan kunci PUBLIK yang diberikan Zhou ke akun itu. Kunci publik aman dibagikan; kunci pribadinya ada di laptop Zhou.
  5. Membatasi firewall: SSH hanya boleh dari jaringan Tailscale (100.64.0.0/10), bukan dari internet.
Mencabut akses kapan saja: jalankan  .\siapkan_akses.ps1 -Cabut
Pemakaian:  .\siapkan_akses.ps1 -KunciPublik "ssh-ed25519 AAAA... lyra-remote-beeffresh"
CATATAN JUJUR: skrip ini ditulis di Linux dan BELUM diuji di Windows. Jalankan, lalu kirim keluaran layarnya ke Zhou.
#>
param(
  [string]$KunciPublik = "",
  [switch]$Cabut
)
$ErrorActionPreference = "Stop"
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Host "Jalankan PowerShell sebagai Administrator." -ForegroundColor Red; exit 1 }

if ($Cabut) {
  Stop-Service sshd -ErrorAction SilentlyContinue; Set-Service sshd -StartupType Disabled -ErrorAction SilentlyContinue
  Remove-LocalUser -Name lyra -ErrorAction SilentlyContinue
  Remove-NetFirewallRule -Name "BeefFresh-SSH-Tailscale" -ErrorAction SilentlyContinue
  Write-Host "Akses Lyra dicabut: sshd dimatikan, akun 'lyra' dihapus, aturan firewall dihapus." -ForegroundColor Green; exit 0 }

if ($KunciPublik -notmatch '^ssh-ed25519 ') { Write-Host "Berikan -KunciPublik 'ssh-ed25519 ...' dari Zhou." -ForegroundColor Red; exit 1 }

Write-Host "== 1/5 Tailscale"
if (-not (Get-Command tailscale -ErrorAction SilentlyContinue) -and -not (Test-Path "$env:ProgramFiles\Tailscale\tailscale.exe")) {
  winget install --id Tailscale.Tailscale -e --accept-package-agreements --accept-source-agreements }
Write-Host "   Buka ikon Tailscale di pojok kanan bawah, lalu LOGIN dengan akun yang disebut Zhou."

Write-Host "== 2/5 OpenSSH Server"
$cap = Get-WindowsCapability -Online -Name "OpenSSH.Server*" | Select-Object -First 1
if ($cap.State -ne "Installed") { Add-WindowsCapability -Online -Name $cap.Name | Out-Null }
$cfg = "$env:ProgramData\ssh\sshd_config"
if (-not (Test-Path $cfg)) { Start-Service sshd; Stop-Service sshd }
$t = Get-Content $cfg
$t = $t -replace '^\s*#?\s*PasswordAuthentication\s+.*$', 'PasswordAuthentication no'
if ($t -notmatch '^PasswordAuthentication no') { $t += 'PasswordAuthentication no' }
if ($t -notmatch '^AllowUsers') { $t += 'AllowUsers lyra' }
Set-Content $cfg $t
Set-Service sshd -StartupType Automatic; Restart-Service sshd

Write-Host "== 3/5 Akun terbatas 'lyra'"
if (-not (Get-LocalUser -Name lyra -ErrorAction SilentlyContinue)) {
  $acak = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
  New-LocalUser -Name lyra -Password (ConvertTo-SecureString $acak -AsPlainText -Force) -PasswordNeverExpires -Description "Akses jarak jauh Lyra (hanya kunci SSH)" | Out-Null
  Add-LocalGroupMember -Group "Users" -Member lyra
  Remove-Variable acak }

Write-Host "== 4/5 Kunci publik"
$home_lyra = "C:\Users\lyra"
if (-not (Test-Path $home_lyra)) { # profil dibuat saat login pertama; buat folder .ssh langsung
  New-Item -ItemType Directory -Path $home_lyra | Out-Null }
New-Item -ItemType Directory -Force -Path "$home_lyra\.ssh" | Out-Null
Set-Content -Path "$home_lyra\.ssh\authorized_keys" -Value $KunciPublik -Encoding ascii
icacls "$home_lyra\.ssh\authorized_keys" /inheritance:r /grant "lyra:F" "SYSTEM:F" "Administrators:F" | Out-Null

Write-Host "== 5/5 Firewall: SSH hanya dari Tailscale"
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue | Disable-NetFirewallRule
New-NetFirewallRule -Name "BeefFresh-SSH-Tailscale" -DisplayName "BeefFresh SSH (hanya Tailscale)" -Direction Inbound -Protocol TCP -LocalPort 22 -RemoteAddress 100.64.0.0/10 -Action Allow | Out-Null

Write-Host ""
Write-Host "SELESAI. Kirim ke Zhou: (a) nama laptop ini, (b) hasil perintah  tailscale ip -4  (c) apakah ada pesan merah di atas." -ForegroundColor Green
Write-Host "Tambahan: Pengaturan > Sistem > Daya: set 'Tidur' = Tidak pernah saat tercolok listrik, supaya laptop tetap bisa dijangkau."
