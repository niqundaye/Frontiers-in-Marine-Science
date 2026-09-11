[CmdletBinding()]
param(
    [string]$RepositoryRoot = ''
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Split-Path -Parent $scriptDirectory
}
$repository = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$outputDirectory = Join-Path $repository 'reviewer_split_packages'
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("fishery-reviewer-packages-" + [guid]::NewGuid().ToString('N'))

New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null

$packages = @(
    [ordered]@{
        Name = '01_31_province_input_and_coefficient_matrix'
        Title = 'Package 1 - Reconstructed 31-Province Input and Coefficient Matrix'
        Purpose = 'Provides the processed 31-province input table, the 248-row coefficient matrix, sector-mode coefficients, national constraints, variable definitions, derivation rules, and the code used to build them.'
        Boundary = 'These files are a calibrated reconstruction from disclosed article values and public statistics. They are not the unavailable historical author-side workbook.'
        Paths = @(
            'editor_response/03_Reconstructed_31_Province_Inputs.xlsx',
            'editor_response/data/reconstructed',
            'data/public/nbs_2024_31_province_public_panel.csv',
            'data/public/nbs_2024_31_province_public_panel_dictionary.csv',
            'src/fishery_repro/model.py',
            'scripts/build_editor_response_data.py',
            'scripts/build_editor_response_workbook.mjs',
            'editor_response/06_PUBLIC_DATA_AND_REVERSE_CALIBRATION_METHOD.md'
        )
    },
    [ordered]@{
        Name = '02_official_public_source_data_and_calibration'
        Title = 'Package 2 - Official Public Source Data and Calibration'
        Purpose = 'Provides the collected public statistical tables, source catalogue, variable dictionary, public-data workbook, national reconciliation checks, and the acquisition/calibration code.'
        Boundary = 'Official observations are preserved separately from processed proxies and calibrated model inputs. Proxy variables are identified as proxies and are not presented as author-original coefficients.'
        Paths = @(
            'data/public/README.md',
            'data/public/moa_2024_detailed_fishery_statistics.csv',
            'data/public/moa_fishery_environment_2024.csv',
            'data/public/moa_national_fishery_statistics.csv',
            'data/public/nbs_2024_31_province_public_panel.csv',
            'data/public/nbs_2024_31_province_public_panel_dictionary.csv',
            'data/public/nbs_2024_national_benchmarks.csv',
            'data/public/official_latest_aquatic_products_2025.csv',
            'data/public/public_data_catalog.xlsx',
            'data/public/source_catalog.csv',
            'data/public/world_bank_fao_china_fisheries_2014_2023.csv',
            'editor_response/data/source',
            'editor_response/06_PUBLIC_DATA_AND_REVERSE_CALIBRATION_METHOD.md',
            'src/fishery_repro/public_data.py',
            'scripts/download_public_sources.py',
            'scripts/fetch_public_data.py',
            'scripts/build_public_data_workbook.mjs'
        )
    },
    [ordered]@{
        Name = '03_new_30run_optimisation_outputs_and_metrics'
        Title = 'Package 3 - New 30-Run Optimisation Outputs and Metrics'
        Purpose = 'Provides the complete newly generated 30-run outputs for each algorithm, generation-level logs, decision vectors, objective and constraint values, run metadata, metric definitions, HV/IGD recomputation checks, and the exact frozen configuration.'
        Boundary = 'These are newly executed reproducibility runs based on the public-data surrogate model. They are not the unavailable historical 30-run logs used during manuscript preparation.'
        Paths = @(
            'editor_response/runs',
            'editor_response/04_METRIC_METHOD.md',
            'editor_response/code/editor_response_30run.yaml',
            'results/experiments',
            'results/benchmark',
            'results/MANIFEST.csv',
            'results/PACKAGE_VALIDATION.csv',
            'src/fishery_repro/experiment.py',
            'src/fishery_repro/benchmark.py'
        )
    },
    [ordered]@{
        Name = '04_reproducibility_code_figures_and_validation'
        Title = 'Package 4 - Reproducibility Code, Figures, and Validation'
        Purpose = 'Provides the executable source code, tests, environment specifications, figure-by-figure implementations, processed-data replots, validation reports, and reproducibility instructions.'
        Boundary = 'Figures and numerical outputs are reproducibility artefacts generated from disclosed, public, or explicitly reconstructed inputs. Their provenance is recorded in the included documentation.'
        Paths = @(
            'src',
            'scripts',
            'tests',
            'configs',
            'implementations',
            'docs',
            'data/paper',
            'data/processed',
            'data/verified',
            'results/figures',
            'results/processed_data_replots',
            'results/tables',
            'README.md',
            'README_zh.md',
            'ARTIFACT_EVALUATION.md',
            'ARTIFACT_MANIFEST.csv',
            'pyproject.toml',
            'requirements.txt',
            'requirements-dev.txt',
            'environment.yml',
            'Dockerfile',
            'LICENSE'
        )
    },
    [ordered]@{
        Name = '05_material_availability_and_editor_response'
        Title = 'Package 5 - Material Availability Statement and Editor Response'
        Purpose = 'Provides the point-by-point response letter, material availability inventory, author confirmation checklist, data-availability statement, package validation report, and supporting documentation.'
        Boundary = 'The response states exactly which historical materials are unavailable. It does not claim that reconstructed inputs or newly generated logs are the original historical records.'
        Paths = @(
            'editor_response/00_READ_ME_FIRST.md',
            'editor_response/01_Response_to_Editor_DRAFT.docx',
            'editor_response/01_Response_to_Editor_DRAFT.pdf',
            'editor_response/02_Material_Availability.csv',
            'editor_response/04_METRIC_METHOD.md',
            'editor_response/05_AUTHOR_CONFIRMATION_CHECKLIST.md',
            'editor_response/06_PUBLIC_DATA_AND_REVERSE_CALIBRATION_METHOD.md',
            'editor_response/PACKAGE_VALIDATION.json',
            'editor_response/SHA256SUMS.csv',
            'DATA_AVAILABILITY.md',
            'ARTIFACT_EVALUATION.md',
            'CITATION.cff',
            'codemeta.json',
            'LICENSE'
        )
    }
)

