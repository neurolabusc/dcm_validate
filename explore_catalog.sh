#!/bin/bash
#
# Interactive Catalog Explorer for dcm_validate
#
# This script provides easy access to catalog exploration tools:
# - VisiData: Fast terminal-based CSV viewer
# - Datasette: Web-based SQLite browser with search and SQL queries
#
# Author: Roger Newman-Norlund (2025)
# License: BSD-2-Clause license (see included file "LICENSE")

set -e

# Configuration
CATALOG_DIR="catalogs"
COMBINED_CATALOG="$CATALOG_DIR/all_datasets.csv"
DB_FILE="$CATALOG_DIR/catalogs.db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Check if catalogs exist
check_catalogs() {
    if [ ! -d "$CATALOG_DIR" ]; then
        print_msg "$RED" "Error: catalogs/ directory not found."
        print_msg "$YELLOW" "Run 'python generate_all_catalogs.py' first to generate catalogs."
        exit 1
    fi

    if [ ! -f "$COMBINED_CATALOG" ]; then
        print_msg "$RED" "Error: $COMBINED_CATALOG not found."
        print_msg "$YELLOW" "Run 'python generate_all_catalogs.py' first to generate catalogs."
        exit 1
    fi
}

# Function to launch VisiData
launch_visidata() {
    if ! command_exists vd; then
        print_msg "$RED" "VisiData not installed."
        print_msg "$YELLOW" "Install with: pip install visidata"
        exit 1
    fi

    print_msg "$GREEN" "Launching VisiData..."
    print_msg "$BLUE" "Tip: Press 'h' for help, 'q' to quit"
    vd "$COMBINED_CATALOG"
}

# Function to convert CSV to SQLite
csv_to_sqlite() {
    if ! command_exists sqlite-utils; then
        print_msg "$RED" "sqlite-utils not installed."
        print_msg "$YELLOW" "Install with: pip install sqlite-utils"
        exit 1
    fi

    print_msg "$GREEN" "Converting catalogs to SQLite database..."

    # Remove existing database if present
    rm -f "$DB_FILE"

    # Import all CSV files
    for csv_file in "$CATALOG_DIR"/*.csv; do
        if [ -f "$csv_file" ]; then
            table_name=$(basename "$csv_file" .csv)
            print_msg "$BLUE" "  Importing $(basename "$csv_file") -> table '$table_name'"
            sqlite-utils insert "$DB_FILE" "$table_name" "$csv_file" --csv
        fi
    done

    print_msg "$GREEN" "✓ Database created: $DB_FILE"
}

# Function to launch Datasette
launch_datasette() {
    if ! command_exists datasette; then
        print_msg "$RED" "Datasette not installed."
        print_msg "$YELLOW" "Install with: pip install datasette"
        exit 1
    fi

    # Convert to SQLite if needed
    if [ ! -f "$DB_FILE" ]; then
        csv_to_sqlite
    fi

    print_msg "$GREEN" "Launching Datasette web interface..."
    print_msg "$BLUE" "Opening http://localhost:8001 in your browser"
    print_msg "$BLUE" "Press Ctrl+C to stop the server"
    echo ""

    datasette serve "$DB_FILE" --port 8001 --open
}

# Main menu
show_menu() {
    echo ""
    print_msg "$GREEN" "╔═══════════════════════════════════════════════╗"
    print_msg "$GREEN" "║   dcm_validate Catalog Explorer              ║"
    print_msg "$GREEN" "╚═══════════════════════════════════════════════╝"
    echo ""
    print_msg "$BLUE" "Select exploration tool:"
    echo ""
    echo "  1) VisiData        - Terminal-based interactive viewer"
    echo "  2) Datasette       - Web-based SQLite browser (recommended)"
    echo "  3) Convert to DB   - Convert CSV to SQLite only (no viewer)"
    echo "  4) Exit"
    echo ""
}

# Main script
main() {
    check_catalogs

    # If argument provided, use direct mode
    if [ $# -gt 0 ]; then
        case "$1" in
            1|vd|visidata)
                launch_visidata
                ;;
            2|datasette|web)
                launch_datasette
                ;;
            3|db|convert)
                csv_to_sqlite
                ;;
            *)
                print_msg "$RED" "Invalid option: $1"
                print_msg "$YELLOW" "Usage: $0 [1|2|3]"
                exit 1
                ;;
        esac
        exit 0
    fi

    # Interactive mode
    while true; do
        show_menu
        read -p "Enter choice [1-4]: " choice

        case $choice in
            1)
                launch_visidata
                break
                ;;
            2)
                launch_datasette
                break
                ;;
            3)
                csv_to_sqlite
                break
                ;;
            4)
                print_msg "$GREEN" "Goodbye!"
                exit 0
                ;;
            *)
                print_msg "$RED" "Invalid choice. Please select 1-4."
                sleep 1
                ;;
        esac
    done
}

main "$@"
