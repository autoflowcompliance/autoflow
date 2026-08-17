#!/usr/bin/env bash
# Package a client-ready zip: the tool, the client README and a mapping template.
# Usage: ./delivery_kit/build_kit.sh [output.zip]
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="${1:-$root/delivery_kit/data-migration-tool.zip}"
staging="$(mktemp -d)"
kit="$staging/data-migration-tool"

mkdir -p "$kit"
cp -r "$root/data_migration_tool" "$kit/data_migration_tool"
cp -r "$root/.streamlit" "$kit/.streamlit"
cp "$root/delivery_kit/README_CLIENT.md" "$kit/README.md"
cp "$root/delivery_kit/mapping_template.yaml" "$kit/mapping_template.yaml"
find "$kit" -type d \( -name __pycache__ -o -name .pytest_cache -o -name tests \) -prune -exec rm -rf {} +

rm -f "$output"
(cd "$staging" && zip -qr "$output" data-migration-tool)
rm -rf "$staging"
echo "Wrote $output"
