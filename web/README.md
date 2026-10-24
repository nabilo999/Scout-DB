# ScoutIQ local player report

This is a small local React page. The Python API runs on the same computer and calls `nearest_neighbors.py` when you request a report.

## Start it

Open one PowerShell window in the project folder and run:

```powershell
py -m pip install -r requirements.txt
py -m uvicorn api:app --reload
```

Open a second PowerShell window and run:

```powershell
cd web
$env:NODE_OPTIONS = "--use-system-ca"
npm install
Remove-Item Env:NODE_OPTIONS
npm run dev -- --port 5174 --strictPort
```

Open `http://127.0.0.1:5174`. Port 5173 may already be used by another local project.
