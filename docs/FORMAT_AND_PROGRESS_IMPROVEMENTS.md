# Format Selection & Progress Display Improvements

## Overview
Major improvements to format selection, download progress display, and yt-dlp warning fixes.

## Changes Made

### 1. Enhanced Format Selection ✨

#### Video Formats
- **Available formats:** mp4, mkv, webm, avi
- **Default:** mp4
- **Prompt:** "Output format"

#### Audio Formats  
- **Available formats:** mp3, m4a, opus, flac, wav
- **Default:** mp3
- **Quality:** Uses default from config (no prompt)

#### New Workflow
**Before:**
```
Step 2: Download Format
Format type [video/audio]: audio

Step 3: Quality Settings
Audio quality (kbps) [320/256/192/128] (192): 
```

**After:**
```
Step 2: Download Format
Format type [video/audio]: audio

Step 3: Format & Quality Settings
Output format [mp3/m4a/opus/flac/wav] (mp3): mp3
Using default audio quality: 192 kbps
```

### 2. Fixed yt-dlp Warnings 🔧

#### Problems Fixed
1. **JavaScript Runtime Warning:**
   ```
   WARNING: [youtube] No supported JavaScript runtime could be found
   ```

2. **SABR Streaming Warnings:**
   ```
   WARNING: [youtube] Some web_safari client https formats have been skipped
   WARNING: [youtube] Some web client https formats have been skipped
   ```

#### Solution
Added to base yt-dlp options:
```python
'extractor_args': {'youtube': {'player_client': ['default']}}
```

This tells yt-dlp to use the default player client, avoiding the JavaScript runtime requirement and SABR streaming issues.

### 3. Prevented .meta File Downloads 🚫

#### Problem
yt-dlp was creating unnecessary metadata files:
- `.info.json` files
- `.description` files  
- `.annotations.xml` files
- Thumbnail files

#### Solution
Added to base yt-dlp options:
```python
'writethumbnail': False,
'writeinfojson': False,
'writedescription': False,
'writeannotations': False,
'writesubtitles': False,
```

### 4. System Dependencies Check 🔍

#### New Install.py Features
Checks for required system tools:

**ffmpeg:**
- Required for video/audio processing
- Install: `sudo apt install ffmpeg`

**Node.js:**
- Required for better YouTube extraction
- Install: `sudo apt install nodejs`

#### Installation Flow
```
═══════════════════════════════════════════════════════════════════════════
  System Requirements Check
═══════════════════════════════════════════════════════════════════════════

✓ Python version: 3.12.0

Checking system dependencies...
✓ ffmpeg: 4.4.2
✓ Node.js: v18.12.1
```

If missing:
```
⚠ Warning: Missing dependencies: ffmpeg, node

These are optional but recommended:
  • ffmpeg: Required for video/audio processing
    Install: sudo apt install ffmpeg (Ubuntu/Debian)
  • Node.js: Required for better YouTube extraction
    Install: sudo apt install nodejs (Ubuntu/Debian)

Continue anyway? [y/N]:
```

### 5. Improved Progress Display 📊

#### New Display Format
```
╔═══════════════════════════════════════════════════════════════╗
║ Downloading Queue                                             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║     Total: 100                                                ║
║ Completed: 45                                                 ║
║    Failed: 2                                                  ║
║   Pending: 53                                                 ║
║                                                               ║
║ 001 - Amazing Song Title ........................ Downloaded ║
║ 002 - Another Great Song ........................ Downloaded ║
║ 003 - Third Song ................................. Downloading║
║ 004 - Fourth Song ................................ Pending    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

#### Features
- **Overall stats panel:** Total, Completed, Failed, Pending counts
- **Single-line format:** Each item on one line with dots
- **Color-coded status:**
  - [green]Downloaded[/green] = Success
  - [red]Error[/red] = Failed  
  - [yellow]Downloading[/yellow] = In progress
  - [dim]Pending[/dim] = Waiting
- **Smart truncation:** Long titles truncated to fit
- **Index numbering:** 001, 002, 003 format

#### Old vs New

**Old:**
```
[1/100] Amazing Song Title
✓ Downloaded successfully

[2/100] Another Great Song  
✓ Downloaded successfully

[3/100] Third Song
✗ Failed: Network error
```

**New:**
```
[Progress Panel Showing Stats]

001 - Amazing Song Title .................... Downloaded
002 - Another Great Song ................... Downloaded
003 - Third Song ............................ Error: Network error
```

---

## Configuration

### Queue Model Updates
Added `file_format` field to Queue:
```python
@dataclass
class Queue:
    # ... existing fields ...
    file_format: str = "mp4"  # Output format
