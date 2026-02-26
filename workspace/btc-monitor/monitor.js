const fs = require('fs');
const https = require('https');
const path = require('path');

// Configuration
const CONFIG = {
  PRICE_THRESHOLD: 71000,
  VOLUME_MULTIPLIER: 1.5,
  FUNDING_RATE_THRESHOLD: 0.0001, // 0.01%
  BREAKOUT_CONFIRMATION_MINUTES: 30,
  CHECK_INTERVAL_MINUTES: 5,
  STATE_FILE: path.join(__dirname, 'state.json'),
  LOG_FILE: path.join(__dirname, 'monitor.log')
};

// Logger
function log(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}`;
  console.log(logMessage);
  fs.appendFileSync(CONFIG.LOG_FILE, logMessage + '\n');
}

// Read/Write state
function readState() {
  try {
    if (fs.existsSync(CONFIG.STATE_FILE)) {
      const data = fs.readFileSync(CONFIG.STATE_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (err) {
    log(`Error reading state: ${err.message}`);
  }
  return {
    isMonitoring: false,
    breakoutStartTime: null,
    lastCheckTime: null,
    alerted: false
  };
}

function writeState(state) {
  try {
    fs.writeFileSync(CONFIG.STATE_FILE, JSON.stringify(state, null, 2));
  } catch (err) {
    log(`Error writing state: ${err.message}`);
  }
}

// HTTP request helper
function httpGet(url) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; BTC-Monitor/1.0)'
      }
    };
    https.get(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error('Invalid JSON response'));
        }
      });
    }).on('error', reject);
  });
}

// Fetch BTC price and volume from Binance spot
async function getBTCSpotData() {
  try {
    const data = await httpGet('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
    return {
      price: parseFloat(data.lastPrice),
      volume: parseFloat(data.volume),
      quoteVolume: parseFloat(data.quoteVolume)
    };
  } catch (err) {
    log(`Error fetching spot data: ${err.message}`);
    return null;
  }
}

// Fetch funding rate from Binance perpetual
async function getFundingRate() {
  try {
    const data = await httpGet('https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT');
    return parseFloat(data.lastFundingRate);
  } catch (err) {
    log(`Error fetching funding rate: ${err.message}`);
    return null;
  }
}

// Calculate 20-day average volume
async function get20DayAvgVolume() {
  try {
    const data = await httpGet('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=20');
    const volumes = data.map(k => parseFloat(k[5])); // Volume is at index 5
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    return avgVolume;
  } catch (err) {
    log(`Error calculating 20-day volume: ${err.message}`);
    return null;
  }
}

// Send alert via message tool
async function sendAlert(data) {
  const { exec } = require('child_process');
  
  const durationMinutes = Math.floor((Date.now() - data.breakoutStartTime) / 60000);
  const volumeMultiplier = (data.volume / data.avgVolume).toFixed(2);
  const fundingRatePercent = (data.fundingRate * 100).toFixed(4);
  
  const message = `🚨 BTC突破$71K追涨提醒

✅ 触发条件已全部满足：
• 现货价格：$${data.price.toLocaleString()}
• 成交量：${data.volume.toFixed(2)} / 20日均量 ${data.avgVolume.toFixed(2)} = ${volumeMultiplier}倍
• 资金费率：${fundingRatePercent}%
• 突破持续：${durationMinutes}分钟

📈 操作建议：
• 标的：BTC Call Options
• 推荐合约：BTC-27MAR26-71K-C 或 BTC-6MAR26-75K-C
• 仓位：本金5-10%
• 止损：跌破$70,000或权利金亏损50%
• 目标：$75K（第一止盈）/ $80K（第二止盈）

⚠️ 风险提示：
- 假突破风险：需成交量配合确认
- IV飙升风险：突破时IV可能跳升，权利金变贵
- 时间衰减：选择3-4周后到期合约平衡Theta`;

  return new Promise((resolve, reject) => {
    const cmd = `openclaw message send --target "whatsapp" --message "${message.replace(/"/g, '\\"').replace(/\n/g, '\\n')}"`;
    exec(cmd, (error, stdout, stderr) => {
      if (error) {
        log(`Failed to send alert: ${error.message}`);
        reject(error);
      } else {
        log('Alert sent successfully');
        resolve(stdout);
      }
    });
  });
}

// Main monitoring logic
async function monitor() {
  log('=== Starting BTC $71K Breakout Monitor ===');
  
  const state = readState();
  log(`Current state: isMonitoring=${state.isMonitoring}, alerted=${state.alerted}`);
  
  // Fetch all required data
  const [spotData, fundingRate, avgVolume] = await Promise.all([
    getBTCSpotData(),
    getFundingRate(),
    get20DayAvgVolume()
  ]);
  
  if (!spotData || fundingRate === null || avgVolume === null) {
    log('Failed to fetch required data, skipping this check');
    return;
  }
  
  const { price, volume } = spotData;
  log(`Price: $${price.toLocaleString()}, Volume: ${volume.toFixed(2)}, Avg20d: ${avgVolume.toFixed(2)}, Funding: ${(fundingRate * 100).toFixed(4)}%`);
  
  // Check individual conditions
  const priceCondition = price > CONFIG.PRICE_THRESHOLD;
  const volumeCondition = volume > (avgVolume * CONFIG.VOLUME_MULTIPLIER);
  const fundingCondition = fundingRate > CONFIG.FUNDING_RATE_THRESHOLD;
  
  log(`Conditions - Price>${CONFIG.PRICE_THRESHOLD}: ${priceCondition}, Volume>${CONFIG.VOLUME_MULTIPLIER}x: ${volumeCondition}, Funding>0.01%: ${fundingCondition}`);
  
  const allConditionsMet = priceCondition && volumeCondition && fundingCondition;
  
  if (allConditionsMet) {
    if (!state.isMonitoring) {
      // First time entering breakout mode
      log('🚀 All conditions met! Entering breakout monitoring mode');
      state.isMonitoring = true;
      state.breakoutStartTime = Date.now();
      state.alerted = false;
    } else {
      // Already in monitoring mode, check if 30 minutes passed
      const elapsedMs = Date.now() - state.breakoutStartTime;
      const elapsedMinutes = Math.floor(elapsedMs / 60000);
      log(`Monitoring breakout... Elapsed: ${elapsedMinutes} minutes`);
      
      if (elapsedMinutes >= CONFIG.BREAKOUT_CONFIRMATION_MINUTES && !state.alerted) {
        log('✅ Breakout confirmed! Sending alert...');
        try {
          await sendAlert({
            price,
            volume,
            avgVolume,
            fundingRate,
            breakoutStartTime: state.breakoutStartTime
          });
          state.alerted = true;
          // Reset after alerting to wait for next opportunity
          state.isMonitoring = false;
          state.breakoutStartTime = null;
        } catch (err) {
          log(`Alert failed: ${err.message}`);
        }
      }
    }
  } else {
    if (state.isMonitoring) {
      log('❌ Conditions no longer met, resetting monitoring state');
      // Reset state if conditions break
      state.isMonitoring = false;
      state.breakoutStartTime = null;
      state.alerted = false;
    }
  }
  
  state.lastCheckTime = Date.now();
  writeState(state);
  log('=== Monitor check complete ===\n');
}

// Run monitor
monitor().catch(err => {
  log(`Fatal error: ${err.message}`);
  process.exit(1);
});
