# PowerShell script to create CodeProjects.zip with exclusions
$source = "C:\Users\holla\OneDrive\Desktop\CodeProjects"
$destination = "C:\Users\holla\OneDrive\Desktop\CodeProjects.zip"

# Remove existing zip if it exists
if (Test-Path $destination) {
    Remove-Item $destination -Force
}

# Get all items excluding virtual environments and other unwanted files
$items = Get-ChildItem -Path $source -Recurse | Where-Object {
    $_.FullName -notmatch "\\venv\\" -and
    $_.FullName -notmatch "\\\.venv\\" -and
    $_.FullName -notmatch "\\env\\" -and
    $_.FullName -notmatch "\\__pycache__\\" -and
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\\.git\\" -and
    $_.FullName -notmatch "\\dist\\" -and
    $_.FullName -notmatch "\\build\\" -and
    $_.Extension -ne ".pyc" -and
    $_.Name -ne ".env"
}

# Create a temporary directory
$tempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }

# Copy files to temp directory maintaining structure
foreach ($item in $items) {
    $relativePath = $item.FullName.Substring($source.Length + 1)
    $targetPath = Join-Path $tempDir $relativePath
    
    if ($item.PSIsContainer) {
        New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
    } else {
        $targetDir = Split-Path $targetPath -Parent
        if (!(Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $item.FullName -Destination $targetPath -Force
    }
}

# Compress the temporary directory
Compress-Archive -Path "$tempDir\*" -DestinationPath $destination -CompressionLevel Optimal

# Clean up
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "Successfully created $destination"