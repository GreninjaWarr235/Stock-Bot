# PowerShell script to register SwingBotIntradayScanner task for market hours portfolio monitoring
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$botDir = (Get-Item "$scriptDir\..").FullName
$batPath = "$scriptDir\run_intraday_scanner.bat"

# Define action to run the batch script in bot directory
$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $botDir

# Define weekday trigger starting at 9:15 AM (Monday to Friday) repeating every 15 minutes for 6 hours 15 minutes (until 3:30 PM)
$daysOfWeek = [System.DayOfWeek]::Monday, [System.DayOfWeek]::Tuesday, [System.DayOfWeek]::Wednesday, [System.DayOfWeek]::Thursday, [System.DayOfWeek]::Friday
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $daysOfWeek -At 9:15AM
$rep = New-ScheduledTaskTrigger -Once -At 9:15AM -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Hours 6 -Minutes 15)
$trigger.Repetition = $rep.Repetition

# Configure settings: Wake from sleep, allow on battery, start immediately if missed
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun `
    -StartWhenAvailable

# Register task under current user context
try {
    Register-ScheduledTask `
        -TaskName "SwingBotIntradayScanner" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -User "$env:USERDOMAIN\$env:USERNAME" `
        -Force
    Write-Host "Successfully registered 'SwingBotIntradayScanner' task for $env:USERNAME!"
} catch {
    Register-ScheduledTask `
        -TaskName "SwingBotIntradayScanner" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Force
    Write-Host "Registered 'SwingBotIntradayScanner' task!"
}

Write-Host "   - Target Universe: portfolio.csv"
Write-Host "   - Schedule: Mon-Fri, 9:15 AM to 3:30 PM IST (Every 15 Minutes)"
Write-Host "   - Wake from Sleep: ENABLED"
Write-Host "   - Run on Battery: ENABLED"
