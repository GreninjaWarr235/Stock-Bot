# PowerShell script to register SwingBotScanner task with wake-on-sleep support
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$botDir = (Get-Item "$scriptDir\..").FullName
$batPath = "$scriptDir\run_scanner.bat"

# Define action to run the batch script in bot directory
$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $botDir

# Define weekday trigger at 4:05 PM (Monday to Friday only)
$daysOfWeek = [System.DayOfWeek]::Monday, [System.DayOfWeek]::Tuesday, [System.DayOfWeek]::Wednesday, [System.DayOfWeek]::Thursday, [System.DayOfWeek]::Friday
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $daysOfWeek -At 4:05PM

# Configure settings: Wake from sleep, allow on battery, start immediately if missed
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun `
    -StartWhenAvailable

# Try registering under current user context first
try {
    Register-ScheduledTask `
        -TaskName "SwingBotScanner" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -User "$env:USERDOMAIN\$env:USERNAME" `
        -Force
    Write-Host "Successfully registered 'SwingBotScanner' task for $env:USERNAME!"
} catch {
    # Fallback to registering basic user task
    Register-ScheduledTask `
        -TaskName "SwingBotScanner" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Force
    Write-Host "Registered 'SwingBotScanner' task!"
}

Write-Host "   - Schedule: Weekdays (Mon-Fri) at 4:05 PM IST"
Write-Host "   - Wake from Sleep: ENABLED"
Write-Host "   - Run when Locked: ENABLED"
Write-Host "   - Run on Battery: ENABLED"
