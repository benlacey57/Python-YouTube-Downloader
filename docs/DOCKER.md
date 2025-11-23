🐳 Development Environment Setup
This project uses a VS Code Dev Container to ensure a consistent, reproducible, and fully-equipped development environment across all platforms. This setup automatically includes essential system dependencies like ffmpeg and configures VS Code with strict code quality standards.
The configuration files are located in the docker/ directory.
Directory Structure
docker/
├── Dockerfile                  # Builds the base environment
├── devcontainer.json           # VS Code configuration for the container
└── settings.json               # VS Code settings override (theme, formatting, linting)

1. Prerequisites (Docker and VS Code)
To use the Dev Container, you must have the following installed:
 * ** Docker Desktop:** For running containers.
 * Visual Studio Code (VS Code).
 * VS Code Dev Containers Extension: Install the official extension from Microsoft.
2. Getting Started
 * Open Project in VS Code: Open the project root folder.
 * Reopen in Container: VS Code will detect the devcontainer.json file and prompt you to "Reopen in Container." Click this prompt.
 * The first time you do this, Docker will build the image defined in Dockerfile, which may take a few minutes.
3. Environment Details
The docker/Dockerfile provides the foundation for the environment:
 * Base OS: debian:bullseye-slim.
 * Python: Python 3 is installed.
 * FFmpeg: FFmpeg is installed globally (Crucial for yt-dlp to merge and process audio/video files).
 * User: A non-root user (devuser) is created for secure development practices.
4. Development Standards and Tools
The devcontainer.json and settings.json enforce the following code quality standards and setup:
| Category | Tool | Enforced Standard | settings.json Key |
|---|---|---|---|
| Theme | Shades of Purple | High-contrast, custom color theme. | workbench.colorTheme |
| Formatting | Black | Uncompromising code formatting on every save (line length 100). | editor.formatOnSave |
| Linting | Flake8 | Enforces code style consistency and common error checking. | python.linting.flake8Enabled |
| Imports | Isort | Automatically organizes imports alphabetically on save. | source.organizeImports |
| Type Checking | Mypy | Runs static analysis to check for type errors. | mypy-type-checker.enabled |
| Security | Safety | Runs a dependency scan upon terminal launch to check for known vulnerabilities. | terminal.integrated.profiles.linux |
Key Setting: Format on Save
The most impactful setting is automatically applied:
"editor.formatOnSave": true,
"editor.codeActionsOnSave": {
    "source.fixAll": "explicit",
    "source.organizeImports": "explicit"
}

