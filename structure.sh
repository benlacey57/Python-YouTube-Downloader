#!/bin/bash

# --- Configuration ---
OUTPUT_FILE="PROJECT_STRUCTURE.txt"
COMMIT_MESSAGE="Docs: Update project structure tree view"
GIT_DIR=".git"

# --- Utility Functions ---

# Function to check if a command exists
command_exists () {
    command -v "$1" >/dev/null 2>&1
}

# Function to display messages in green
success() {
    echo -e "\033[0;32m✓ $1\033[0m"
}

# Function to display warnings in yellow
warning() {
    echo -e "\033[0;33m⚠ $1\033[0m"
}

# Function to display errors in red
error() {
    echo -e "\033[0;31m✗ $1\033[0m"
}


# --- Main Script Logic ---

echo "--- Directory Tree Generation Script ---"

# 1. Check for 'tree' command availability
if ! command_exists tree; then
    error "The 'tree' command is required but not installed."
    error "Please install it (e.g., 'sudo apt install tree' or 'brew install tree')."
    exit 1
fi
success "Dependency 'tree' found."


# 2. Generate the directory tree view and save it to the output file
warning "Generating directory tree view and saving to '$OUTPUT_FILE'..."
# The 'tree -a' command includes hidden files like .git but excludes the output file itself
# We exclude the venv directory which is typically large and noisy
tree -a -I 'venv|__pycache__|node_modules' -o "$OUTPUT_FILE"
if [ $? -eq 0 ]; then
    success "Tree structure successfully saved to '$OUTPUT_FILE'."
else
    error "Failed to generate tree structure."
    exit 1
fi


# 3. Check if we are inside a Git repository
if [ -d "$GIT_DIR" ]; then
    warning "Git repository detected. Proceeding with auto-commit..."

    # a. Stage the generated file
    git add "$OUTPUT_FILE"
    
    # Check if there are changes to commit (0 means staged changes exist)
    if git diff --cached --exit-code > /dev/null; then
        warning "No changes detected for '$OUTPUT_FILE' since the last commit. Skipping commit."
        exit 0
    fi

    # b. Commit the change
    git commit -m "$COMMIT_MESSAGE"
    if [ $? -eq 0 ]; then
        success "Committed changes with message: '$COMMIT_MESSAGE'"
    else
        error "Git commit failed. Manual intervention may be needed."
        exit 1
    fi

    # c. Push the commit
    warning "Attempting to push changes to remote..."
    # Get the current branch name
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # Try to push to origin/current-branch
    git push origin "$CURRENT_BRANCH"
    if [ $? -eq 0 ]; then
        success "Successfully pushed '$OUTPUT_FILE' update to origin/$CURRENT_BRANCH."
    else
        error "Git push failed. You may need to authenticate or set up tracking."
        error "Run 'git push' manually to resolve."
    fi

else
    warning "No .git directory found. Skipping commit and push."
fi

echo "--- Script Finished ---"
