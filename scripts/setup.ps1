param([string]$Python = 'python', [switch]$LocalGenerator)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& $Python -m venv --without-pip .venv
if ($LASTEXITCODE -ne 0) { throw '创建虚拟环境失败，请用 -Python 指定可运行的 Python 3.12+' }
& $Python -m pip --python .\.venv\Scripts\python.exe install numpy==2.2.6 transformers==4.57.1
if ($LASTEXITCODE -ne 0) { throw '依赖安装失败' }
& $Python -m pip --python .\.venv\Scripts\python.exe install torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'PyTorch 安装失败' }
if ($LocalGenerator) { & .\.venv\Scripts\python.exe scripts\download_models.py --generation }
else { & .\.venv\Scripts\python.exe scripts\download_models.py }
if ($LASTEXITCODE -ne 0) { throw '模型下载失败' }
& .\.venv\Scripts\python.exe -m src.cli index
if ($LASTEXITCODE -ne 0) { throw '索引建立失败' }
