# Instala NQMaster + GoldMaster (+ grabador de order flow) en ESTA PC.
# Uso (PowerShell, en la PC donde esta NinjaTrader 8):
#   powershell -ExecutionPolicy Bypass -File "<carpeta del repo>\tools\instalar_en_pc.ps1"
# Opciones:
#   -Destino "D:\NinjaTrader Strategy"   carpeta del repo (por defecto: Documentos\NinjaTrader Strategy)
#   -ConDatos                            tambien instala Python y restaura los datos de investigacion (~3 GB, para nt_compare.py)
param([string]$Destino = (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "NinjaTrader Strategy"), [switch]$ConDatos)
$ErrorActionPreference = "Stop"
$repo = "https://github.com/kiwiplusapp/nqmaster-research.git"

function Paso($t) { Write-Host ""; Write-Host "==> $t" -ForegroundColor Cyan }

Paso "1/4 Repositorio"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Falta Git. Instalalo desde https://git-scm.com/download/win y volve a correr este script." -ForegroundColor Red; exit 1
}
if (Test-Path (Join-Path $Destino ".git")) { git -C $Destino pull --ff-only }
else { git clone $repo $Destino }      # repo privado: Git pide iniciar sesion en GitHub la primera vez

Paso "2/4 NinjaTrader 8"
$custom = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "NinjaTrader 8\bin\Custom"
if (-not (Test-Path $custom)) {
    Write-Host "No encuentro $custom. Instala NinjaTrader 8, abrilo una vez, cerralo y volve a correr este script." -ForegroundColor Red; exit 1
}
if (Get-Process -Name NinjaTrader -ErrorAction SilentlyContinue) { Write-Host "NinjaTrader esta abierto: no hay problema, compilas con F5 al terminar." -ForegroundColor Yellow }
$bk = Join-Path $custom ("backup_nqmaster_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force $bk | Out-Null
foreach ($f in @("Strategies\NQMaster.cs", "Strategies\GoldMaster.cs", "Indicators\OrderFlowRecorder.cs")) {
    $p = Join-Path $custom $f
    if (Test-Path $p) { Copy-Item $p $bk -Force }                       # copia de lo que habia antes
}

Paso "3/4 Copiando estrategias e indicador"
Copy-Item (Join-Path $Destino "NQMaster.cs") (Join-Path $custom "Strategies") -Force
Copy-Item (Join-Path $Destino "GoldMaster.cs") (Join-Path $custom "Strategies") -Force
Copy-Item (Join-Path $Destino "OrderFlowRecorder.cs") (Join-Path $custom "Indicators") -Force
foreach ($f in @("Strategies\NQMaster.cs", "Strategies\GoldMaster.cs", "Indicators\OrderFlowRecorder.cs")) {
    $a = (Get-FileHash (Join-Path $Destino (Split-Path $f -Leaf))).Hash; $b = (Get-FileHash (Join-Path $custom $f)).Hash
    Write-Host ("  {0,-34} {1}" -f $f, $(if ($a -eq $b) { "OK" } else { "DISTINTO" }))
}
Write-Host "  Copia de seguridad de los archivos anteriores: $bk"

Paso "4/4 Datos de investigacion (opcional)"
if ($ConDatos) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Write-Host "Falta Python 3.11+: https://www.python.org/downloads/ (marca 'Add to PATH')." -ForegroundColor Red; exit 1 }
    Push-Location $Destino
    python -m pip install -r requirements.txt
    python tools\restore_data.py
    Pop-Location
} else { Write-Host "  Omitido (agrega -ConDatos para poder correr nt_compare.py y la investigacion en esta PC)." }

Write-Host ""
Write-Host "LISTO. Falta un paso en NinjaTrader:" -ForegroundColor Green
Write-Host "  Control Center > New > NinjaScript Editor > presionar F5 (compila). Abajo no debe aparecer ningun error."
Write-Host "  Guia de uso: $Destino\OPERAR_5x150K.md"
