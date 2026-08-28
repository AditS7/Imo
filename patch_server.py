with open("server.js", "r") as f:
    text = f.read()

text = text.replace(
    """  // Start the Python bot in the background
  console.log('[Node] Starting Python Discord bot...');
  
  // Use the local pip install path for python
  const bot = spawn('python3', ['-m', 'bot.main'], {
    env: { ...process.env, PATH: `${process.env.HOME}/.local/bin:${process.env.PATH}` }
  });
  
  bot.stdout.on('data', data => process.stdout.write(`[BOT] ${data}`));
  bot.stderr.on('data', data => process.stderr.write(`[BOT ERROR] ${data}`));
  
  bot.on('close', (code) => {
    console.log(`[Node] Bot process exited with code ${code}`);
  });""",
  "  console.log('[Node] Preview running (Discord bot start skipped in AI Studio preview).');"
)

with open("server.js", "w") as f:
    f.write(text)
