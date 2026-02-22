/**
 * PM2 Ecosystem Configuration — LOCAL AGENT (PC / Laptop)
 *
 * Manages Local Agent processes on the user's local machine.
 * Reads .env automatically via scripts/run_local_agent.sh wrapper.
 *
 * Usage:
 *   pm2 start ecosystem.config.local.js    # Start all
 *   pm2 stop ecosystem.config.local.js     # Stop all
 *   pm2 restart ecosystem.config.local.js  # Restart all
 *   pm2 logs local_approval_handler        # View logs
 *   pm2 logs whatsapp_watcher_local        # View WhatsApp logs
 *   pm2 list                               # Status
 */

const path = require('path');

const PROJECT_ROOT = __dirname;

module.exports = {
  apps: [
    // ----------------------------------------------------------------
    // 1. Local Approval Handler
    //    Loads .env → runs local_agent/src/orchestrator.py every 30s
    //    Scans vault/Approved/ → sends emails via SMTP
    // ----------------------------------------------------------------
    {
      name:          'local_approval_handler',
      script:        path.join(PROJECT_ROOT, 'scripts', 'run_local_agent.sh'),
      interpreter:   'bash',
      cwd:           PROJECT_ROOT,
      watch:         false,
      autorestart:   true,
      max_restarts:  10,
      min_uptime:    '5s',
      restart_delay: 5000,
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file:    path.join(PROJECT_ROOT, 'vault', 'Logs', 'Local', 'pm2_error.log'),
      out_file:      path.join(PROJECT_ROOT, 'vault', 'Logs', 'Local', 'pm2_out.log'),
    },

    // ----------------------------------------------------------------
    // 2. WhatsApp Watcher (Local)
    //    Monitors WhatsApp Web via Playwright, generates AI replies
    //    Uses local WhatsApp session (already authenticated)
    // ----------------------------------------------------------------
    {
      name:          'whatsapp_watcher_local',
      script:        path.join(PROJECT_ROOT, 'scripts', 'whatsapp_watcher.py'),
      interpreter:   path.join(PROJECT_ROOT, 'venv', 'Scripts', 'python.exe'),
      cwd:           PROJECT_ROOT,
      watch:         false,
      autorestart:   true,
      max_restarts:  10,
      min_uptime:    '10s',
      restart_delay: 10000,
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {
        PYTHONPATH:              PROJECT_ROOT,
        PYTHONUNBUFFERED:        '1',
        WHATSAPP_SESSION_PATH:   path.join(process.env.USERPROFILE || process.env.HOME || '', '.whatsapp_session_dir'),
        WHATSAPP_POLL_INTERVAL:  '30',
        CHATS_TO_CHECK:          '5',
      },
      error_file:    path.join(PROJECT_ROOT, 'vault', 'Logs', 'Local', 'whatsapp_error.log'),
      out_file:      path.join(PROJECT_ROOT, 'vault', 'Logs', 'Local', 'whatsapp_out.log'),
    },
  ],
};