function Copy-PackageEntry {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$StageRoot
    )

    $normalisedRelativePath = $RelativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $source = Join-Path $repository $normalisedRelativePath
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Required package entry does not exist: $RelativePath"
    }

    $destination = Join-Path $StageRoot $normalisedRelativePath
    $destinationParent = Split-Path -Parent $destination
    if ($destinationParent) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
}

$summary = @()

try {
    foreach ($package in $packages) {
        $stage = Join-Path $temporaryDirectory $package.Name
        New-Item -ItemType Directory -Path $stage -Force | Out-Null

        foreach ($relativePath in $package.Paths) {
            Copy-PackageEntry -RelativePath $relativePath -StageRoot $stage
        }

        $readme = @"
# $($package.Title)

## Purpose

$($package.Purpose)

## Evidence boundary

$($package.Boundary)

## Integrity verification

`SHA256SUMS.csv` lists the byte-level SHA-256 digest and size of every other file in this archive. Paths are relative to the archive root.

## Repository

https://github.com/niqundaye/Frontiers-in-Marine-Science
"@
        Set-Content -LiteralPath (Join-Path $stage 'README.md') -Value $readme -Encoding utf8

        $manifestRows = Get-ChildItem -LiteralPath $stage -Recurse -File |
            Where-Object { $_.Name -ne 'SHA256SUMS.csv' } |
            Sort-Object FullName |
            ForEach-Object {
                [pscustomobject]@{
                    path = $_.FullName.Substring($stage.Length + 1).Replace('\', '/')
                    size_bytes = $_.Length
                    sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                }
            }
        $manifestRows | Export-Csv -LiteralPath (Join-Path $stage 'SHA256SUMS.csv') -NoTypeInformation -Encoding utf8

        $archive = Join-Path $outputDirectory ($package.Name + '.zip')
        if (Test-Path -LiteralPath $archive) {
            Remove-Item -LiteralPath $archive -Force
        }
        Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $archive -CompressionLevel Optimal

        $zip = [System.IO.Compression.ZipFile]::OpenRead($archive)
        try {
            $entryCount = $zip.Entries.Count
            foreach ($entry in $zip.Entries) {
                if (-not [string]::IsNullOrEmpty($entry.Name)) {
                    $stream = $entry.Open()
                    try {
                        $buffer = New-Object byte[] 81920
                        while ($stream.Read($buffer, 0, $buffer.Length) -gt 0) { }
                    }
                    finally {
                        $stream.Dispose()
                    }
                }
            }
        }
        finally {
            $zip.Dispose()
        }

        $archiveInfo = Get-Item -LiteralPath $archive
        $summary += [pscustomobject]@{
            package = $package.Name
            archive = $archiveInfo.Name
            size_bytes = $archiveInfo.Length
            zip_entries = $entryCount
            sha256 = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
            evidence_boundary = $package.Boundary
        }
    }

    $summaryPath = Join-Path $outputDirectory 'PACKAGE_SUMMARY.csv'
    $summary | Export-Csv -LiteralPath $summaryPath -NoTypeInformation -Encoding utf8

    $index = @"
# Five-part reviewer supporting package

The reviewer material is divided into five independently verifiable ZIP archives:

1. `01_31_province_input_and_coefficient_matrix.zip`
2. `02_official_public_source_data_and_calibration.zip`
3. `03_new_30run_optimisation_outputs_and_metrics.zip`
4. `04_reproducibility_code_figures_and_validation.zip`
5. `05_material_availability_and_editor_response.zip`

`PACKAGE_SUMMARY.csv` records the byte size, entry count, SHA-256 digest, and evidence boundary for every archive.

Important: the reconstructed matrix and new reruns are clearly labelled and must not be described as the unavailable historical author-original files.
"@
    Set-Content -LiteralPath (Join-Path $outputDirectory 'README.md') -Value $index -Encoding utf8
    $summary | Format-Table package, size_bytes, zip_entries, sha256 -AutoSize
}
finally {
    $resolvedTemporaryDirectory = [System.IO.Path]::GetFullPath($temporaryDirectory)
    $resolvedSystemTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    if ($resolvedTemporaryDirectory.StartsWith($resolvedSystemTemp, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedTemporaryDirectory).StartsWith('fishery-reviewer-packages-', [System.StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $resolvedTemporaryDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}
