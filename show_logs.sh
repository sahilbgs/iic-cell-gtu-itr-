#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal & Tunnel - Live Log Viewer
# Usage:
#   ./show_logs.sh         # View all logs live
#   ./show_logs.sh portal  # View portal logs live
#   ./show_logs.sh tunnel  # View tunnel logs live
#   ./show_logs.sh access  # View HTTP traffic/access requests live
#   ./show_logs.sh error   # View portal errors/exceptions live
#   ./show_logs.sh status  # Show service status & recent log summary
# ==============================================================================

PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
touch "$LOG_DIR/portal_access.log" "$LOG_DIR/portal_error.log" "$LOG_DIR/tunnel.log"

MODE="${1:-all}"

case "$MODE" in
  portal)
    echo "======================================================================"
    echo " Streaming GTU-ITR Portal Logs (Access & Errors)..."
    echo " Press Ctrl + C to exit."
    echo "======================================================================"
    tail -f -n 50 "$LOG_DIR/portal_access.log" "$LOG_DIR/portal_error.log"
    ;;

  tunnel)
    echo "======================================================================"
    echo " Streaming Cloudflare Tunnel Logs..."
    echo " Press Ctrl + C to exit."
    echo "======================================================================"
    tail -f -n 50 "$LOG_DIR/tunnel.log"
    ;;

  access)
    echo "======================================================================"
    echo " Streaming Portal HTTP Access Requests..."
    echo " Press Ctrl + C to exit."
    echo "======================================================================"
    tail -f -n 50 "$LOG_DIR/portal_access.log"
    ;;

  error)
    echo "======================================================================"
    echo " Streaming Portal Application Errors..."
    echo " Press Ctrl + C to exit."
    echo "======================================================================"
    tail -f -n 50 "$LOG_DIR/portal_error.log"
    ;;

  status)
    echo "======================================================================"
    echo " GTU-ITR Portal & Tunnel Status Summary"
    echo "======================================================================"
    echo "--> Checking Processes:"
    ps aux | grep -E "(gunicorn|cloudflared)" | grep -v grep || echo "No active processes found."
    echo ""
    echo "--> Port 5000 (Local Portal):"
    if curl -s -I http://127.0.0.1:5000 >/dev/null 2>&1; then
      echo "  [OK] Portal is responding on http://127.0.0.1:5000"
    else
      echo "  [ERROR] Portal is NOT responding on port 5000"
    fi
    echo ""
    echo "--> Live Domain (Cloudflare Tunnel):"
    if curl -s -I https://iic-gtu-itr.aceglory.in >/dev/null 2>&1; then
      echo "  [OK] Domain https://iic-gtu-itr.aceglory.in is reachable (Status: 200 OK)"
    else
      echo "  [ERROR] Domain https://iic-gtu-itr.aceglory.in is not reachable"
    fi
    echo ""
    echo "--> Recent Tunnel Logs (Last 5 lines):"
    tail -n 5 "$LOG_DIR/tunnel.log"
    echo ""
    echo "--> Recent Portal Access Logs (Last 5 lines):"
    tail -n 5 "$LOG_DIR/portal_access.log"
    echo ""
    echo "--> Recent Portal Error Logs (Last 5 lines):"
    tail -n 5 "$LOG_DIR/portal_error.log"
    echo "======================================================================"
    ;;

  all|*)
    echo "======================================================================"
    echo " Streaming Portal & Tunnel Live Logs..."
    echo " Press Ctrl + C to exit."
    echo "======================================================================"
    tail -f -n 30 "$LOG_DIR/portal_access.log" "$LOG_DIR/portal_error.log" "$LOG_DIR/tunnel.log"
    ;;
esac
