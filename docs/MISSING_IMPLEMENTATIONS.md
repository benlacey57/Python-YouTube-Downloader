# Missing Implementations and Issues

## Critical Issues

### 1. ❌ Proxy Rotation Not Actually Applied to Downloads
**Status**: Display works, but proxy is NOT rotated during actual downloads

**Problem**:
- In `downloaders/playlist.py`, the `current_proxy` variable is calculated and displayed
- However, this proxy is NEVER passed to the individual downloaders
- `VideoDownloader`, `AudioDownloader`, and `LiveStreamDownloader` all call `get_base_ydl_opts()` which always uses `config.proxies[0]` (the first proxy)
- The rotation logic only affects what is displayed to the user, not what proxy is actually used

**Location**: `downloaders/playlist.py:183` calls `download_item()` without passing proxy info

**Fix Required**:
```python
# Option 1: Modify get_base_ydl_opts to accept proxy parameter
def get_base_ydl_opts(self, proxy: Optional[str] = None) -> Dict[str, Any]:
    # ... existing code ...
    if proxy:
        opts['proxy'] = proxy
    elif self.config.proxies:
        opts['proxy'] = self.config.proxies[0]
    # ...

# Option 2: Temporarily modify config.proxies before calling download_item
# In playlist.py before download_item call:
if rotation_enabled and current_proxy:
    # Temporarily set first proxy to current_proxy
    original_proxies = config_manager.config.proxies.copy()
    config_manager.config.proxies = [current_proxy] + [p for p in original_proxies if p != current_proxy]
    item = self.download_item(item, queue, idx)
    config_manager.config.proxies = original_proxies
```

**Impact**: HIGH - Proxy rotation feature doesn't work at all for actual downloads

---

### 2. ⚠️ download_timeout Field Mismatch
**Status**: Partially fixed, but references still inconsistent

**Problem**:
- AppConfig has `download_timeout_minutes` (int, minutes)
- `base.py:65` references `download_timeout_seconds` which no longer exists
- This causes timeout to not be applied to downloads

**Location**: `downloaders/base.py:65-66`
```python
if self.config.download_timeout_seconds:  # ← This field doesn't exist!
    opts['socket_timeout'] = self.config.download_timeout_seconds
```

**Fix Required**:
```python
if self.config.download_timeout_minutes:
    opts['socket_timeout'] = self.config.download_timeout_minutes * 60  # Convert to seconds
```

**Impact**: MEDIUM - Download timeout is not applied, long videos may hang

---

## Minor Issues

### 3. ⚠️ Wrong Method Name in Download Settings Menu
**Status**: Method doesn't exist

**Problem**:
- `ui/download_settings_menu.py:51` calls `configure_download_timeout()`
- Actual method name is `configure_timeout()`

**Location**: `ui/download_settings_menu.py:51`

**Fix Required**:
```python
elif choice == "4":
    self.config_manager.configure_timeout()  # Remove "download_" prefix
```

**Impact**: LOW - Menu option will crash when selected

---

### 4. ℹ️ Duplicate Quality Configuration
**Status**: Not critical, just redundant

**Problem**:
- Both options 1 and 2 in Download Settings menu call the same method
- `configure_default_quality()` handles both video and audio quality together

**Location**: `ui/download_settings_menu.py:45-47`

**Fix Options**:
1. Remove one of the options
2. Split `configure_default_quality()` into separate video/audio methods
3. Keep as-is if intentional (both options do the same thing)

**Impact**: NONE - Functionality works, just confusing UX

---

### 5. ⚠️ BaseDownloader.__init__ Called in Wrong Order
**Status**: Logic error in constructor

**Problem**:
- In `PlaylistDownloader.__init__`, the `_print_stats()` method is defined
- Then `super().__init__()` is called INSIDE the `_print_stats()` method body
- This is a code structure issue

**Location**: `downloaders/playlist.py:35-54`

**Current (wrong)**:
```python
def _print_stats(self, stats: dict):
    # ... print code ...
    
    # Initialize base with config  ← This is in the wrong place!
    super().__init__(
        config_manager.config,
        self.stats_manager,
        self.notification_manager
    )
```

**Fix Required**:
```python
def __init__(self):
    # Get managers internally
    config_manager = ConfigManager()
    self.stats_manager = StatsManager()
    self.notification_manager = NotificationManager(config_manager.config)
    
    # Initialize base with config
    super().__init__(
        config_manager.config,
        self.stats_manager,
        self.notification_manager
    )
    
    # Initialize specialized downloaders
    self.video_downloader = VideoDownloader()
    self.audio_downloader = AudioDownloader()
    self.livestream_downloader = LiveStreamDownloader()

def _print_stats(self, stats: dict):
    # ... print code only ...
```

**Impact**: MEDIUM - May cause AttributeErrors or initialization issues

---

## Missing Features (Not Critical)

### 6. ℹ️ Proxy Testing Uses Wrong URL
**Status**: Works but not optimal

**Problem**:
- `network_settings_menu.py:159` tests proxies with Google
- Should test with YouTube since that's what we're downloading from

**Fix**:
```python
test_url = "https://www.youtube.com"  # Instead of google.com
```

**Impact**: LOW - Tests work but may not reflect actual YouTube proxy compatibility

---

### 7. ℹ️ NetworkSettingsMenu.__init__ Constructor Parameter Mismatch
**Status**: Inconsistent with other menus

**Problem**:
- `ui/menu.py:654-657` tries to pass `self` (ConfigManager) to NetworkSettingsMenu
- But `NetworkSettingsMenu.__init__` takes no parameters and creates its own ConfigManager

**Location**: 
- `managers/config_manager.py:656` - `network_menu = NetworkSettingsMenu(self)`
- `ui/network_settings_menu.py:15-16` - `def __init__(self):`

**Fix Required**:
```python
# In NetworkSettingsMenu
def __init__(self, config_manager: ConfigManager = None):
    self.config_manager = config_manager or ConfigManager()
```

**Impact**: LOW - Works but creates duplicate ConfigManager instances

---

## Summary

### Must Fix (Breaking Issues)
1. ✅ **Proxy rotation not applied to actual downloads** - Critical functionality broken
2. ✅ **download_timeout_seconds reference** - Timeout not working
3. ✅ **configure_download_timeout method name** - Menu option crashes
4. ✅ **PlaylistDownloader constructor logic** - Potential AttributeErrors

### Should Fix (Quality Issues)
5. Duplicate quality menu options - Confusing UX
6. Proxy test URL - Should use YouTube
7. NetworkSettingsMenu constructor parameter - Memory inefficiency

### Testing Checklist
- [ ] Test proxy rotation with actual proxies and verify different proxies are used
- [ ] Test download timeout with long video
- [ ] Test all Download Settings menu options
- [ ] Test all Network Settings menu options  
- [ ] Test all Notification Settings menu options
- [ ] Verify no AttributeErrors during initialization

## Recommended Fix Order

1. **Fix PlaylistDownloader constructor** (prevents AttributeErrors)
2. **Fix proxy rotation logic** (core feature)
3. **Fix download_timeout reference** (important for long videos)
4. **Fix method name in download settings menu** (prevents crash)
5. **Optional: Fix NetworkSettingsMenu constructor** (better architecture)
6. **Optional: Improve proxy testing URL** (better accuracy)
