#!/bin/bash
# Quick diagnostic script to check scheduler status

echo "========================================"
echo "EngageFlow Scheduler Diagnostic"
echo "========================================"
echo ""

echo "[1] Checking pending queue items..."
cd ~/engageflow/backend
sqlite3 engageflow.db "SELECT COUNT(*) as pending_count FROM queue_items WHERE status = 'pending';"
echo ""

echo "[2] Next 3 scheduled actions:"
sqlite3 engageflow.db "SELECT scheduledFor, action, profileName FROM queue_items WHERE status = 'pending' ORDER BY scheduledFor ASC LIMIT 3;"
echo ""

echo "[3] Recent Activity Timeline entries:"
sqlite3 engageflow.db "SELECT timestamp, profile, status, message FROM logs ORDER BY timestamp DESC LIMIT 5;"
echo ""

echo "[4] Checking if scheduler is running (backend logs):"
if [ -f logs/engageflow.log ]; then
    echo "Last 5 scheduler-related log entries:"
    grep -i "queue\|scheduler\|execute" logs/engageflow.log | tail -5
else
    echo "⚠ Log file not found at logs/engageflow.log"
fi
echo ""

echo "[5] Backend process status:"
ps aux | grep "uvicorn\|python.*app" | grep -v grep
echo ""

echo "========================================"
echo "Diagnosis complete!"
echo "========================================"
