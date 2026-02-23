# Sleep Checker v1 - Sleep Blocker

A face recognition-based system daemon that monitors user presence before system sleep events. When the system attempts to sleep, this daemon analyzes webcam input to make intelligent decisions about whether to allow sleep, prevent sleep, or shutdown the system.

## How It Works

| Detection Result | Action |
|------------------|--------|
| Owner detected | Block sleep (user is present) |
| Unknown person detected | Shutdown system (security measure) |
| No face detected | Allow sleep (user is away) |

## Files

| File | Description |
|------|-------------|
| `phase1_face_detect.py` | Basic face detection testing with webcam |
| `phase2_face_training.py` | Capture face images and generate encodings |
| `phase3_face_recognition.py` | Real-time face recognition testing |
| `phase4_system_controller.py` | System integration testing |
| `phase5_service_daemon.py` | **Main daemon script** for systemd |
| `service/sleep-checker.service` | Systemd service template |

## Installation

### 1. Generate face encodings

```bash
cd /path/to/sleep_checker
source venv/bin/activate
python v1_sleep_blocker/phase2_face_training.py
```

### 2. Copy the daemon script

```bash
sudo cp v1_sleep_blocker/phase5_service_daemon.py /usr/local/bin/sleep_checker.py
sudo chmod +x /usr/local/bin/sleep_checker.py
```

### 3. Install the systemd service

```bash
# Create systemd service
# NOTE: Use RequiredBy (not WantedBy) so that service failure blocks sleep
sudo tee /etc/systemd/system/sleep-checker.service << 'EOF'
[Unit]
Description=Sleep Checker - Face Recognition Guard
Before=sleep.target suspend.target hibernate.target

[Service]
Type=oneshot
ExecStart=/path/to/your/venv/bin/python /usr/local/bin/sleep_checker.py pre
TimeoutSec=30

[Install]
RequiredBy=sleep.target suspend.target hibernate.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable sleep-checker.service
```

## Usage

### Check service status
```bash
systemctl status sleep-checker.service
```

### View logs
```bash
journalctl -u sleep-checker.service
```

### Temporarily disable
```bash
sudo systemctl disable sleep-checker.service
```

### Re-enable
```bash
sudo systemctl enable sleep-checker.service
```

### Force sleep (bypass all checks)
```bash
sudo systemctl suspend --force
```

## Testing

```bash
# Test face recognition without system actions
source venv/bin/activate
python v1_sleep_blocker/phase5_service_daemon.py --test

# Test with actual exit codes (but no system sleep)
python v1_sleep_blocker/phase5_service_daemon.py pre
echo $?  # 1 = blocking sleep, 0 = allowing sleep
```

## Important Notes

### Why RequiredBy instead of WantedBy?

- `WantedBy=` creates a **soft dependency** - sleep proceeds even if service fails
- `RequiredBy=` creates a **hard dependency** - sleep is **blocked** if service fails

This is the key difference that makes the sleep blocking actually work!

### Limitations

This version only blocks **system sleep**. It does NOT prevent:
- Screen dimming due to inactivity
- Screen lock due to inactivity

For preventing screen idle, see **v2_idle_monitor** (coming soon).
