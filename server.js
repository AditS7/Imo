import express from 'express';
const app = express();
const port = 3000;

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
          .status { display: inline-block; padding: 0.25rem 0.75rem; background: #f9e2af; color: #11111b; border-radius: 999px; font-weight: bold; margin-top: 1rem; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🤖 Discord Bot is Paused in Preview</h1>
          <p>The bot is configured to only run on Railway.</p>
          <div class="status">⏸️ Dev Preview Running</div>
        </div>
      </body>
    </html>
  `);
});

app.listen(port, () => {
  console.log(`[Node] Web UI started on port ${port} (Bot execution skipped in AI Studio).`);
});
