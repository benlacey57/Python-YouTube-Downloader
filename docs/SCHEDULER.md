#🤖 Scheduled Operation (cron)

## Automated Cron Script

The `scripts/cron.py` script provides fully automated operation:
- Check monitored channels for new videos
- Download pending queues
- Send notifications about completed activities
- Log all operations

### Installation
```bash
# Install with interactive menu
bash scripts/install_cron.sh

# Test the cron script
bash scripts/install_cron.sh --test
```

**Manual Setup:**
```bash
# Make scripts executable
chmod +x scripts/cron.py
chmod +x scripts/install_cron.sh
```

**Test manually**
```bash
python3 scripts/cron.py
```

**Add to crontab**
```bash
crontab -e
```

Add one of these lines to setup automated running.
```bash
# Every hour - full run
0 * * * * cd /path/to/project && /usr/bin/python3 scripts/cron.py >> logs/cron.log 2>&1

# Every 6 hours - full run
0 */6 * * * cd /path/to/project && /usr/bin/python3 scripts/cron.py >> logs/cron.log 2>&1

# Daily at 2 AM - full run
0 2 * * * cd /path/to/project && /usr/bin/python3 scripts/cron.py >> logs/cron.log 2>&1
```

## Cron Job Options
**Full run (check + download)**
```bash
python3 scripts/cron.py
```

**Check channels only (no downloads)**
```bash
python3 scripts/cron.py --check-only
```

**Download only (no channel checks)**
```bash
python3 scripts/cron.py --download-only
```

**Limit number of queues to process**
```bash
python3 scripts/cron.py --queue-limit 5
```

**Skip summary notification**
```bash
python3 scripts/cron.py --no-notify
```

**Custom log file**
```bash
python3 scripts/cron.py --log-file /path/to/custom.log
```

**Combine options**
```bash
python3 scripts/cron.py --check-only --no-notify
```

.
