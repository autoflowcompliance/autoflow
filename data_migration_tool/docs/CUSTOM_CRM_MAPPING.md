# Adding your own CRM (Zoho, Keap, Monday.com, anything else)

The tool ships with HubSpot, Salesforce and Pipedrive. Any other CRM is one YAML
file — no code changes.

## 1. Get the target import template

Download the CRM's sample import file (every CRM offers one) and note the exact
column headers, in order. Those headers become your target fields.

## 2. Copy the template

```bash
cp delivery_kit/mapping_template.yaml data_migration_tool/configs/zoho.yaml
```

## 3. Fill in the fields

```yaml
crm: Zoho CRM
description: Zoho contacts import template

fields:
  - name: First Name          # exact header Zoho expects
    required: true
    aliases: ["fname", "Given Name"]
  - name: Email
    type: email
    required: true
    unique: true
    transform: email_lowercase
    aliases: ["Email Address", "E-mail"]
  - name: Phone
    type: phone
    transform: phone_e164
    aliases: ["Phone 1", "Telephone"]
```

Per-field options:

| Key | Meaning |
| --- | --- |
| `name` | Target column header, written exactly as the CRM expects it |
| `type` | `string`, `email`, `phone`, `date` or `number` (drives validation) |
| `required` | Empty values are reported as errors |
| `unique` | Duplicate values are reported as errors |
| `aliases` | Extra source header names to match on |
| `source` | Force one specific source column instead of matching |
| `sources` + `separator` | Combine several source columns into one field |
| `transform` | Value transform, see below |
| `default` | Value used when nothing matches |

Transforms: `phone_e164`, `email_lowercase`, `date_iso`, `trim`, `title_case`,
`upper_case`, `lower_case`, `digits_only`, `ascii`, `expand_scientific_notation`.

## 4. Matching rules (so you know what to expect)

For each target field the mapper tries, in order:

1. An exact match on the field name (case and punctuation insensitive).
2. An exact match on any alias.
3. A fuzzy match above 82% similarity — `Phone1` matches `phone`, `Notes` does not.

Anything unmatched is listed in the mapping log as dropped, so nothing
disappears silently. Read the mapping log after your first run and add aliases
for whatever was missed.

## 5. Use it

Streamlit picks the file up automatically from `configs/` after a restart.
From the CLI you can also point at a file anywhere:

```bash
python -m data_migration_tool.cli -i messy.csv -c configs/zoho.yaml -o output/
```

## 6. Check it worked

Open `output/mapping_log.csv` and confirm:

- every required target field has a source column,
- the `match_type` column is `exact` or `alias` for the important fields,
- the dropped-columns section contains nothing you needed.
