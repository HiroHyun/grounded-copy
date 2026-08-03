# grounded-copy installer shim for PowerShell.
#
#   irm https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.ps1 | iex
#
# install.py holds every decision. This file resolves a Python 3 and hands the
# arguments over, so there is one implementation to keep correct.
#
# The body sits in a function because `$PSCommandPath` is $null under
# `irm | iex` and `$args` reaches a function reliably. The script downloads
# install.py to a temporary file and runs it from there: piping a string into a
# native process's stdin drops the pipe on some PowerShell hosts.

function Install-GroundedCopy {
    param([string[]] $Arguments = @())

    $ErrorActionPreference = 'Stop'
    $raw = 'https://raw.githubusercontent.com/HiroHyun/grounded-copy/main'

    $python = $null
    foreach ($candidate in @('python', 'python3', 'py')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -eq $command) { continue }
        & $candidate -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
    }
    if ($null -eq $python) {
        Write-Error 'grounded-copy: Python 3 is required and resolved as none of python, python3, py'
        return 1
    }

    # A clone runs its own copy.
    if ($PSCommandPath) {
        $local = Join-Path (Split-Path -Parent $PSCommandPath) 'install.py'
        if (Test-Path $local) {
            & $python $local @Arguments
            return $LASTEXITCODE
        }
    }

    $temp = Join-Path ([System.IO.Path]::GetTempPath()) ("grounded-copy-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temp | Out-Null
    try {
        $script = Join-Path $temp 'install.py'
        Invoke-WebRequest -Uri "$raw/install.py" -OutFile $script -UseBasicParsing
        & $python $script @Arguments
        return $LASTEXITCODE
    }
    finally {
        Remove-Item -Recurse -Force $temp -ErrorAction SilentlyContinue
    }
}

exit (Install-GroundedCopy -Arguments $args)
