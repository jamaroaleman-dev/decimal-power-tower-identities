#Requires -Version 5.1
<# Create a NEW public GitHub repository from this extracted release. #>
[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$')]
    [string]$RepositoryName = 'decimal-power-tower-identities',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$env:GH_HOST = 'github.com'
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-Checked {
    param([string]$Tool, [string[]]$Arguments)
    & $Tool @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Tool failed with exit code $LASTEXITCODE. Publication stopped."
    }
}

function Ensure-Tool {
    param([string]$Name, [string]$PackageId)
    if (Get-Command $Name -ErrorAction SilentlyContinue) { return }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "Install $Name, then run this command again. Automatic installation requires Windows Package Manager (winget)."
    }
    Write-Host "Installing $Name through Windows Package Manager..."
    Invoke-Checked 'winget' @('install', '--id', $PackageId, '--exact', '--source', 'winget', '--accept-package-agreements', '--accept-source-agreements')
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath;$env:Path"
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was installed but is not available in this terminal. Open a new terminal and run this script again."
    }
}

$projectRoot = $PSScriptRoot
foreach ($required in @('README.md', 'articulo_torres_en.tex', 'search.py', 'search_external_indices.py')) {
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $required) -PathType Leaf)) {
        throw "Release file missing: $required. Extract the complete ZIP first."
    }
}
if (Test-Path -LiteralPath (Join-Path $projectRoot '.git')) {
    throw 'This directory already contains a Git repository. Use a fresh extraction; no existing repository was modified.'
}
if ($DryRun) {
    Write-Host "Release validated. Normal execution installs missing tools, authenticates, creates a NEW PUBLIC repository named $RepositoryName, commits, and pushes."
    return
}

Ensure-Tool 'git' 'Git.Git'
Ensure-Tool 'gh' 'GitHub.cli'

& gh auth status --hostname github.com *> $null
if ($LASTEXITCODE -ne 0) {
    Invoke-Checked 'gh' @('auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https', '--web')
}
$accountJson = & gh api user --hostname github.com
if ($LASTEXITCODE -ne 0) { throw 'Could not identify the authenticated GitHub account.' }
$account = $accountJson | ConvertFrom-Json
$login = [string]$account.login
if (-not $login -or -not $account.id) { throw 'GitHub returned an invalid account record.' }
$fullName = "$login/$RepositoryName"

& gh repo view $fullName --json name *> $null
if ($LASTEXITCODE -eq 0) {
    throw "Repository $fullName already exists. It was not modified. Choose a different -RepositoryName."
}

Invoke-Checked 'gh' @('auth', 'setup-git', '--hostname', 'github.com')
Invoke-Checked 'git' @('-C', $projectRoot, 'init', '--initial-branch=main')
Invoke-Checked 'git' @('-C', $projectRoot, 'config', 'user.name', 'Josué Amaro')
$commitEmail = '{0}+{1}@users.noreply.github.com' -f $account.id, $login
Invoke-Checked 'git' @('-C', $projectRoot, 'config', 'user.email', $commitEmail)
Invoke-Checked 'git' @('-C', $projectRoot, 'add', '--all')
Invoke-Checked 'git' @('-C', $projectRoot, 'commit', '-m', 'Publish English manuscript and reproducible power-tower searches')
Invoke-Checked 'gh' @('repo', 'create', $fullName, '--public', '--source', $projectRoot, '--remote', 'origin', '--push', '--description', 'Self-referential decimal power towers and integer roots: manuscript and exact Python searches by Josue Amaro')
Write-Host "Published successfully: https://github.com/$fullName"
