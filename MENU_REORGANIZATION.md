# Menu Reorganization and Proxy Rotation Implementation

## Overview
This document describes the completed menu reorganization and proxy rotation implementation for the YouTube Playlist Downloader.

## Changes Completed

### 1. Menu Structure Reorganization

The main menu has been reorganized from a flat list of 20+ items into a logical hierarchy:

#### New Main Menu Structure
```
YouTube Playlist Downloader
============================
📥 Downloads
  1. Build New Queue
  2. Process Queues
  3. Resume Interrupted Queue

📊 Monitoring & Stats  
  4. View Statistics
  5. View Download Queue

⚙️ Configuration
  6. Download Settings
  7. Network Settings
  8. Notification Settings

🔧 System
  9. System Info
  10. Exit
```

### 2. New Submenu Files Created

#### Download Settings Menu (`ui/download_settings_menu.py`)
- Default Quality Settings
- Parallel Downloads Configuration
- Download Timeout Settings
- Filename Template Configuration
- Filename Normalization Toggle
- Live Stream Settings
- Authentication Configuration

#### Network Settings Menu (`ui/network_settings_menu.py`)
- Add Proxy
- Remove Proxy
- List All Proxies
- Test Proxies
- Toggle Proxy Rotation (Enable/Disable)
- Configure Rotation Frequency
- Rate Limiting Configuration
- Bandwidth Limiting

#### Notification Settings Menu (`ui/notification_settings_menu.py`)
- Configure Slack Notifications
- Configure Email Notifications
- Toggle Notification Providers
- Configure Notification Preferences (what events trigger notifications)
- Configure Alert Thresholds (file size alerts)

### 3. Config Manager Enhancements

#### New AppConfig Fields
```python
# Proxy rotation settings
proxy_rotation_enabled: bool = False
proxy_rotation_frequency: int = 10  # Change proxy every X downloads
```

#### Field Migration
- Migrated `download_timeout_seconds` (int) → `download_timeout_minutes` (int)
- Automatic conversion during config load: seconds / 60 = minutes
- Default changed from 300 seconds → 120 minutes for better UX

#### New/Alias Methods
- `configure_parallel_downloads()` - Alias for `configure_workers()`
- `manage_proxies()` - Delegates to NetworkSettingsMenu
- `configure_slack_webhook()` - Alias for `configure_slack()`

### 4. Proxy Rotation Implementation

#### Display During Downloads
When downloading a queue, the header now shows proxy status:
- **No proxies configured**: `⚠ No proxies configured` (yellow warning)
- **Proxies with rotation disabled**: `Proxy: http://proxy1.example.com:8080`
- **Proxies with rotation enabled**: `Proxy Rotation: Enabled (every 10 downloads)`

#### Rotation Logic
In `downloaders/playlist.py`:
```python
if rotation_enabled:
    # Calculate which proxy to use based on download count and frequency
    proxy_index = (download_count // config.proxy_rotation_frequency) % len(proxies)
    current_proxy = config.proxies[proxy_index]
    download_count += 1
    # Display which proxy is being used
    progress.console.print(f"[dim]Using proxy: {current_proxy}[/dim]")
```

**Rotation behavior:**
- Downloads 1-10: Use proxy[0]
- Downloads 11-20: Use proxy[1]
- Downloads 21-30: Use proxy[2] (or cycle back to proxy[0] if only 2 proxies)
- And so on...

### 5. Wait Time Logic
Random delays between downloads are only applied when **no proxies are configured**:
```python
if not has_proxies:
    wait_time = random.uniform(
        config.min_delay_seconds,
        config.max_delay_seconds
    )
    progress.console.print(f"[dim]Waiting {wait_time:.1f}s before next download...[/dim]")
    time.sleep(wait_time)
```

When proxies are configured (with or without rotation), downloads proceed without artificial delays.

## Files Modified

### Core Files
1. `managers/config_manager.py`
   - Added proxy rotation fields to AppConfig
   - Added field migration logic for download_timeout
   - Added new config methods and aliases

2. `downloaders/playlist.py`
   - Added imports: `time`, `random`, `Table`
   - Added proxy rotation logic in `download_queue()`
   - Added proxy status display in download header
   - Updated wait time logic to respect proxy configuration

3. `ui/menu.py`
   - Reorganized main menu into categories with emojis
   - Added routing to new submenus
   - Added helper methods for submenus

### New Files
1. `ui/download_settings_menu.py` - Download configuration submenu (206 lines)
2. `ui/network_settings_menu.py` - Network and proxy configuration submenu (356 lines)
3. `ui/notification_settings_menu.py` - Notification configuration submenu (164 lines)

## Usage Examples

### Enabling Proxy Rotation
1. Main Menu → `7. Network Settings`
2. Network Settings → `1. Add Proxy` (add multiple proxies)
3. Network Settings → `5. Toggle Proxy Rotation` (enable it)
4. Network Settings → `6. Configure Rotation Frequency` (set to desired value, e.g., 10)
5. Build and process a queue - proxies will rotate automatically

### Viewing Proxy Status During Downloads
When processing a queue, the download header will show:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Downloading: My Playlist Name
Format: video | Quality: 720p | Storage: local
Proxy Rotation: Enabled (every 10 downloads)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/50] Video Title Here
Using proxy: http://proxy1.example.com:8080
✓ Downloaded successfully
```

### Testing Proxies
1. Main Menu → `7. Network Settings`
2. Network Settings → `4. Test Proxies`
3. System will test each proxy with a quick YouTube request

## Configuration File Changes

After the migration, your `downloader_config.json` will have:
- `download_timeout_minutes` instead of `download_timeout_seconds`
- `proxy_rotation_enabled` (new field, default: false)
- `proxy_rotation_frequency` (new field, default: 10)

Old configs are automatically migrated on first load.

## Benefits of Reorganization

1. **Better UX**: Logical grouping makes features easier to find
2. **Scalability**: Easy to add new features to existing submenus
3. **Visual Hierarchy**: Emojis and categories provide clear navigation
4. **Reduced Clutter**: Main menu has 10 options instead of 20+
5. **Contextual Help**: Related settings are grouped together

## Proxy Rotation Benefits

1. **Avoid Rate Limits**: Distribute requests across multiple proxies
2. **Prevent IP Bans**: Reduce load on any single proxy/IP
3. **Visibility**: Always know which proxy is in use
4. **Flexibility**: Easy to enable/disable and adjust frequency
5. **Smart Logic**: Only applies delays when proxies aren't configured

## Testing Checklist

- [x] Config migration (timeout field) works correctly
- [x] New config fields load with proper defaults
- [x] Proxy rotation fields added to AppConfig
- [x] ConfigManager methods created/aliased
- [x] Playlist downloader shows proxy status in header
- [x] Proxy rotation logic implements correctly
- [ ] Full menu navigation test (requires yt_dlp installation)
- [ ] Proxy rotation test with actual proxies
- [ ] NetworkSettingsMenu proxy management functions

## Future Enhancements

1. **Proxy Health Monitoring**: Track success/failure rates per proxy
2. **Auto-disable Bad Proxies**: Remove proxies that fail repeatedly
3. **Proxy Pools**: Support for proxy provider APIs
4. **Geographic Distribution**: Show proxy locations
5. **Performance Metrics**: Track download speeds per proxy
