import express from 'express';
import { spawn } from 'child_process';

const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>Discord Bot Status</title>
        <style>
          body { font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #1e1e2e; color: #cdd6f4; margin: 0; }
          .container { text-align: center; background: #313244; padding: 2rem 4rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
          h1 { color: #89b4fa; margin-bottom: 0.5rem; }
          p { font-size: 1.1rem; }
          .status { display: inline-block; padding: 0.25rem 0.75rem; background: #a6e3a1; color: #11111b; border-radius: 999px; font-weight: bold; margin-top: 1rem; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🤖 Discord Bot is Active</h1>
          <p>The Python bot process is running in the background.</p>
          <div class="status">● Online</div>
        </div>
      </body>
    </html>
  `);
});

app.listen(port, () => {
  console.log(`[Node] Web UI started on port ${port}`);
  
  // Start the Python bot in the background
  console.log('[Node] Starting Python Discord bot...');
  
  // Use the local pip install path for python
  const bot = spawn('python3', ['-m', 'bot.main'], {
    env: { ...process.env, PATH: `${process.env.HOME}/.local/bin:${process.env.PATH}` }
  });
  
  bot.stdout.on('data', data => process.stdout.write(`[BOT] ${data}`));
  bot.stderr.on('data', data => process.stderr.write(`[BOT ERROR] ${data}`));
  
  bot.on('close', (code) => {
    console.log(`[Node] Bot process exited with code ${code}`);
  });
});
