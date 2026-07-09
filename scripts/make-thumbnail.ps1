param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

Add-Type -AssemblyName System.Drawing

$width = 1200
$height = 675
$source = [System.Drawing.Image]::FromFile($InputPath)
$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)

try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.DrawImage($source, 0, 0, $width, $height)

    $fontPath = 'C:\Windows\Fonts\NotoSansKR-VF.ttf'
    $fontCollection = New-Object System.Drawing.Text.PrivateFontCollection
    $fontCollection.AddFontFile($fontPath)
    $family = $fontCollection.Families[0]

    $badgeFont = New-Object System.Drawing.Font($family, 24, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $titleFont = New-Object System.Drawing.Font($family, 55, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $subtitleFont = New-Object System.Drawing.Font($family, 36, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)

    $navy = [System.Drawing.Color]::FromArgb(255, 22, 54, 96)
    $teal = [System.Drawing.Color]::FromArgb(255, 19, 143, 139)
    $yellow = [System.Drawing.Color]::FromArgb(255, 248, 184, 45)
    $white = [System.Drawing.Color]::White

    $badgeBrush = New-Object System.Drawing.SolidBrush($teal)
    $titleBrush = New-Object System.Drawing.SolidBrush($navy)
    $subtitleBrush = New-Object System.Drawing.SolidBrush($teal)
    $whiteBrush = New-Object System.Drawing.SolidBrush($white)
    $yellowBrush = New-Object System.Drawing.SolidBrush($yellow)

    $badgeRect = New-Object System.Drawing.RectangleF(72, 105, 310, 48)
    $badgePath = New-Object System.Drawing.Drawing2D.GraphicsPath
    $radius = 20
    $diameter = $radius * 2
    $badgePath.AddArc($badgeRect.X, $badgeRect.Y, $diameter, $diameter, 180, 90)
    $badgePath.AddArc($badgeRect.Right - $diameter, $badgeRect.Y, $diameter, $diameter, 270, 90)
    $badgePath.AddArc($badgeRect.Right - $diameter, $badgeRect.Bottom - $diameter, $diameter, $diameter, 0, 90)
    $badgePath.AddArc($badgeRect.X, $badgeRect.Bottom - $diameter, $diameter, $diameter, 90, 90)
    $badgePath.CloseFigure()
    $graphics.FillPath($badgeBrush, $badgePath)

    $textFormat = New-Object System.Drawing.StringFormat
    $textFormat.Alignment = [System.Drawing.StringAlignment]::Center
    $textFormat.LineAlignment = [System.Drawing.StringAlignment]::Center
    $graphics.DrawString('보증금 지키는 체크리스트', $badgeFont, $whiteBrush, $badgeRect, $textFormat)

    $graphics.FillRectangle($yellowBrush, 72, 184, 76, 8)
    $graphics.DrawString('전세 계약 전', $titleFont, $titleBrush, 68, 222)
    $graphics.DrawString('꼭 확인!', $titleFont, $titleBrush, 68, 296)
    $graphics.DrawString('필수 부동산 사이트 7곳', $subtitleFont, $subtitleBrush, 70, 390)

    $outputDirectory = Split-Path -Parent $OutputPath
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

    $encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/jpeg'
    $encoderParameters = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $encoderParameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, 92L)
    $bitmap.Save($OutputPath, $encoder, $encoderParameters)
}
finally {
    if ($encoderParameters) { $encoderParameters.Dispose() }
    if ($badgePath) { $badgePath.Dispose() }
    if ($textFormat) { $textFormat.Dispose() }
    if ($badgeFont) { $badgeFont.Dispose() }
    if ($titleFont) { $titleFont.Dispose() }
    if ($subtitleFont) { $subtitleFont.Dispose() }
    if ($badgeBrush) { $badgeBrush.Dispose() }
    if ($titleBrush) { $titleBrush.Dispose() }
    if ($subtitleBrush) { $subtitleBrush.Dispose() }
    if ($whiteBrush) { $whiteBrush.Dispose() }
    if ($yellowBrush) { $yellowBrush.Dispose() }
    if ($fontCollection) { $fontCollection.Dispose() }
    $graphics.Dispose()
    $bitmap.Dispose()
    $source.Dispose()
}