```

### Default Formats
- **Video:** mp4
- **Audio:** mp3

### Supported Formats

**Video:**
- mp4 (H.264, widely compatible)
- mkv (Matroska, high quality)
- webm (VP9, web optimized)
- avi (Legacy format)

**Audio:**
- mp3 (Most compatible)
- m4a (AAC, better quality)
- opus (Best compression)
- flac (Lossless)
- wav (Uncompressed)

---

## Usage Examples

### Example 1: Audio Download with Format Selection
```
Step 2: Download Format
Format type [video/audio] (video): audio

Step 3: Format & Quality Settings  
Output format [mp3/m4a/opus/flac/wav] (mp3): opus
Using default audio quality: 192 kbps

Step 4: Output Settings
Output directory (downloads/My_Playlist): 
...
```

### Example 2: Video Download with Format Selection
```
Step 2: Download Format
Format type [video/audio] (video): video

Step 3: Format & Quality Settings
Output format [mp4/mkv/webm/avi] (mp4): mkv
Video quality [best/1080p/720p/480p/360p] (720p): 1080p

Step 4: Output Settings
...
```

### Example 3: Download Progress
```
╭─────────────────────────────────────────╮
│ Progress                                │
├─────────────────────────────────────────┤
│     Total:  50                          │
│ Completed:  [green]25[/green]          │
│    Failed:  [red]1[/red]                │
│   Pending:  [yellow]24[/yellow]        │
╰─────────────────────────────────────────╯

001 - First Song .............................. [green]Downloaded[/green]
002 - Second Song ............................. [green]Downloaded[/green]
003 - Third Song .............................. [red]Error: Unavailable[/red]
004 - Fourth Song ............................. [yellow]Downloading[/yellow]
005 - Fifth Song .............................. [dim]Pending[/dim]

Waiting 3.2s...
```

---

## Benefits

### 1. Better Format Control
✅ Choose output format explicitly  
✅ Format-specific defaults (mp4/mp3)  
✅ No unnecessary quality prompts for audio  
✅ Wide format support  

### 2. Cleaner Output
✅ No confusing yt-dlp warnings  
✅ No .meta files cluttering directory  
✅ Clear progress visibility  
✅ Color-coded status  

### 3. Better Progress Tracking
✅ See overall stats at a glance  
✅ Track success/failure rates  
✅ Identify problematic downloads quickly  
✅ Single-line compact format  

### 4. Safer Installation
✅ Checks for required tools  
✅ Warns about missing dependencies  
✅ Provides installation instructions  
✅ Optional but recommended tools  

---

## Technical Details

### Format Storage
File format is now stored in the queue:
```python
queue = Queue(
    ...
    file_format="mp3",  # Stored with queue
    ...
)
```

### yt-dlp Options
```python
opts = {
    # Fix warnings
    'extractor_args': {'youtube': {'player_client': ['default']}},
    
    # Prevent metadata files
    'writethumbnail': False,
    'writeinfojson': False,
    'writedescription': False,
    'writeannotations': False,
    'writesubtitles': False,
}
```

### Progress Display Logic
```python
# Format: "001 - Title .......... Status"
display_title = title[:60] + "..." if len(title) > 60 else title
padding = "." * max(0, 70 - len(display_title) - len(str(idx)))
print(f"{idx:03d} - {display_title} {padding} {status}")
```

---

## Troubleshooting

### Issue: Still seeing yt-dlp warnings
**Solution:** Update to latest code, player_client fix is in place

### Issue: Wrong format downloaded
**Solution:** Check queue.file_format field, re-create queue if needed

### Issue: ffmpeg not found during download
**Solution:** Install ffmpeg: `sudo apt install ffmpeg`

### Issue: YouTube extraction errors
**Solution:** Install nodejs: `sudo apt install nodejs`

### Issue: .meta files still created
**Solution:** Update to latest code, metadata writing is disabled

---

## Migration Notes

### Existing Queues
- Old queues may not have `file_format` field
- Default to "mp4" for video, "mp3" for audio
- Consider re-creating old queues for format control

### Configuration
- No config changes required
- All improvements are backward compatible
- New queues automatically use new features

---

## Future Enhancements

Potential improvements:
- [ ] Custom format presets
- [ ] Format quality profiles
- [ ] Auto-format selection based on source
- [ ] Format conversion queue
- [ ] Batch format changes

Enjoy the improved format control and progress visibility! 🎉
