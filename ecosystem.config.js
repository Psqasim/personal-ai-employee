/**
 * PM2 Ecosystem Configuration
 * Manages Cloud Agent processes on Oracle VM
 *
 * Usage:
 *   pm2 start ecosystem.config.js       # Start all processes
 *   pm2 list                            # List processes
 *   pm2 logs                            # View logs
 *   pm2 restart all                     # Restart all
 *   pm2 stop all                        # Stop all
 *   pm2 delete all                      # Delete all
 */

module.exports = {
  apps: [
    {
      name: 'cloud_orchestrator',
      script: 'cloud_agent/src/orchestrator.py',
      interpreter: 'python3',
      cwd: '/opt/personal-ai-employee',

      // Environment variables
      env: {
        PYTHONPATH: '/opt/personal-ai-employee',
        ENV_FILE: '.env.cloud',
        PYTHONUNBUFFERED: '1',  // Disable Python output buffering
      },

      // Auto-restart configuration
      autorestart: true,
      max_restarts: 10,           // Max restarts within min_uptime
      min_uptime: 5000,           // 5 seconds minimum uptime
      restart_delay: 1000,        // 1 second delay between restarts

      // Crash detection
      exp_backoff_restart_delay: 100,  // Exponential backoff starting at 100ms

      // Logging
      error_file: '/home/ubuntu/.pm2/logs/cloud_orchestrator-error.log',
      out_file: '/home/ubuntu/.pm2/logs/cloud_orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Resource limits (optional)
      max_memory_restart: '500M',  // Restart if memory exceeds 500MB

      // Execution mode
      exec_mode: 'fork',           // Use fork mode (not cluster)
      instances: 1,                // Single instance

      // Watch for file changes (disable for production)
      watch: false,

      // Cron restart (optional - restart daily at 3 AM)
      // cron_restart: '0 3 * * *',

      // Process ID file
      pid_file: '/home/ubuntu/.pm2/pids/cloud_orchestrator.pid',
    },

    {
      name: 'git_sync_cloud',
      script: 'cloud_agent/src/git_sync.py',
      interpreter: 'python3',
      cwd: '/opt/personal-ai-employee',

      env: {
        PYTHONPATH: '/opt/personal-ai-employee',
        ENV_FILE: '.env.cloud',
        PYTHONUNBUFFERED: '1',
      },

      autorestart: true,
      max_restarts: 10,
      min_uptime: 5000,
      restart_delay: 1000,

      error_file: '/home/ubuntu/.pm2/logs/git_sync_cloud-error.log',
      out_file: '/home/ubuntu/.pm2/logs/git_sync_cloud-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      max_memory_restart: '200M',

      exec_mode: 'fork',
      instances: 1,
      watch: false,

      pid_file: '/home/ubuntu/.pm2/pids/git_sync_cloud.pid',
    },
  ],

  /**
   * Deployment configuration (optional)
   * Use for automated deployment from local to Cloud VM
   */
  deploy: {
    production: {
      user: 'ubuntu',
      host: '129.80.x.x',  // Replace with your Oracle VM IP
      ref: 'origin/003-platinum-tier',
      repo: 'git@github.com:user/personal-ai-employee.git',
      path: '/opt/personal-ai-employee',
      'pre-deploy-local': '',
      'post-deploy': 'source venv/bin/activate && pip install -r requirements.txt && pm2 reload ecosystem.config.js',
      'pre-setup': '',
    },
  },
};
