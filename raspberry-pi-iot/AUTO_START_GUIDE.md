# GuardIt Auto-Start Setup Guide

This guide explains how to automatically start the GuardIt IMU WiFi server when your Raspberry Pi boots up.

## 🚀 Quick Setup

The auto-start service is already installed and enabled! Your GuardIt server will automatically start when the Pi boots.

### Server Access
- **URL:** `http://10.103.139.13:8080`
- **Static IP:** `10.103.139.13` (permanent)
- **Port:** `8080`

## 📋 Service Management

Use the provided management script to control the service:

```bash
# Check service status
./manage_service.sh status

# Start the service
./manage_service.sh start

# Stop the service  
./manage_service.sh stop

# Restart the service
./manage_service.sh restart

# View recent logs
./manage_service.sh logs

# Follow logs in real-time
./manage_service.sh follow-logs

# Test server connectivity
./manage_service.sh test
```

## 🔧 Manual Service Commands

If you prefer using systemctl directly:

```bash
# Check status
sudo systemctl status guardit.service

# Start service
sudo systemctl start guardit.service

# Stop service
sudo systemctl stop guardit.service

# Restart service
sudo systemctl restart guardit.service

# View logs
sudo journalctl -u guardit.service -f

# Enable auto-start (already done)
sudo systemctl enable guardit.service

# Disable auto-start
sudo systemctl disable guardit.service
```

## 📱 iOS App Connection

Your iOS app can now connect directly to:
- **IP:** `10.103.139.13`
- **Port:** `8080`
- **Full URL:** `http://10.103.139.13:8080`

## 🔄 Boot Process

When you power on your Raspberry Pi:

1. 🔌 Pi boots up
2. 🌐 Network connects
3. 🚀 GuardIt service automatically starts
4. 📱 iOS app can immediately connect
5. 📹 Cameras are auto-initialized and streaming
6. 🎯 IMU monitoring begins

## 💻 Development Workflow

When making code changes via SSH:

1. **Edit your code** (imu_wifi_server.py, etc.)
2. **Restart the service** to load changes:
   ```bash
   ./manage_service.sh restart
   ```
3. **Test your changes** - the service will use your updated code
4. **View logs** if needed:
   ```bash
   ./manage_service.sh logs
   ```

> **Note:** You don't need to reinstall the service - just restart it to pick up code changes!

## 🛠️ Service Configuration

The service is configured with:
- **Auto-restart:** If the server crashes, it automatically restarts
- **Delay restart:** 10 seconds between restart attempts
- **User:** Runs as `guardit` user
- **Working directory:** `/home/guardit/Documents/GuardIt/raspberry-pi-iot`
- **Logging:** All output goes to system journal

## 🔍 Troubleshooting

### Server not responding
```bash
# Check service status
./manage_service.sh status

# View logs for errors
./manage_service.sh logs

# Restart service
./manage_service.sh restart
```

### Check if auto-start is enabled
```bash
sudo systemctl is-enabled guardit.service
# Should return: enabled
```

### Reinstall service
```bash
# Uninstall
./manage_service.sh uninstall

# Reinstall
./manage_service.sh install
```

## 📊 Performance Notes

- **Startup time:** ~10-15 seconds after network is ready
- **Camera auto-start:** CSI camera streaming begins automatically
- **Memory usage:** ~50-100MB depending on camera usage
- **CPU usage:** ~5-15% depending on detection and streaming load

## 🔐 Security

The service runs with:
- Limited privileges (`NoNewPrivileges=true`)
- Private temporary directory (`PrivateTmp=true`)
- Runs as non-root user (`guardit`)

## 📝 Log Locations

- **System journal:** `sudo journalctl -u guardit.service`
- **Service file:** `/etc/systemd/system/guardit.service`
- **Management script:** `./manage_service.sh`

Your GuardIt system is now fully automated and ready for production use! 🎉
