# ------------------------- CONFIGURABLE VARIABLES -----------------------------------------
param (
    [string]$port = "",
    [int]$baudRate = 0 
)

$board = "arduino:avr:uno"
$sketch = "TicTacToe/TicTacToe.ino"
$serialLog = "serial_output.log"
$pythonScript = "game.py"
$exeFilePath = "game.exe"
$pythonTestScript = "tests.py"  # Original test script for Python logic
$pythonHWTestScript = "hw_tests.py"  # Updated to include the Arduino communication test script
$testResultsLog = "test_results.log"  # Log file for test results
# ------------------------------------------------------------------------------------------

# Check if the log file exists and clear it
if (Test-Path $testResultsLog) {
    Write-Output "Log file exists, clearing the contents of $testResultsLog..."
    Clear-Content -Path $testResultsLog
} else {
}

function Check-ArduinoCLI {
    if (-not (Get-Command arduino-cli -ErrorAction SilentlyContinue)) {
        Write-Output "arduino-cli not found. Please install it."
        exit 1
    }
}

function Compile-Sketch {
    Write-Output "Compiling the Arduino sketch..."
    
    $compileCommand = & arduino-cli compile --fqbn $board $sketch
    if ($LASTEXITCODE -ne 0) {
        Write-Output "Sketch compilation failed. Please check for errors."
        exit 1
    }
    Write-Output "Sketch compiled successfully."
}

function Upload-Sketch {
    Write-Output "Uploading sketch to Arduino Uno board via port $port..."
    & arduino-cli upload -p $port --fqbn $board $sketch
    if ($LASTEXITCODE -ne 0) {
        Write-Output "Upload failed. Check the output for errors."
        exit 1
    }
}

function Generate-Exe {
    Write-Output "Generating .exe file from Python script $pythonScript..."
    
    # Використовуємо PyInstaller для створення .exe з Python скрипту
    $scriptDir = (Get-Location).Path  # Отримуємо поточний каталог
    & pyinstaller --onefile --distpath "$scriptDir" --workpath "$scriptDir/_build" --specpath "$scriptDir/_specs" $pythonScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Output "EXE file created successfully: $exeFilePath"
    } else {
        Write-Output "Failed to create EXE file."
        exit 1
    }
}

function Run-PythonTest {
    Write-Output "Running Python tests from script $pythonTestScript..."

    # Running the Python test file (tests.py)
    & python $pythonTestScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Output "Python logic test passed."
    } else {
        Write-Output "Python logic test failed. Check the Python test log."
        exit 1
    }
}

function Run-PythonHWTest {
    Write-Output "Running Arduino communication test from Python script $pythonHWTestScript..."

    # Running the hardware communication test file (hw_tests.py) with positional arguments
    & python $pythonHWTestScript $port $baudRate
    
    if ($LASTEXITCODE -eq 0) {
        Write-Output "UART communication test passed."
    } else {
        Write-Output "UART communication test failed. Check the Python test log."
        exit 1
    }
}

# Always generate the EXE file, regardless of input
Generate-Exe

# If port or baudRate are specified, proceed with Arduino interactions
if (-not [string]::IsNullOrEmpty($port) -and $baudRate -ne 0) {
    Check-ArduinoCLI
    Compile-Sketch
    Upload-Sketch
    # Run the Arduino communication test only if port and baudRate are specified
    Run-PythonHWTest
} else {
    Write-Output "No Arduino parameters provided, skipping Arduino tests."
}

# Run the Python tests for game logic
Run-PythonTest
