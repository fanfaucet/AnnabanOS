from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
async def interface() -> str:
    return """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>AnnabanOS Interface</title>
  <style>
    :root { color-scheme: dark; }
    body {
      margin: 0;
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: #0b1020;
      color: #e6edf6;
      display: grid;
      place-items: center;
      min-height: 100vh;
    }
    .app {
      width: min(920px, 92vw);
      background: #131a31;
      border: 1px solid #2a355d;
      border-radius: 14px;
      padding: 1rem;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
    }
    h1 { margin-top: 0; font-size: 1.2rem; }
    .controls {
      display: grid;
      gap: 0.75rem;
      grid-template-columns: 1fr auto;
    }
    textarea {
      grid-column: 1 / -1;
      min-height: 90px;
      border-radius: 10px;
      border: 1px solid #314275;
      background: #0f1630;
      color: #e6edf6;
      padding: 0.75rem;
      resize: vertical;
    }
    button {
      justify-self: end;
      border: none;
      border-radius: 8px;
      padding: 0.6rem 1rem;
      background: #4f7cff;
      color: #fff;
      font-weight: 600;
      cursor: pointer;
    }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    #stream {
      margin-top: 1rem;
      border: 1px solid #2a355d;
      border-radius: 10px;
      background: #0d142b;
      padding: 0.8rem;
      min-height: 240px;
      max-height: 48vh;
      overflow: auto;
      white-space: pre-wrap;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .line { margin: 0 0 0.55rem; }
    .line span { opacity: 0.75; }
  </style>
</head>
<body>
  <main class=\"app\">
    <h1>AnnabanOS Streaming Interface</h1>
    <div class=\"controls\">
      <textarea id=\"prompt\" placeholder=\"Ask your business assistant...\"></textarea>
      <button id=\"run\">Run Stream</button>
    </div>
    <section id=\"stream\" aria-live=\"polite\"></section>
  </main>

<script>
const streamBox = document.getElementById('stream');
const runBtn = document.getElementById('run');
const promptInput = document.getElementById('prompt');

function addLine(text) {
  const p = document.createElement('p');
  p.className = 'line';
  p.textContent = text;
  streamBox.appendChild(p);
  streamBox.scrollTop = streamBox.scrollHeight;
}

async function runStream() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    addLine('Please provide a prompt.');
    return;
  }

  runBtn.disabled = true;
  streamBox.innerHTML = '';
  addLine('Starting stream...');

  try {
    const response = await fetch('/stream/business', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });

    if (!response.ok || !response.body) {
      addLine(`Stream request failed: ${response.status}`);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const event of events) {
        const line = event.split('\n').find((l) => l.startsWith('data: '));
        if (!line) continue;

        try {
          const payload = JSON.parse(line.slice(6));
          if (payload.error) {
            addLine(`Error: ${payload.error}`);
          } else {
            addLine(JSON.stringify(payload));
          }
        } catch {
          addLine(line.slice(6));
        }
      }
    }

    addLine('Stream completed.');
  } catch (error) {
    addLine(`Network error: ${error.message}`);
  } finally {
    runBtn.disabled = false;
  }
}

runBtn.addEventListener('click', runStream);
promptInput.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    runStream();
  }
});
</script>
</body>
</html>
"""
