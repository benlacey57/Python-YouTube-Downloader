#!/bin/bash

# --- Configuration and Defaults ---
# Default output file name
OUTPUT_FILE="../structure.txt"

# Default directories/patterns to exclude
EXCLUDES="--exclude=logs --exclude=__pycache__ --exclude=.git --exclude=*.pyc"

# --- Functions ---

# Function to display help menu
show_help() {
    echo "Usage: ./structure.sh [OPTIONS]"
    echo ""
    echo "Generates a list of files and folders in the current directory, saving the output to a file."
    echo ""
    echo "Options:"
    echo "  -o, --output <file>   Specify the output file name (Default: $OUTPUT_FILE)"
    echo "  -e, --exclude <dirs>  Comma-separated list of directories/patterns to exclude (e.g., tests,temp)"
    echo "  -t, --tree            Use the 'tree' command for a graphical view (requires 'tree' installed)"
    echo "  -f, --find            Use the 'find' command for a simple path list (Default)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Example:"
    echo "  ./structure.sh --output code_structure.txt --exclude tests,venv"
}

# Function to parse arguments
parse_args() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -o|--output)
                if [ -n "$2" ]; then
                    OUTPUT_FILE="$2"
                    shift
                else
                    echo "Error: Option $1 requires an argument." >&2
                    exit 1
                fi
                ;;
            -e|--exclude)
                if [ -n "$2" ]; then
                    # Convert comma-separated list into the format needed for 'find'
                    EXCLUDES=$(echo "$2" | sed 's/[^, ]\+/\0\//g' | sed 's/,/ -or -path .//g')
                    EXCLUDES="-not -path ./${EXCLUDES} -not -path ./${EXCLUDES%/*}"
                    shift
                else
                    echo "Error: Option $1 requires an argument." >&2
                    exit 1
                fi
                ;;
            -t|--tree)
                COMMAND_TYPE="tree"
                ;;
            -f|--find)
                COMMAND_TYPE="find"
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "Error: Unknown option $1" >&2
                show_help
                exit 1
                ;;
        esac
        shift
    done
}

# --- Main Execution ---
cd ../

# Set default command type
COMMAND_TYPE="find"

# Parse command line arguments
parse_args "$@"

echo "--- Generating project structure listing ---"
echo "Output file: $OUTPUT_FILE"

# Run the appropriate command based on selection
if [ "$COMMAND_TYPE" == "tree" ]; then
    # Check if 'tree' is installed
    if ! command -v tree &> /dev/null; then
        echo "Error: 'tree' command not found. Please install it or use the default '--find' option." >&2
        exit 1
    fi

    # Tree command logic (cannot easily use find's exclude format)
    echo "Using 'tree' command for graphical output (Excludes are approximate)."
    tree -I ".git|__pycache__|logs|*pyc" > "$OUTPUT_FILE"

elif [ "$COMMAND_TYPE" == "find" ]; then
    # Default 'find' command logic
    echo "Using 'find' command for path list."

    # Initial universal excludes
    FIND_EXCLUDES="-not -path './.git/*' -not -path '*/__pycache__/*'"

    # Combine initial and user-defined excludes (if user provided -e, it overrides defaults)
    if [ "$EXCLUDES" != "" ]; then
        FIND_EXCLUDES="$FIND_EXCLUDES $(echo "$EXCLUDES" | sed 's/ / -not -path /g')"
    fi
    
    # Construct the full find command
    FIND_CMD="find . $FIND_EXCLUDES -print"

    # Execute and redirect to output file
    eval "$FIND_CMD" > "$OUTPUT_FILE"

else
    echo "Error: Invalid command type." >&2
    exit 1
fi

echo "Successfully saved folder structure to $OUTPUT_FILE"
echo "----------------------------------------------------"
