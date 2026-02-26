#!/bin/bash
cd /Users/oneday/.openclaw/workspace/btc-monitor
/usr/local/bin/node monitor.js >> /Users/oneday/.openclaw/workspace/btc-monitor/cron.log 2>&1
