<#
.SYNOPSIS
    Cria uma Service Account com privilégio mínimo (somente leitura + execução de jobs)
    para conectar o Metabase (Docker) ao Google BigQuery com segurança.

.DESCRIPTION
    Segue exatamente as boas práticas de segurança IAM da aula e de produção:
    - roles/bigquery.dataViewer
    - roles/bigquery.jobUser
    - roles/bigquery.metadataViewer
    A chave gerada (`secrets/metabase-service-account.json`) já está protegida no `.gitignore`.
#>

param(
    [string]$ProjectId = "netflix-analytics-de",
    [string]$ServiceAccountName = "metabase-bq-reader"
)

$ErrorActionPreference = "Stop"
$env:CLOUDSDK_METRICS_ENVIRONMENT = "datacloud.antigravity"
$SdkBin = Join-Path $env:LOCALAPPDATA "Google\Cloud SDK\google-cloud-sdk\bin"
if ((Test-Path $SdkBin) -and ($env:Path -notlike "*$SdkBin*")) {
    $env:Path = "$SdkBin;$env:Path"
}
$SaEmail = "$ServiceAccountName@$ProjectId.iam.gserviceaccount.com"
$OutDir = Join-Path $PSScriptRoot "..\secrets"
$KeyPath = Join-Path $OutDir "metabase-service-account.json"

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

Write-Host "1/3 Verificando/Criando Service Account: $SaEmail ..." -ForegroundColor Cyan
$existing = gcloud iam service-accounts list --project=$ProjectId --filter="email:$SaEmail" --format="value(email)"
if (-not $existing) {
    gcloud iam service-accounts create $ServiceAccountName `
        --project=$ProjectId `
        --display-name="Metabase BigQuery Read-Only Connector"
}

Write-Host "2/3 Aplicando permissões IAM de privilégio mínimo ..." -ForegroundColor Cyan
$roles = @(
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/bigquery.metadataViewer"
)
foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$SaEmail" `
        --role=$role `
        --quiet | Out-Null
}

Write-Host "3/3 Gerando arquivo de credencial JSON em $KeyPath ..." -ForegroundColor Cyan
gcloud iam service-accounts keys create $KeyPath `
    --iam-account=$SaEmail `
    --project=$ProjectId

Write-Host "`nConcluído! Use o arquivo '$KeyPath' ao conectar o BigQuery no Metabase (http://localhost:3000)." -ForegroundColor Green

