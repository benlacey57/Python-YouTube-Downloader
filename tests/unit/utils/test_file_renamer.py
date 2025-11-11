import pytest

# --- FIX FOR PACKAGE IMPORTS ---
# This ensures Python can find 'managers', 'utils', 'models', etc.
# when the script is run from the root directory.
import sys
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# -------------------------------

from ...utils.file_renamer import FileRenamer


# --- Test normalize_title ---

@pytest.mark.parametrize("title, expected, case_sensitive", [
    # Basic cleaning and whitespace
    (" My Cool Video ", "My cool video", True),
    ("Title with    lots of space", "Title with lots of space", True),
    # Special characters removal and replacement
    ("Video: Title? / Slash", "Video Title Slash", True),
    ("Title-with_hyphen's", "Title-with_hyphen's", True),
    # Unicode and Emojis
    ("Video title áéíóú 🔥", "Video title aeiou", True),
    # Acronyms and case
    ("HOW TO USE PYTHON AND SQL", "How to use PYTHON and SQL", True), # SQL kept due to isupper check
    ("Title with ACRONYM and a word", "Title with ACRONYM and a word", True),
    # Sentence case disabled
    ("Title with ACRONYM and a word", "Title with ACRONYM and a word", False),
    # Leading/trailing hyphens/spaces
    (" - Test title - ", "Test title", True),
])
def test_normalize_title(title, expected, case_sensitive):
    """Test various aspects of title normalization and case handling."""
    result = FileRenamer.normalize_title(title, sentence_case=case_sensitive)
    assert result == expected


# --- Test sanitize_filename ---

@pytest.mark.parametrize("filename, normalize, expected", [
    # Basic sanitation (with normalization)
    ("Test <file> / path: name.mp4", True, "Test file path name"),
    # Invalid characters removal (without normalization)
    ("File/Path*?|<>:", False, "FilePath"),
    # Emojis removal (without normalization)
    ("Video title 🚀", False, "Video title "),
    # Max length limit (200 chars)
    ("A" * 250, True, ("A" * 200).strip()),
    # Trailing dot/space removal
    ("File Name. ", False, "File Name"),
])
def test_sanitize_filename(filename, normalize, expected):
    """Test removing invalid filesystem characters and handling normalization flag."""
    result = FileRenamer.sanitize_filename(filename, normalize=normalize)
    assert result == expected


# --- Test apply_template ---

@pytest.mark.parametrize("template, title, uploader, index, playlist, normalize, expected_output", [
    # Basic template application
    ("{index} - {title}", "My Video", "Uploader", 10, "", True, "10 - My Video"),
    # Template with format specifier
    ("{index:03d} - {title}", "My Video", "Uploader", 5, "", True, "005 - My Video"),
    # Template with multiple placeholders (including normalized values)
    ("{playlist} by {uploader} ({date})", "Title", "Dr. E", 1, "The Series", True, "The Series by Dr E (Unknown)"),
    # Template output requires final sanitization (normalize=False)
    ("{index:02d} - {title}:?/\\", "Video", "Uploader", 1, "", False, "01 - Video"),
    # Check normalization flag impacts placeholder value creation
    ("{title}", "ALL CAPS", "Uploader", 1, "", True, "All caps"),
    ("{title}", "ALL CAPS", "Uploader", 1, "", False, "ALL CAPS"),
])
def test_apply_template(template, title, uploader, index, playlist, normalize, expected_output):
    """Test applying templates, including format specifiers and final sanitization."""
    # Note: We rely on sanitize_filename's mock for testing normalize=False on final output
    # but the internal recursive calls to sanitize_filename for placeholders use the 'normalize' flag.

    result = FileRenamer.apply_template(
        template=template,
        title=title,
        uploader=uploader,
        upload_date="Unknown",
        index=index,
        playlist_title=playlist,
        video_id="ID",
        normalize=normalize
    )
    assert result == expected_output
