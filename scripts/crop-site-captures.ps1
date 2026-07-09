param(
    [string]$SourceDirectory = '.\assets\site-captures'
)

Add-Type -AssemblyName System.Drawing

Get-ChildItem -LiteralPath $SourceDirectory -Filter '*.png' | ForEach-Object {
    $source = [System.Drawing.Image]::FromFile($_.FullName)
    $cropWidth = $source.Width
    $cropHeight = [Math]::Min([int]($cropWidth * 0.75), $source.Height)
    $bitmap = New-Object System.Drawing.Bitmap($cropWidth, $cropHeight)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    try {
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage(
            $source,
            (New-Object System.Drawing.Rectangle(0, 0, $cropWidth, $cropHeight)),
            (New-Object System.Drawing.Rectangle(0, 0, $cropWidth, $cropHeight)),
            [System.Drawing.GraphicsUnit]::Pixel
        )

        $outputPath = Join-Path $_.DirectoryName ($_.BaseName + '.jpg')
        $encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
            Where-Object MimeType -eq 'image/jpeg'
        $parameters = New-Object System.Drawing.Imaging.EncoderParameters(1)
        $parameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter(
            [System.Drawing.Imaging.Encoder]::Quality,
            90L
        )
        $bitmap.Save($outputPath, $encoder, $parameters)
    }
    finally {
        if ($parameters) { $parameters.Dispose() }
        $graphics.Dispose()
        $bitmap.Dispose()
        $source.Dispose()
    }
}
