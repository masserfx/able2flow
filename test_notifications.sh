#!/bin/bash

# Test script for ANT HILL Notifications System
# Usage: ./test_notifications.sh [count]

API_URL="http://localhost:8000/api"
COUNT=${1:-5}

echo "🧪 Testing ANT HILL Notification System"
echo "========================================"
echo ""
echo "Creating $COUNT sample notifications..."
echo ""

for i in $(seq 1 $COUNT); do
  echo "[$i/$COUNT] Creating notification..."

  response=$(curl -s -X POST "$API_URL/notifications/test/create-sample" \
    -H "Content-Type: application/json")

  if [ $? -eq 0 ]; then
    echo "✅ Success: $response"
  else
    echo "❌ Failed to create notification"
  fi

  # Wait 2 seconds between notifications (simulating real-time flow)
  if [ $i -lt $COUNT ]; then
    echo "   Waiting 2 seconds..."
    sleep 2
  fi

  echo ""
done

echo "========================================"
echo "✅ Test completed!"
echo ""
echo "📊 You should now see:"
echo "  - $COUNT notifications in the notification bell"
echo "  - Toast popups appearing (if frontend is running)"
echo "  - Sound effects playing"
echo "  - Unread badge showing count"
echo ""
echo "🔍 Check the frontend at: http://localhost:5173"
echo "🔔 Click the notification bell icon to see all notifications"
