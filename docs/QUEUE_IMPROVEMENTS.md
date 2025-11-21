# Queue Builder Improvements

## Overview
Significant improvements have been made to the queue creation and download process to handle large playlists better and provide cleaner output.

## Changes Made

### 1. Suppressed yt-dlp Verbose Output ✨

**Problem:**
When fetching playlist information, yt-dlp was showing verbose output like:
```
[youtube:tab] Extracting URL: https://www.youtube.com/...
[youtube:tab] Downloading playlist PL...
[download] Downloading playlist: Music
[download] Downloading item 1 of 638
[download] Downloading item 2 of 638
...
```

This output was confusing because:
- It appeared before asking for format type
- It made users think files were being downloaded
- Nothing was actually in the downloads folder yet

**Solution:**
- Set `quiet=True` and `no_warnings=True` in yt-dlp options for playlist info fetching
- Added stdout capture during playlist info fetch
- Clean output now shows only:
  ```
  Fetching playlist information...
  ✓ Found playlist: Music
    Total videos: 638
  ```

### 2. Batch Download Support 📦

**Problem:**
Large playlists (hundreds or thousands of videos) would:
- Take too long to download all at once
- Risk interruption and data loss
- No way to download in manageable chunks

**Solution:**
Added intelligent batch download feature:

#### Automatic Detection
- Playlists with >50 items trigger batch mode prompt
- Suggests downloading 25% of playlist at a time
- Example: 638-item playlist suggests 160 items per batch

#### User Control
```
Step 5: Batch Settings

ℹ Large playlist detected (638 items)
Suggested batch size: 160 items (25% of playlist)

Download in batches? [Y/n]: y
Batch size (1-638) [160]: 100
Start from item # (0-538) [0]: 0

✓ Will download items 1 to 100
```

#### Features
- Choose custom batch size
- Start from any position in playlist
- Resume from where you left off
- Perfect for testing or gradual downloads

### 3. Random Wait Times Between Downloads ⏱️

**Problem:**
- Rapid sequential downloads could trigger rate limiting
- No delays between items risked IP blocks
- Especially important when no proxies configured

**Solution:**
Implemented intelligent wait times:

#### Configuration-Based
Uses existing rate limit settings from config:
- `min_delay_seconds` (default: 2.0s)
- `max_delay_seconds` (default: 5.0s)

#### Smart Behavior
- **With proxies configured:** No wait (proxies rotate)
- **Without proxies:** Random wait between each download
- Wait time randomized to appear more human
- Example: "Waiting 3.7s before next download..."

#### Output
```
[1/100] Video Title
✓ Downloaded successfully
Waiting 4.2s before next download...

[2/100] Another Video
✓ Downloaded successfully
Waiting 2.8s before next download...
```

### 4. Improved Status Messages 📊

**Before:**
```
Adding videos to queue...
✓ Added 638 videos to queue
```

**After:**
```
Adding videos to queue...
Processing batch: items 1 to 100
✓ Added 100 videos to queue
```

**Features:**
- Shows exact range being processed
- Uses thousand separators for large numbers (1,234)
- Clear batch boundaries
- Progress visibility

---

## Usage Examples

### Example 1: Small Playlist (No Batching)
```
Step 1: Playlist Information
Enter playlist URL: https://youtube.com/playlist?list=...

Fetching playlist information...
✓ Found playlist: My Favorites
  Total videos: 25

Step 2: Download Format
Format type [video/audio] (video): audio

Step 3: Quality Settings
Audio quality (kbps) [320/256/192/128] (192): 

[continues normally...]
```

### Example 2: Large Playlist (With Batching)
```
Step 1: Playlist Information
Enter playlist URL: https://youtube.com/playlist?list=...

Fetching playlist information...
✓ Found playlist: Complete Collection
  Total videos: 1,245

[... format and quality settings ...]

Step 5: Batch Settings

ℹ Large playlist detected (1,245 items)
Suggested batch size: 312 items (25% of playlist)

Download in batches? [Y/n]: y
Batch size (1-1245) [312]: 50
Start from item # (0-1195) [0]: 0

✓ Will download items 1 to 50

[... storage settings ...]

✓ Queue created: Complete Collection

Adding videos to queue...
Processing batch: items 1 to 50
✓ Added 50 videos to queue
```

