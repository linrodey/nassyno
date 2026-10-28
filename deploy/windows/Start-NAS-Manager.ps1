$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Can Docker Desktop (Linux containers). Khong can cai Python. Cai Docker Desktop tu docker.com va mo lai script.'
}
& docker info --format '{{.OSType}}' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Hay khoi dong Docker Desktop truoc.' }
& docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Can Docker Compose di kem Docker Desktop.' }
$runtime = Join-Path $PSScriptRoot 'runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
& icacls $runtime '/inheritance:r' '/grant:r' "*$($sid):(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Khong dat duoc quyen bao ve thu muc runtime.' }
$tokenPath = Join-Path $runtime 'app-token'
if (-not (Test-Path $tokenPath)) {
    Write-Host 'Tao khoa truy cap UNG DUNG it nhat 32 ky tu. Khong dung mat khau NAS.'
    $secure = Read-Host 'Khoa ung dung (se nhap lai trong trinh duyet)' -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        if ($value.Length -lt 32) { throw 'Khoa ung dung phai co it nhat 32 ky tu.' }
        [IO.File]::WriteAllText($tokenPath, $value, (New-Object Text.UTF8Encoding($false)))
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        $value = $null
        $secure.Dispose()
    }
}
$inventoryPath = Join-Path $runtime 'inventory.json'
if (-not (Test-Path $inventoryPath)) {
    Copy-Item (Join-Path $PSScriptRoot '../../config.nassite.example.json') $inventoryPath
}
& docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw 'Khoi dong that bai. Khong nhap tai khoan NAS vao trang chua hoat dong.' }
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8080/healthz' -TimeoutSec 2
        if ($health.status -eq 'ok') { $ready = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) { throw 'Dich vu chua san sang. Xem docker compose logs (khong gui bat ky bi mat nao).' }
Start-Process 'http://127.0.0.1:8080'
Write-Host 'Trang da mo tren localhost. Nhap khoa UNG DUNG, chon NAS SITE > Dang nhap thu.'
Write-Host 'Dung ung dung: docker compose down (chay trong thu muc nay).'
