#!/bin/bash

# List all Python virtual environments in the project

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_VENV="${VIRTUAL_ENV##*/}"

echo "📦 Python Virtual Environments in $PROJECT_ROOT"
echo ""

found_any=false

while IFS= read -r venv_path; do
    project_name=$(basename "$(dirname "$venv_path")")
    venv_name=$(basename "$venv_path")
    is_active=""

    if [ "$VIRTUAL_ENV" == "$venv_path" ]; then
        is_active=" (✅ ACTIVE)"
    fi

    # Get Python version
    if [ -f "$venv_path/bin/python" ]; then
        python_version=$("$venv_path/bin/python" --version 2>&1)
    else
        python_version="unknown"
    fi

    echo "📍 $project_name/$venv_name$is_active"
    echo "   Location: $venv_path"
    echo "   Python: $python_version"
    echo ""

    found_any=true
done < <(find "$PROJECT_ROOT" -maxdepth 3 -name "venv" -type d 2>/dev/null)

if [ "$found_any" = false ]; then
    echo "❌ Keine Virtual Environments gefunden"
    echo ""
    echo "Setup durchführen mit:"
    echo "  task sim:install"
    echo "  task ml:install"
else
    echo "💡 Tipps:"
    echo "  Aktivieren:   source <path>/bin/activate"
    echo "  Deaktivieren: deactivate"
    echo "  Aktuell aktiv: $CURRENT_VENV"
fi