### Example 3: Continuing a Batch
```
Step 5: Batch Settings

ℹ Large playlist detected (1,245 items)
Suggested batch size: 312 items (25% of playlist)

Download in batches? [Y/n]: y
Batch size (1-1245) [312]: 50
Start from item # (0-1195) [0]: 50    ← Continue from where you left off

✓ Will download items 51 to 100
```

### Example 4: Download with Wait Times
```
[1/50] Amazing Video Title
✓ Downloaded successfully
Waiting 3.2s before next download...

[2/50] Another Great Video
✓ Downloaded successfully  
Waiting 4.7s before next download...

[3/50] Third Video
✓ Downloaded successfully
Waiting 2.1s before next download...
```

---

## Configuration

### Rate Limiting Settings
Edit your `config.json` or use Settings menu:

```json
{
  "min_delay_seconds": 2.0,
  "max_delay_seconds": 5.0,
  "max_downloads_per_hour": 50
}
```

**Recommendations:**
- **Conservative:** 3-8 seconds (safer, slower)
- **Balanced:** 2-5 seconds (default, good balance)
- **Aggressive:** 1-3 seconds (faster, riskier)

### Proxy Configuration
If you have proxies configured, wait times are skipped:

```json
{
  "proxies": [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080"
  ]
}
```

---

## Benefits

### 1. Better User Experience
- ✅ Clean, understandable output
- ✅ No confusing "downloading" messages
- ✅ Clear progress indicators
- ✅ Know exactly what's happening

### 2. Large Playlist Management
- ✅ Download in manageable chunks
- ✅ Test with small batches first
- ✅ Resume from any position
- ✅ Reduce risk of total failure

### 3. Rate Limiting Protection
- ✅ Automatic wait times
- ✅ Random delays appear human
- ✅ Configurable timing
- ✅ Smart proxy detection

### 4. Reduced Risk
- ✅ Less likely to trigger rate limits
- ✅ Batches limit impact of failures
- ✅ Can stop and resume easily
- ✅ Test before committing to full playlist

---

## Technical Details

### Batch Calculation
```python
# 25% of playlist (minimum 1)
suggested_batch = max(1, math.ceil(video_count * 0.25))
```

### Wait Time Calculation
```python
# Random wait between min and max delay
wait_time = random.uniform(
    config.min_delay_seconds,
    config.max_delay_seconds
)
```

### Stdout Suppression
```python
# Capture stdout to suppress yt-dlp output
old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    playlist_info = downloader.get_playlist_info(url)
finally:
    sys.stdout = old_stdout
```

---

## Best Practices

### For Small Playlists (<50 items)
- Download entire playlist at once
- Default settings work well
- Wait times prevent rate limiting

### For Medium Playlists (50-200 items)
- Use suggested 25% batch size
- Test first batch before continuing
- Monitor for rate limiting

### For Large Playlists (200+ items)
- Definitely use batching
- Start with smaller test batch (20-50)
- Increase batch size if stable
- Consider downloading overnight

### For Very Large Playlists (1000+ items)
- Use 50-100 item batches
- Download over multiple sessions
- Keep batch size manageable
- Monitor disk space

---

## Troubleshooting

### Issue: Still seeing yt-dlp output
**Solution:** Update to latest code, stdout capture is now in place

### Issue: Wait times too long/short
**Solution:** Adjust `min_delay_seconds` and `max_delay_seconds` in settings

### Issue: Want to skip wait times
**Solution:** Configure proxies or temporarily set `min_delay_seconds: 0`

### Issue: Batch size validation error
**Solution:** Ensure batch size is between 1 and total video count

### Issue: Lost track of position in playlist
**Solution:** Check queue viewer to see what was downloaded, calculate next start position

---

## Future Enhancements

Potential improvements:
- [ ] Remember last batch position per playlist
- [ ] Auto-calculate optimal batch size based on success rate
- [ ] Adaptive wait times based on response times
- [ ] Batch download resume from interruption
- [ ] Progress across multiple batches
- [ ] Estimated time for full playlist

---

## Migration Notes

### Existing Queues
- Old queues work as before
- New features apply to new queues only
- Re-create queue to use batch features

### Configuration
- No config changes required
- New features use existing rate limit settings
- All improvements are backward compatible

Enjoy the improved queue management! 🚀
