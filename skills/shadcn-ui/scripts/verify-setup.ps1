$ErrorActionPreference = "Stop"

$ok = $true

function Write-Success($message) {
    Write-Host "✓ $message"
}

function Write-Warn($message) {
    Write-Host "⚠ $message"
}

function Write-Fail($message) {
    Write-Host "✗ $message"
}

Write-Host "🔍 Verifying shadcn/ui setup..."
Write-Host ""

# components.json
if (Test-Path "components.json") {
    Write-Success "components.json found"
}
else {
    Write-Fail "components.json not found"
    Write-Host "  Run: npx shadcn@latest init"
    exit 1
}

# tailwind config
if ((Test-Path "tailwind.config.js") -or (Test-Path "tailwind.config.ts")) {
    Write-Success "Tailwind config found"
}
else {
    Write-Fail "tailwind.config.js not found"
    Write-Host "  Install Tailwind: npm install -D tailwindcss postcss autoprefixer"
    exit 1
}

# tsconfig alias
if (Test-Path "tsconfig.json") {
    $tsconfig = Get-Content "tsconfig.json" -Raw
    if ($tsconfig -match '"@/\*"') {
        Write-Success "Path aliases configured in tsconfig.json"
    }
    else {
        Write-Warn "Path aliases not found in tsconfig.json"
    }
}
else {
    Write-Warn "tsconfig.json not found (TypeScript not configured)"
}

# css file
$cssCandidates = @("src/index.css", "src/globals.css", "app/globals.css")
$cssFile = $null
foreach ($candidate in $cssCandidates) {
    if (Test-Path $candidate) {
        $cssFile = $candidate
        break
    }
}

if ($cssFile) {
    Write-Success "Global CSS file found"
    $css = Get-Content $cssFile -Raw
    if ($css -match "@tailwind\s+base") {
        Write-Success "Tailwind directives present"
    }
    else {
        Write-Fail "Tailwind directives missing"
        $ok = $false
    }

    if (($css -match ":\s*root") -or ($css -match "@layer\s+base")) {
        Write-Success "CSS variables defined"
    }
    else {
        Write-Warn "CSS variables not found"
    }
}
else {
    Write-Fail "Global CSS file not found"
    $ok = $false
}

# components/ui
$uiDirs = @("src/components/ui", "components/ui")
$uiDir = $null
foreach ($candidate in $uiDirs) {
    if (Test-Path $candidate) {
        $uiDir = $candidate
        break
    }
}

if ($uiDir) {
    Write-Success "components/ui directory exists"
    $componentCount = (Get-ChildItem $uiDir -File -Include *.tsx, *.jsx -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "  $componentCount components installed"
}
else {
    Write-Warn "components/ui directory not found"
}

# lib/utils.ts
$utilsCandidates = @("src/lib/utils.ts", "lib/utils.ts")
$utilsFile = $null
foreach ($candidate in $utilsCandidates) {
    if (Test-Path $candidate) {
        $utilsFile = $candidate
        break
    }
}

if ($utilsFile) {
    Write-Success "lib/utils.ts exists"
    $utils = Get-Content $utilsFile -Raw
    if ($utils -match "export\s+function\s+cn") {
        Write-Success "cn() utility function present"
    }
    else {
        Write-Fail "cn() utility function missing"
        $ok = $false
    }
}
else {
    Write-Fail "lib/utils.ts not found"
    $ok = $false
}

Write-Host ""
if ($ok) {
    Write-Success "Setup verification complete!"
    exit 0
}

Write-Fail "Setup verification found blocking issues."
exit 1
