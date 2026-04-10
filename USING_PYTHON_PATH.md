# Using the Specified Python Path

This project uses a specific Python installation located at:
```
C:\Users\svijapur\AppData\Local\Programs\Python\Python314\python.exe
```

## Helper Scripts

For convenience, PowerShell helper scripts have been created to run Python commands with the correct path:

### Available Scripts

1. **`run_python.ps1`** - Generic Python script runner
   ```powershell
   .\run_python.ps1 script_name.py [arguments]
   ```

2. **`run_service.ps1`** - Start the FastAPI service
   ```powershell
   .\run_service.ps1
   ```

## Direct Python Usage

If you prefer to use Python directly, use the full path:

```powershell
C:\Users\svijapur\AppData\Local\Programs\Python\Python314\python.exe script_name.py [arguments]
```

## Examples

### Install Dependencies
```powershell
C:\Users\svijapur\AppData\Local\Programs\Python\Python314\python.exe -m pip install -r requirements.txt
```

Or using the helper script:
```powershell
.\run_python.ps1 -m pip install -r requirements.txt
```

### Start the Service
```powershell
.\run_service.ps1
```

Or directly:
```powershell
C:\Users\svijapur\AppData\Local\Programs\Python\Python314\python.exe start_service.py
```

### Run Test Scripts
```powershell
.\run_python.ps1 test_service.py
.\run_python.ps1 test_bulk_import.py
.\run_python.ps1 quick_test.py
```

## Note for Kubernetes Deployment

The Kubernetes deployment files use the container's Python installation (not the host's Python path). The helper scripts are only for local development on Windows.

