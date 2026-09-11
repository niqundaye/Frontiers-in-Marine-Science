param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$taskInput = (Resolve-Path -LiteralPath $InputPath).Path
$taskOutput = [System.IO.Path]::GetFullPath($OutputPath)
$taskWord = $null
$taskDocument = $null

try {
    $taskWord = New-Object -ComObject Word.Application
    $taskWord.Visible = $false
    $taskWord.DisplayAlerts = 0
    $taskDocument = $taskWord.Documents.Open($taskInput, $false, $true)
    # 17 = wdExportFormatPDF.
    $taskDocument.ExportAsFixedFormat($taskOutput, 17)
}
finally {
    if ($null -ne $taskDocument) {
        $taskDocument.Close($false)
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskDocument)
    }
    if ($null -ne $taskWord) {
        $taskWord.Quit()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskWord)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Get-Item -LiteralPath $taskOutput | Select-Object FullName, Length, LastWriteTime
