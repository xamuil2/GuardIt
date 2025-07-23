#!/bin/bash

# GuardIt Service Management Script
# Usage: ./manage_service.sh [start|stop|restart|status|logs|install|uninstall]

SERVICE_NAME="guardit.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
LOCAL_SERVICE_FILE="./guardit.service"

case "$1" in
    start)
        echo "🚀 Starting GuardIt service..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    stop)
        echo "🛑 Stopping GuardIt service..."
        sudo systemctl stop $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    restart)
        echo "🔄 Restarting GuardIt service..."
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    status)
        echo "📊 GuardIt service status:"
        sudo systemctl status $SERVICE_NAME --no-pager
        echo ""
        echo "🌐 Server should be accessible at: http://10.103.139.13:8080"
        ;;
    logs)
        echo "📋 GuardIt service logs (last 50 lines):"
        sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
        ;;
    follow-logs)
        echo "📋 Following GuardIt service logs (Ctrl+C to stop):"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    install)
        echo "📦 Installing GuardIt service..."
        if [ ! -f "$LOCAL_SERVICE_FILE" ]; then
            echo "❌ Error: $LOCAL_SERVICE_FILE not found"
            exit 1
        fi
        sudo cp $LOCAL_SERVICE_FILE $SERVICE_FILE
        sudo systemctl daemon-reload
        sudo systemctl enable $SERVICE_NAME
        echo "✅ Service installed and enabled for auto-start"
        echo "🚀 Starting service..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    uninstall)
        echo "🗑️ Uninstalling GuardIt service..."
        sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
        sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
        sudo rm -f $SERVICE_FILE
        sudo systemctl daemon-reload
        echo "✅ Service uninstalled"
        ;;
    test)
        echo "🧪 Testing GuardIt server connection..."
        if curl -s http://127.0.0.1:8080/status > /dev/null; then
            echo "✅ Server is responding"
            echo "📊 Status:"
            curl -s http://127.0.0.1:8080/status | python3 -m json.tool 2>/dev/null || curl -s http://127.0.0.1:8080/status
        else
            echo "❌ Server is not responding"
            echo "🔍 Check service status:"
            sudo systemctl status $SERVICE_NAME --no-pager
        fi
        ;;
    *)
        echo "GuardIt Service Manager"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start         Start the GuardIt service"
        echo "  stop          Stop the GuardIt service"
        echo "  restart       Restart the GuardIt service"
        echo "  status        Show service status"
        echo "  logs          Show recent service logs"
        echo "  follow-logs   Follow service logs in real-time"
        echo "  install       Install and enable the service"
        echo "  uninstall     Remove the service"
        echo "  test          Test server connectivity"
        echo ""
        echo "Service URL: http://10.103.139.13:8080"
        ;;
esac
