# Data Migration Tool — how to run it

This tool cleans a messy CRM export and produces an import-ready CSV, a mapping
log and a QA report. Everything runs on your own computer; no data is uploaded
anywhere.

## One-time setup (about 5 minutes)

1. **Install Python 3.10 or newer** from https://www.python.org/downloads/
   (on Windows, tick "Add Python to PATH" during installation).
2. Open a terminal (macOS: Terminal, Windows: PowerShell) in this folder.
3. Install the tool:

   ```bash
   pip install -r data_migration_tool/requirements.txt
   ```

## Every time you use it

```bash
streamlit run data_migration_tool/app.py
```

Your browser opens automatically. Then:

1. **Upload** your CSV export (up to 200 MB).
2. **Choose the target CRM** — HubSpot, Salesforce or Pipedrive.
3. If your dates look like `04/03/2026`, set **Date order** in the left sidebar
   to the convention your export uses. Getting this wrong silently swaps days
   and months, so check it.
4. Click **Process File**.
5. **Download** the clean CSV, the QA report and the mapping log.

Close the tool by pressing `Ctrl+C` in the terminal.

## Putting your own name on the reports

Edit `data_migration_tool/branding.yaml`:

```yaml
brand_name: Your Agency
logo_url: "https://your-agency.com/logo.png"
footer_note: "Questions? hello@your-agency.com"
accent_colour: "#0f766e"
```

The QA report and audit report then carry your branding.

## Using a different CRM

Zoho, Keap, Monday.com and anything else are supported by adding one YAML file.
Start from `mapping_template.yaml` in this folder and follow
`data_migration_tool/docs/CUSTOM_CRM_MAPPING.md`.

## Without the web interface

For very large files or scripted runs:

```bash
python -m data_migration_tool.cli --input messy.csv --crm hubspot --outdir output/
```

Add `--date-order dayfirst` (or `monthfirst`) when your dates are ambiguous.

## If something goes wrong

| Message | What to do |
| --- | --- |
| "…is larger than 200 MB" | Split the file, or use the command line above |
| "…could not be read as a CSV table" | Re-export from the source system as CSV |
| "Something went wrong while processing this file" | Open the file in Excel to confirm it is a normal table, then re-export |
