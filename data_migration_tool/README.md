# AutoFlow Data Migration Tool

Takes a messy CRM export and returns an import-ready CSV, a mapping log and a QA report.
Optionally audits what the client actually ended up with after the import.

```
raw CSV -> CLEANER -> MAPPER -> VALIDATOR -> deliverables -> POST-IMPORT AUDITOR
```

## Quick start

```bash
cd data_migration_tool
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Web interface
streamlit run app.py

# Command line
python -m data_migration_tool.cli \
  -i data_migration_tool/samples/messy_contacts.csv \
  -c hubspot \
  -o output              # run from the repository root
```

The CLI exits with status `1` when the validator found errors, so it can gate a delivery script.

## Reading client files

Encoding is detected per file (`charset-normalizer`), so Windows-1252 exports with
`Müller` or `Café` load without a `UnicodeDecodeError`; the delimiter is sniffed too.
Unreadable files raise a client-safe message instead of a traceback. Streamlit uploads
are capped at 200 MB in `.streamlit/config.toml` — larger files go through the CLI.

Ambiguous dates such as `04/03/2026` are **not** guessed when you say otherwise: set
`--date-order dayfirst|monthfirst` on the CLI, `date_dayfirst` in the cleaning config,
or the sidebar selector in the app. The default (`auto`) only infers day-first when the
first component cannot be a month.

## White-labelling

Edit `branding.yaml`, or set `BRAND_NAME`, `LOGO_URL`, `BRAND_FOOTER_NOTE` and
`BRAND_ACCENT_COLOUR`, which override the file. Both the QA report and the audit report
pick the values up.

## Other CRMs

Zoho, Keap, Monday.com and anything else need one YAML file, no code: see
[docs/CUSTOM_CRM_MAPPING.md](docs/CUSTOM_CRM_MAPPING.md) and
[../delivery_kit/mapping_template.yaml](../delivery_kit/mapping_template.yaml).

## Client delivery

`../delivery_kit/` holds the client-facing README and mapping template;
`../delivery_kit/build_kit.sh` zips the tool plus those files for handover.

## Deliverables

| File | Contents |
| --- | --- |
| `clean_data.csv` | Import-ready file in the target CRM's column layout |
| `mapping_log.csv` | Target field, source column, match type, confidence, transform |
| `cleaning_log.csv` | Every cleaning action and how many records it touched |
| `issues.csv` | Row-level issues with a recommended fix |
| `qa_report.html` | Quality score, check summary, issues, mapping, sample records |
| `audit_report.html` + `audit_mismatches.csv` | Optional post-import comparison |

## Components

### Cleaner (`cleaners/`)

Configuration driven, with no hardcoded column names: each column's role
(email / phone / date / numeric / identifier / text) is inferred from its header and its
values, and can be overridden in a YAML config.

| Issue | Before | After |
| --- | --- | --- |
| Date formats | `12/31/24`, `31-Dec-24` | `2024-12-31` |
| Phone numbers | `(555) 123-4567`, `555.123.4567` | `+15551234567` |
| Excel scientific notation | `4.05E+14` | `405000000000000` |
| Whitespace | `"  John   Smith "` | `"John Smith"` |
| Email case | `JOHN@Email.com` | `john@email.com` |
| Duplicates / missing values | duplicated rows, blanks | deduplicated; blanks flagged, filled or dropped |

```yaml
# cleaning.yaml
pipeline:
  cleaning:
    remove_duplicates: true
    missing_value_strategy: auto   # flag | auto | drop
    date_format: "%Y-%m-%d"
    default_region: US             # phone region for national-format numbers
    normalize_unicode: false
    phone_columns: ["Phone 1"]     # optional explicit roles
```

```bash
python -m data_migration_tool.cli -i raw.csv -c hubspot --cleaning-config cleaning.yaml
```

### Mapper (`mappers/`, `configs/`)

Each target CRM is a YAML template listing its fields, aliases and per-field transforms.
A source column is matched to a target field by alias, then by fuzzy name match; anything
unmatched is reported in the mapping log rather than silently dropped.

```yaml
crm: HubSpot
fields:
  - name: email
    required: true
    unique: true
    transform: email_lowercase
    aliases: ["Email Address", "E-mail", "Primary Email"]
  - name: Name            # several source columns can feed one field
    sources: ["First Name", "Last Name"]
    separator: " "
```

Ships with `hubspot`, `salesforce` and `pipedrive`; add a CRM by dropping a YAML file into
`configs/`, or pass a path to any config with `-c path/to/config.yaml`.
Available transforms: `phone_e164`, `email_lowercase`, `date_iso`, `trim`, `title_case`,
`upper_case`, `lower_case`, `digits_only`, `ascii`, `expand_scientific_notation`.

### Validator (`validators/`)

Checks completeness (required fields), uniqueness, validity (emails via pattern, phones via
`phonenumbers`, dates against the target format) and consistency, and runs a structural check
over the output file with Frictionless. The quality score is the share of records with no
error and no warning.

### Post-import auditor (`auditors/`)

```bash
python -m data_migration_tool.cli -i raw.csv -c hubspot \
  --audit-export exported_from_crm.csv --audit-key email
```

Diffs the delivered file against the client's post-import export on a key column and reports
missing records, unexpected records and per-field value mismatches.

## Development

```bash
pip install -r requirements-dev.txt
pytest                     # from data_migration_tool/
ruff check .
mypy .                     # run as `mypy data_migration_tool` from the repository root
```
